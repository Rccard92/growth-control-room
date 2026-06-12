import re
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_seo import ShopifyArticle, ShopifyCollection, ShopifyPage
from app.models.shopify import ShopifyProduct
from app.services.content.seo_constants import (
    ACTIVE_STATUS,
    BEST_SELLER_LIMIT,
    BODY_LONG_ARTICLE,
    BODY_MIN_ARTICLE,
    BODY_MIN_COLLECTION,
    BODY_MIN_PAGE,
    BODY_MIN_PRODUCT,
    SEO_MIN_LENGTH,
    TITLE_MIN_PAGE,
)
from app.services.shopify.analytics import compute_best_sellers, compute_sold_product_gids, product_lookup

IssueDraft = dict[str, Any]

_FAQ_PATTERN = re.compile(r"\b(faq|domande frequenti|frequently asked)\b", re.IGNORECASE)
_PRODUCT_LINK_PATTERN = re.compile(r"/products/", re.IGNORECASE)
_COLLECTION_LINK_PATTERN = re.compile(r"/collections/", re.IGNORECASE)


def _is_active(status: str | None) -> bool:
    return (status or "").upper() == ACTIVE_STATUS


def _text_len(value: str | None) -> int:
    return len((value or "").strip())


def _product_body_text(product: ShopifyProduct) -> str | None:
    payload = product.raw_payload or {}
    for key in ("descriptionHtml", "description", "bodyHtml", "body"):
        raw = payload.get(key)
        if isinstance(raw, str) and raw.strip():
            from app.services.shopify.html_utils import html_to_text

            return html_to_text(raw) or raw.strip()
    return None


def _article_links_product(article: ShopifyArticle, handle: str | None) -> bool:
    blob = " ".join(
        filter(
            None,
            [article.body_html or "", article.body_text or "", handle or ""],
        )
    ).lower()
    if _PRODUCT_LINK_PATTERN.search(blob):
        return True
    if handle and handle.lower() in blob:
        return True
    return False


def _article_links_collection(article: ShopifyArticle, handle: str | None) -> bool:
    blob = " ".join(filter(None, [article.body_html or "", article.body_text or ""])).lower()
    if _COLLECTION_LINK_PATTERN.search(blob):
        return True
    if handle and f"/collections/{handle.lower()}" in blob:
        return True
    if handle and handle.lower() in blob:
        return True
    return False


def _has_faq_section(article: ShopifyArticle) -> bool:
    blob = " ".join(filter(None, [article.body_html or "", article.body_text or ""]))
    return bool(_FAQ_PATTERN.search(blob))


def _issue(
    *,
    entity_type: str,
    entity_id: UUID,
    issue_type: str,
    severity: str,
    title: str,
    description: str,
    recommendation: str,
) -> IssueDraft:
    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "issue_type": issue_type,
        "severity": severity,
        "title": title,
        "description": description,
        "recommendation": recommendation,
    }


async def generate_seo_audit_issues(
    session: AsyncSession,
    store_id: Any,
    products: list[ShopifyProduct],
    collections: list[ShopifyCollection],
    pages: list[ShopifyPage],
    articles: list[ShopifyArticle],
) -> list[IssueDraft]:
    issues: list[IssueDraft] = []
    products_by_gid = product_lookup(products)
    sold_gids = await compute_sold_product_gids(session, store_id)
    best_sellers = await compute_best_sellers(
        session,
        store_id,
        products_by_gid,
        limit=BEST_SELLER_LIMIT,
    )
    best_seller_products: list[ShopifyProduct] = []
    for item in best_sellers:
        for product in products:
            if product.title == item.get("product_title"):
                best_seller_products.append(product)
                break

    for product in products:
        if not _is_active(product.status):
            continue

        title = (product.seo_title or "").strip()
        description = (product.seo_description or "").strip()

        if not title:
            issues.append(
                _issue(
                    entity_type="product",
                    entity_id=product.id,
                    issue_type="missing_meta_title",
                    severity="critical",
                    title=f"Meta title mancante: {product.title}",
                    description=f"Il prodotto '{product.title}' non ha meta title SEO.",
                    recommendation="Aggiungi un meta title descrittivo con brand e prodotto.",
                )
            )
        elif len(title) < SEO_MIN_LENGTH:
            issues.append(
                _issue(
                    entity_type="product",
                    entity_id=product.id,
                    issue_type="short_meta_title",
                    severity="warning",
                    title=f"Meta title troppo corto: {product.title}",
                    description=f"Meta title di '{product.title}' ha {len(title)} caratteri.",
                    recommendation=f"Espandi il meta title ad almeno {SEO_MIN_LENGTH} caratteri.",
                )
            )

        if not description:
            issues.append(
                _issue(
                    entity_type="product",
                    entity_id=product.id,
                    issue_type="missing_meta_description",
                    severity="critical",
                    title=f"Meta description mancante: {product.title}",
                    description=f"Il prodotto '{product.title}' non ha meta description.",
                    recommendation="Aggiungi una meta description orientata al click e al prodotto.",
                )
            )

        body_text = _product_body_text(product)
        if body_text is not None and _text_len(body_text) < BODY_MIN_PRODUCT:
            issues.append(
                _issue(
                    entity_type="product",
                    entity_id=product.id,
                    issue_type="weak_product_body",
                    severity="warning",
                    title=f"Descrizione prodotto debole: {product.title}",
                    description="La description prodotto è assente o troppo breve.",
                    recommendation="Espandi la scheda prodotto con benefici e use case reali.",
                )
            )

        inventory = product.total_inventory or 0
        if product.shopify_gid not in sold_gids and inventory > 0:
            issues.append(
                _issue(
                    entity_type="product",
                    entity_id=product.id,
                    issue_type="active_no_sales_with_stock",
                    severity="opportunity",
                    title=f"Prodotto attivo senza vendite: {product.title}",
                    description=f"'{product.title}' ha stock ({inventory}) ma nessuna vendita sincronizzata.",
                    recommendation="Valuta contenuto informativo o commerciale per sbloccare domanda.",
                )
            )

    for product in best_seller_products:
        linked = any(_article_links_product(article, product.handle) for article in articles)
        if not linked:
            issues.append(
                _issue(
                    entity_type="product",
                    entity_id=product.id,
                    issue_type="bestseller_no_blog_link",
                    severity="opportunity",
                    title=f"Best seller senza articolo collegato: {product.title}",
                    description=f"'{product.title}' è tra i best seller ma nessun articolo lo linka.",
                    recommendation="Crea o aggiorna un articolo con internal link al prodotto.",
                )
            )

    for collection in collections:
        desc_len = _text_len(collection.description_text)
        if desc_len < BODY_MIN_COLLECTION:
            issues.append(
                _issue(
                    entity_type="collection",
                    entity_id=collection.id,
                    issue_type="missing_description",
                    severity="critical" if desc_len == 0 else "warning",
                    title=f"Description collection debole: {collection.title}",
                    description=f"La collection '{collection.title}' ha description insufficiente.",
                    recommendation="Scrivi una description pillar con scope categoria e link interni.",
                )
            )

        if not (collection.seo_title or "").strip():
            issues.append(
                _issue(
                    entity_type="collection",
                    entity_id=collection.id,
                    issue_type="missing_meta_title",
                    severity="warning",
                    title=f"Meta title mancante: {collection.title}",
                    description=f"Collection '{collection.title}' senza seo title.",
                    recommendation="Aggiungi meta title con nome collection e contesto shop.",
                )
            )

        if not (collection.seo_description or "").strip():
            issues.append(
                _issue(
                    entity_type="collection",
                    entity_id=collection.id,
                    issue_type="missing_meta_description",
                    severity="warning",
                    title=f"Meta description mancante: {collection.title}",
                    description=f"Collection '{collection.title}' senza meta description.",
                    recommendation="Aggiungi meta description con value proposition categoria.",
                )
            )

        linked_article = any(
            _article_links_collection(article, collection.handle) for article in articles
        )
        if not linked_article and articles:
            issues.append(
                _issue(
                    entity_type="collection",
                    entity_id=collection.id,
                    issue_type="no_linked_article",
                    severity="opportunity",
                    title=f"Nessun articolo collegato: {collection.title}",
                    description=f"Nessun articolo linka la collection '{collection.title}'.",
                    recommendation="Pubblica o aggiorna una guida con link alla collection.",
                )
            )

    for page in pages:
        page_title = (page.title or "").strip()
        if _text_len(page_title) < TITLE_MIN_PAGE:
            issues.append(
                _issue(
                    entity_type="page",
                    entity_id=page.id,
                    issue_type="weak_title",
                    severity="warning",
                    title=f"Titolo pagina debole: {page.title or page.handle or 'Senza titolo'}",
                    description="Il titolo della pagina è assente o troppo corto.",
                    recommendation="Usa un titolo chiaro e descrittivo per la pagina.",
                )
            )

        if not (page.seo_description or "").strip():
            issues.append(
                _issue(
                    entity_type="page",
                    entity_id=page.id,
                    issue_type="missing_meta_description",
                    severity="warning",
                    title=f"Meta description mancante: {page.title}",
                    description=f"La pagina '{page.title}' non ha meta description.",
                    recommendation="Aggiungi meta description per snippet SERP.",
                )
            )

        if _text_len(page.body_text) < BODY_MIN_PAGE:
            issues.append(
                _issue(
                    entity_type="page",
                    entity_id=page.id,
                    issue_type="short_body",
                    severity="warning",
                    title=f"Contenuto pagina troppo corto: {page.title}",
                    description="Il body della pagina è insufficiente per SEO.",
                    recommendation="Espandi il contenuto con sezioni utili e link interni.",
                )
            )

    for article in articles:
        if not (article.seo_title or "").strip():
            issues.append(
                _issue(
                    entity_type="article",
                    entity_id=article.id,
                    issue_type="missing_meta_title",
                    severity="warning",
                    title=f"Meta title mancante: {article.title}",
                    description=f"L'articolo '{article.title}' non ha meta title.",
                    recommendation="Aggiungi meta title ottimizzato per query target.",
                )
            )

        if not (article.seo_description or "").strip():
            issues.append(
                _issue(
                    entity_type="article",
                    entity_id=article.id,
                    issue_type="missing_meta_description",
                    severity="warning",
                    title=f"Meta description mancante: {article.title}",
                    description=f"L'articolo '{article.title}' non ha meta description.",
                    recommendation="Aggiungi meta description con benefit chiaro.",
                )
            )

        body_len = _text_len(article.body_text)
        if body_len < BODY_MIN_ARTICLE:
            issues.append(
                _issue(
                    entity_type="article",
                    entity_id=article.id,
                    issue_type="short_body",
                    severity="warning",
                    title=f"Articolo troppo corto: {article.title}",
                    description=f"Body articolo con {body_len} caratteri testo.",
                    recommendation="Espandi l'articolo con sezioni H2/H3 e internal linking.",
                )
            )

        if not _PRODUCT_LINK_PATTERN.search(
            (article.body_html or "") + (article.body_text or "")
        ):
            issues.append(
                _issue(
                    entity_type="article",
                    entity_id=article.id,
                    issue_type="no_internal_product_links",
                    severity="opportunity",
                    title=f"Nessun link prodotto: {article.title}",
                    description="L'articolo non contiene link interni a prodotti.",
                    recommendation="Aggiungi link a prodotti rilevanti del catalogo.",
                )
            )

        if not _COLLECTION_LINK_PATTERN.search(
            (article.body_html or "") + (article.body_text or "")
        ):
            issues.append(
                _issue(
                    entity_type="article",
                    entity_id=article.id,
                    issue_type="no_internal_collection_links",
                    severity="opportunity",
                    title=f"Nessun link collection: {article.title}",
                    description="L'articolo non contiene link interni a collections.",
                    recommendation="Linka la collection pillar correlata al topic.",
                )
            )

        if body_len >= BODY_LONG_ARTICLE and not _has_faq_section(article):
            issues.append(
                _issue(
                    entity_type="article",
                    entity_id=article.id,
                    issue_type="missing_faq_section",
                    severity="info",
                    title=f"FAQ consigliata: {article.title}",
                    description="Articolo lungo senza sezione FAQ rilevata.",
                    recommendation="Aggiungi FAQ per intent informativo e rich snippet.",
                )
            )

    return issues
