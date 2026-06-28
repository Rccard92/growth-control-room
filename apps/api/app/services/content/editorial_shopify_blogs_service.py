"""List Shopify blogs for editorial publishing with lazy sync."""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_seo import ShopifyBlog
from app.schemas.content_seo_editorial import ShopifyBlogListItem, ShopifyBlogsListResponse
from app.services.shopify.client import ShopifyAPIError
from app.services.shopify.connect import get_shopify_client_for_store, get_shopify_store_for_project
from app.services.shopify.content_sync import sync_shopify_blogs_only

logger = logging.getLogger(__name__)


def _blog_to_item(row: ShopifyBlog) -> ShopifyBlogListItem:
    numeric = row.shopify_gid.rsplit("/", 1)[-1] if row.shopify_gid else ""
    return ShopifyBlogListItem(
        id=row.id,
        shopify_blog_id=numeric or row.shopify_gid,
        gid=row.shopify_gid,
        title=row.title,
        handle=row.handle,
    )


async def list_shopify_blogs_for_project(
    session: AsyncSession,
    project_id: UUID,
) -> ShopifyBlogsListResponse:
    store = await get_shopify_store_for_project(project_id, session)
    if store is None or store.connection_status != "connected":
        return ShopifyBlogsListResponse(blogs=[], sync_required=True)

    rows = list(
        (
            await session.execute(
                select(ShopifyBlog)
                .where(ShopifyBlog.shopify_store_id == store.id)
                .order_by(ShopifyBlog.title.asc())
            )
        )
        .scalars()
        .all()
    )

    if rows:
        return ShopifyBlogsListResponse(
            blogs=[_blog_to_item(row) for row in rows],
            sync_required=False,
        )

    try:
        client = await get_shopify_client_for_store(store)
        synced = await sync_shopify_blogs_only(store, client, session)
        if synced > 0:
            rows = list(
                (
                    await session.execute(
                        select(ShopifyBlog)
                        .where(ShopifyBlog.shopify_store_id == store.id)
                        .order_by(ShopifyBlog.title.asc())
                    )
                )
                .scalars()
                .all()
            )
            return ShopifyBlogsListResponse(
                blogs=[_blog_to_item(row) for row in rows],
                sync_required=False,
            )
    except ShopifyAPIError as exc:
        logger.warning(
            "Shopify blogs lazy sync failed for project %s: %s",
            project_id,
            exc.message,
        )

    return ShopifyBlogsListResponse(blogs=[], sync_required=True)
