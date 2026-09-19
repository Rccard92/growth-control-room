from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.seo_optimizer import SeoEntityAnalysis
from app.models.shopify import ShopifyProduct, ShopifyStore
from app.services.content.seo_scoring_engine import score_product
from app.services.content.seo_skill_loader import (
    load_seo_skill_context,
    skill_recommendation_metadata,
)
from app.services.shopify.analytics import compute_best_sellers, product_lookup


@dataclass
class ProductAnalyzeResult:
    products_analyzed: int = 0
    critical: int = 0
    warnings: int = 0
    opportunities: int = 0
    #: Draft/archived products are not analysed; reported so the UI can say why
    #: the analysed count is lower than the catalogue size.
    products_skipped_not_active: int = 0


async def analyze_products_for_store(
    store: ShopifyStore,
    session: AsyncSession,
) -> ProductAnalyzeResult:
    products = (
        (
            await session.execute(
                select(ShopifyProduct).where(ShopifyProduct.shopify_store_id == store.id)
            )
        )
        .scalars()
        .all()
    )

    products_by_gid = product_lookup(list(products))
    best_sellers = await compute_best_sellers(
        session,
        store.id,
        products_by_gid,
        limit=20,
    )
    best_titles = {item.get("product_title") for item in best_sellers}

    load_seo_skill_context()
    skill_meta = skill_recommendation_metadata()

    # One query for every existing analysis instead of one per product: a
    # 5.000-product catalogue used to issue 5.000 round trips here.
    existing_by_entity = {
        row.entity_id: row
        for row in (
            await session.execute(
                select(SeoEntityAnalysis).where(
                    SeoEntityAnalysis.project_id == store.project_id,
                    SeoEntityAnalysis.shopify_store_id == store.id,
                    SeoEntityAnalysis.entity_type == "product",
                )
            )
        ).scalars()
    }

    result = ProductAnalyzeResult()
    now = datetime.now(UTC)

    for product in products:
        if (product.status or "").upper() != "ACTIVE":
            result.products_skipped_not_active += 1
            continue

        desc_text = product.description_text
        if desc_text is None and product.raw_payload:
            desc_text = (product.raw_payload or {}).get("descriptionHtml") or ""
            desc_text = desc_text if isinstance(desc_text, str) else None

        analysis = score_product(
            title=product.title,
            seo_title=product.seo_title,
            seo_description=product.seo_description,
            description_text=desc_text,
            handle=product.handle,
            media_images=product.media_images,
            featured_image_url=product.featured_image_url,
            product_type=product.product_type,
            is_best_seller=product.title in best_titles,
        )

        existing = existing_by_entity.get(product.id)

        recommendations = list(analysis.get("recommendations") or [])
        recommendations.append(skill_meta)

        fields = {
            "entity_gid": product.shopify_gid,
            "entity_title": product.title,
            "last_analyzed_at": now,
            **{k: v for k, v in analysis.items() if k != "recommendations"},
            "recommendations": recommendations,
        }

        if existing is None:
            session.add(
                SeoEntityAnalysis(
                    project_id=store.project_id,
                    shopify_store_id=store.id,
                    entity_type="product",
                    entity_id=product.id,
                    **fields,
                )
            )
        else:
            for key, val in fields.items():
                setattr(existing, key, val)

        result.products_analyzed += 1
        sev = analysis["severity"]
        if sev == "critical":
            result.critical += 1
        elif sev == "warning":
            result.warnings += 1
        elif sev == "opportunity":
            result.opportunities += 1

    await session.commit()
    return result
