"""Analyze a single product or collection for SEO scoring."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_seo import ShopifyCollection
from app.models.seo_optimizer import SeoEntityAnalysis
from app.models.shopify import ShopifyProduct, ShopifyStore
from app.services.content.seo_scoring_engine import score_collection, score_product
from app.services.content.seo_skill_loader import (
    load_seo_skill_context,
    skill_recommendation_metadata,
)
from app.services.shopify.analytics import compute_best_sellers, product_lookup


async def analyze_single_product(
    store: ShopifyStore,
    session: AsyncSession,
    product_id: UUID,
) -> SeoEntityAnalysis | None:
    product = (
        await session.execute(
            select(ShopifyProduct).where(
                ShopifyProduct.id == product_id,
                ShopifyProduct.shopify_store_id == store.id,
            )
        )
    ).scalar_one_or_none()
    if product is None:
        return None

    products_by_gid = product_lookup([product])
    best_sellers = await compute_best_sellers(
        session, store.id, products_by_gid, limit=20
    )
    best_titles = {item.get("product_title") for item in best_sellers}

    load_seo_skill_context()
    skill_meta = skill_recommendation_metadata()
    now = datetime.now(UTC)

    desc_text = product.description_text
    if desc_text is None and product.raw_payload:
        raw_desc = (product.raw_payload or {}).get("descriptionHtml") or ""
        desc_text = raw_desc if isinstance(raw_desc, str) else None

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

    existing = (
        await session.execute(
            select(SeoEntityAnalysis).where(
                SeoEntityAnalysis.project_id == store.project_id,
                SeoEntityAnalysis.shopify_store_id == store.id,
                SeoEntityAnalysis.entity_type == "product",
                SeoEntityAnalysis.entity_id == product.id,
            )
        )
    ).scalar_one_or_none()

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
        existing = SeoEntityAnalysis(
            project_id=store.project_id,
            shopify_store_id=store.id,
            entity_type="product",
            entity_id=product.id,
            **fields,
        )
        session.add(existing)
    else:
        for key, val in fields.items():
            setattr(existing, key, val)

    await session.flush()
    return existing


async def analyze_single_collection(
    store: ShopifyStore,
    session: AsyncSession,
    collection_id: UUID,
) -> SeoEntityAnalysis | None:
    collection = (
        await session.execute(
            select(ShopifyCollection).where(
                ShopifyCollection.id == collection_id,
                ShopifyCollection.shopify_store_id == store.id,
            )
        )
    ).scalar_one_or_none()
    if collection is None:
        return None

    load_seo_skill_context()
    skill_meta = skill_recommendation_metadata()
    now = datetime.now(UTC)

    analysis = score_collection(
        title=collection.title,
        seo_title=collection.seo_title,
        seo_description=collection.seo_description,
        description_text=collection.description_text,
        handle=collection.handle,
        image_url=collection.image_url,
        image_alt=collection.image_alt,
        products_count=collection.products_count,
    )

    existing = (
        await session.execute(
            select(SeoEntityAnalysis).where(
                SeoEntityAnalysis.project_id == store.project_id,
                SeoEntityAnalysis.shopify_store_id == store.id,
                SeoEntityAnalysis.entity_type == "collection",
                SeoEntityAnalysis.entity_id == collection.id,
            )
        )
    ).scalar_one_or_none()

    recommendations = list(analysis.get("recommendations") or [])
    recommendations.append(skill_meta)

    fields = {
        "entity_gid": collection.shopify_gid,
        "entity_title": collection.title,
        "last_analyzed_at": now,
        **{k: v for k, v in analysis.items() if k != "recommendations"},
        "recommendations": recommendations,
    }

    if existing is None:
        existing = SeoEntityAnalysis(
            project_id=store.project_id,
            shopify_store_id=store.id,
            entity_type="collection",
            entity_id=collection.id,
            **fields,
        )
        session.add(existing)
    else:
        for key, val in fields.items():
            setattr(existing, key, val)

    await session.flush()
    return existing
