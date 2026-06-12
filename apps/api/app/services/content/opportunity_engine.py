from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_seo import ShopifyArticle, ShopifyCollection
from app.models.shopify import ShopifyProduct
from app.services.content.seo_audit import (
    _article_links_collection,
    _article_links_product,
    _is_active,
    _product_body_text,
    _text_len,
)
from app.services.content.seo_constants import (
    BEST_SELLER_LIMIT,
    BODY_MIN_COLLECTION,
    SEO_MIN_LENGTH,
)
from app.services.shopify.analytics import compute_best_sellers, compute_sold_product_gids, product_lookup

OpportunityDraft = dict[str, Any]


def _entity_ref(entity_type: str, entity: Any) -> dict[str, Any]:
    return {
        "id": str(entity.id),
        "handle": getattr(entity, "handle", None),
        "title": getattr(entity, "title", None),
        "entity_type": entity_type,
    }


def _keyword_from_entity(entity: Any) -> str | None:
    handle = (getattr(entity, "handle", None) or "").strip()
    title = (getattr(entity, "title", None) or "").strip()
    if handle:
        return handle.replace("-", " ")
    if title:
        return title.lower()
    return None


def _opportunity(
    *,
    opportunity_type: str,
    priority: str,
    title: str,
    description: str,
    reason: str,
    target_entity_type: str | None = None,
    target_entity_id: UUID | None = None,
    suggested_keyword: str | None = None,
    search_intent: str | None = None,
    suggested_products: list[dict[str, Any]] | None = None,
    suggested_collections: list[dict[str, Any]] | None = None,
) -> OpportunityDraft:
    return {
        "opportunity_type": opportunity_type,
        "priority": priority,
        "title": title,
        "description": description,
        "target_entity_type": target_entity_type,
        "target_entity_id": target_entity_id,
        "suggested_keyword": suggested_keyword,
        "search_intent": search_intent,
        "suggested_products": suggested_products,
        "suggested_collections": suggested_collections,
        "reason": reason,
    }


async def generate_content_opportunities(
    session: AsyncSession,
    store_id: Any,
    products: list[ShopifyProduct],
    collections: list[ShopifyCollection],
    articles: list[ShopifyArticle],
    issues: list[dict[str, Any]],
) -> list[OpportunityDraft]:
    opportunities: list[OpportunityDraft] = []
    products_by_gid = product_lookup(products)
    sold_gids = await compute_sold_product_gids(session, store_id)
    best_sellers = await compute_best_sellers(
        session,
        store_id,
        products_by_gid,
        limit=BEST_SELLER_LIMIT,
    )

    issue_by_entity: dict[tuple[str, UUID, str], dict[str, Any]] = {}
    for issue in issues:
        key = (issue["entity_type"], issue["entity_id"], issue["issue_type"])
        issue_by_entity[key] = issue

    best_seller_titles = {item.get("product_title") for item in best_sellers}
    for product in products:
        if not _is_active(product.status):
            continue

        is_best = product.title in best_seller_titles
        inventory = product.total_inventory or 0
        no_sales = product.shopify_gid not in sold_gids

        if is_best and not any(_article_links_product(a, product.handle) for a in articles):
            opportunities.append(
                _opportunity(
                    opportunity_type="blog_topic",
                    priority="high",
                    title=f"Articolo per best seller: {product.title}",
                    description=f"Crea contenuto editoriale che linka '{product.title}'.",
                    target_entity_type="product",
                    target_entity_id=product.id,
                    suggested_keyword=_keyword_from_entity(product),
                    search_intent="commercial",
                    suggested_products=[_entity_ref("product", product)],
                    reason="Prodotto tra i best seller senza copertura blog.",
                )
            )

        if no_sales and inventory > 0:
            opportunities.append(
                _opportunity(
                    opportunity_type="blog_topic",
                    priority="medium",
                    title=f"Guida prodotto fermo: {product.title}",
                    description=f"Stock disponibile ({inventory}) ma nessuna vendita sincronizzata.",
                    target_entity_type="product",
                    target_entity_id=product.id,
                    suggested_keyword=_keyword_from_entity(product),
                    search_intent="informational",
                    suggested_products=[_entity_ref("product", product)],
                    reason="Prodotto attivo con stock e zero vendite — potenziale contenuto informativo.",
                )
            )

        seo_weak = not (product.seo_title or "").strip() or not (product.seo_description or "").strip()
        body = _product_body_text(product)
        body_weak = body is not None and _text_len(body) < SEO_MIN_LENGTH * 3
        if seo_weak or body_weak:
            opportunities.append(
                _opportunity(
                    opportunity_type="product_improvement",
                    priority="high" if is_best else "medium",
                    title=f"Migliora scheda prodotto: {product.title}",
                    description="Meta SEO o description prodotto da rafforzare.",
                    target_entity_type="product",
                    target_entity_id=product.id,
                    suggested_keyword=_keyword_from_entity(product),
                    search_intent="commercial",
                    suggested_products=[_entity_ref("product", product)],
                    reason="Issue SEO prodotto rilevate in audit.",
                )
            )

    for collection in collections:
        desc_weak = _text_len(collection.description_text) < BODY_MIN_COLLECTION
        meta_weak = not (collection.seo_title or "").strip() or not (
            collection.seo_description or ""
        ).strip()
        if desc_weak or meta_weak:
            opportunities.append(
                _opportunity(
                    opportunity_type="collection_improvement",
                    priority="medium",
                    title=f"Migliora SEO collection: {collection.title}",
                    description="Description o meta collection insufficienti.",
                    target_entity_type="collection",
                    target_entity_id=collection.id,
                    suggested_keyword=_keyword_from_entity(collection),
                    search_intent="informational",
                    suggested_collections=[_entity_ref("collection", collection)],
                    reason="Collection debole in audit SEO.",
                )
            )

        if (collection.products_count or 0) >= 3 and not any(
            _article_links_collection(a, collection.handle) for a in articles
        ):
            opportunities.append(
                _opportunity(
                    opportunity_type="blog_topic",
                    priority="medium",
                    title=f"Guida categoria: {collection.title}",
                    description="Articolo pillar per collection con catalogo significativo.",
                    target_entity_type="collection",
                    target_entity_id=collection.id,
                    suggested_keyword=_keyword_from_entity(collection),
                    search_intent="informational",
                    suggested_collections=[_entity_ref("collection", collection)],
                    reason="Collection senza contenuto editoriale collegato.",
                )
            )

    for article in articles:
        body_blob = (article.body_html or "") + (article.body_text or "")
        missing_products = "/products/" not in body_blob.lower()
        missing_collections = "/collections/" not in body_blob.lower()
        if missing_products or missing_collections:
            related_products = [
                _entity_ref("product", p)
                for p in products[:3]
                if _is_active(p.status)
            ]
            related_collections = [
                _entity_ref("collection", c) for c in collections[:2]
            ]
            opportunities.append(
                _opportunity(
                    opportunity_type="internal_linking",
                    priority="medium",
                    title=f"Internal linking: {article.title}",
                    description="Aggiungi link interni a prodotti e/o collections rilevanti.",
                    target_entity_type="article",
                    target_entity_id=article.id,
                    suggested_keyword=_keyword_from_entity(article),
                    search_intent="informational",
                    suggested_products=related_products or None,
                    suggested_collections=related_collections or None,
                    reason="Articolo senza link interni sufficienti.",
                )
            )

        faq_issue = issue_by_entity.get(("article", article.id, "missing_faq_section"))
        if faq_issue:
            opportunities.append(
                _opportunity(
                    opportunity_type="faq",
                    priority="medium",
                    title=f"FAQ per articolo: {article.title}",
                    description="Aggiungi sezione FAQ per intent informativo.",
                    target_entity_type="article",
                    target_entity_id=article.id,
                    suggested_keyword=_keyword_from_entity(article),
                    search_intent="informational",
                    reason=faq_issue["description"],
                )
            )

    type_groups: dict[str, list[ShopifyProduct]] = {}
    for product in products:
        if not _is_active(product.status):
            continue
        key = (product.product_type or "other").strip().lower()
        type_groups.setdefault(key, []).append(product)

    for group in type_groups.values():
        if len(group) >= 2:
            sample = group[0]
            opportunities.append(
                _opportunity(
                    opportunity_type="comparison",
                    priority="low",
                    title=f"Confronto {sample.product_type or 'prodotti simili'}",
                    description="Articolo comparativo tra prodotti reali dello stesso tipo.",
                    target_entity_type="product",
                    target_entity_id=sample.id,
                    suggested_keyword=_keyword_from_entity(sample),
                    search_intent="commercial",
                    suggested_products=[_entity_ref("product", p) for p in group[:4]],
                    reason=f"{len(group)} prodotti con product_type '{sample.product_type}'.",
                )
            )

    return opportunities
