"""Debug counts for Content SEO module."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_seo import ShopifyCollection
from app.models.seo_optimizer import SeoEntityAnalysis
from app.models.shopify import ShopifyProduct, ShopifyStore
from app.services.shopify.content_sync import get_last_collection_sync_errors


async def build_content_seo_debug(
    store: ShopifyStore,
    session: AsyncSession,
) -> dict:
    products_count = (
        await session.execute(
            select(func.count()).select_from(ShopifyProduct).where(
                ShopifyProduct.shopify_store_id == store.id
            )
        )
    ).scalar_one()

    collections_count = (
        await session.execute(
            select(func.count()).select_from(ShopifyCollection).where(
                ShopifyCollection.shopify_store_id == store.id
            )
        )
    ).scalar_one()

    collection_analyses_count = (
        await session.execute(
            select(func.count()).select_from(SeoEntityAnalysis).where(
                SeoEntityAnalysis.shopify_store_id == store.id,
                SeoEntityAnalysis.entity_type == "collection",
            )
        )
    ).scalar_one()

    return {
        "products_count": int(products_count or 0),
        "collections_count": int(collections_count or 0),
        "collection_analyses_count": int(collection_analyses_count or 0),
        "last_content_sync": store.last_sync_at,
        "last_errors": get_last_collection_sync_errors(store.id),
    }
