import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_seo import (
    ShopifyArticle,
    ShopifyBlog,
    ShopifyCollection,
    ShopifyPage,
)
from app.models.shopify import ShopifyStore
from app.services.shopify.client import ShopifyAPIError, ShopifyGraphQLClient
from app.services.shopify.html_utils import html_to_text

logger = logging.getLogger(__name__)

# Ultimi errori sync collections per store (debug/supporto, non sensibile)
_last_collection_sync_errors: dict[str, list[str]] = {}


def parse_products_count(node: dict[str, Any]) -> int | None:
    raw = node.get("productsCount")
    if isinstance(raw, dict):
        count = raw.get("count")
        return int(count) if count is not None else None
    if raw is None:
        return None
    return int(raw)


def get_last_collection_sync_errors(store_id: UUID) -> list[str]:
    return list(_last_collection_sync_errors.get(str(store_id), []))


def _record_collection_sync_errors(store_id: UUID, errors: list[str]) -> None:
    _last_collection_sync_errors[str(store_id)] = errors


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


@dataclass
class ContentSyncResult:
    collections_synced: int = 0
    pages_synced: int = 0
    blogs_synced: int = 0
    articles_synced: int = 0
    duration_seconds: float = 0.0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


async def _upsert_collection(
    session: AsyncSession,
    store_id: UUID,
    node: dict[str, Any],
) -> ShopifyCollection:
    gid = node["id"]
    result = await session.execute(
        select(ShopifyCollection).where(
            ShopifyCollection.shopify_store_id == store_id,
            ShopifyCollection.shopify_gid == gid,
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        row = ShopifyCollection(shopify_store_id=store_id, shopify_gid=gid)
        session.add(row)

    seo = node.get("seo") or {}
    image = node.get("image") or {}
    description_html = node.get("descriptionHtml") or node.get("description")

    row.title = node.get("title") or ""
    row.handle = node.get("handle")
    row.description_html = description_html
    row.description_text = html_to_text(description_html)
    row.seo_title = seo.get("title")
    row.seo_description = seo.get("description")
    row.image_url = image.get("url")
    row.image_alt = image.get("altText")
    row.products_count = parse_products_count(node)
    row.raw_payload = node
    return row


async def _sync_collection_nodes(
    session: AsyncSession,
    store: ShopifyStore,
    client: ShopifyGraphQLClient,
    result: ContentSyncResult,
) -> None:
    try:
        collection_nodes = await client.fetch_all_collections()
        for node in collection_nodes:
            await _upsert_collection(session, store.id, node)
            result.collections_synced += 1
        _record_collection_sync_errors(store.id, [])
    except ShopifyAPIError as exc:
        msg = f"Collections sync failed: {exc.message}"
        logger.warning(
            "Shopify collections sync failed for store %s: %s",
            store.shop_domain,
            exc.message,
        )
        result.errors.append(msg)
        result.warnings.append(msg)
        _record_collection_sync_errors(store.id, [msg])


async def _upsert_page(
    session: AsyncSession,
    store_id: UUID,
    node: dict[str, Any],
) -> ShopifyPage:
    gid = node["id"]
    result = await session.execute(
        select(ShopifyPage).where(
            ShopifyPage.shopify_store_id == store_id,
            ShopifyPage.shopify_gid == gid,
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        row = ShopifyPage(shopify_store_id=store_id, shopify_gid=gid)
        session.add(row)

    seo = node.get("seo") or {}
    body_html = node.get("body")

    row.title = node.get("title") or ""
    row.handle = node.get("handle")
    row.body_html = body_html
    row.body_text = html_to_text(body_html)
    row.seo_title = seo.get("title")
    row.seo_description = seo.get("description")
    row.published_at_shopify = _parse_datetime(node.get("publishedAt"))
    row.raw_payload = node
    return row


async def _upsert_blog(
    session: AsyncSession,
    store_id: UUID,
    node: dict[str, Any],
) -> ShopifyBlog:
    gid = node["id"]
    result = await session.execute(
        select(ShopifyBlog).where(
            ShopifyBlog.shopify_store_id == store_id,
            ShopifyBlog.shopify_gid == gid,
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        row = ShopifyBlog(shopify_store_id=store_id, shopify_gid=gid)
        session.add(row)

    row.title = node.get("title") or ""
    row.handle = node.get("handle")
    row.raw_payload = node
    return row


async def _upsert_article(
    session: AsyncSession,
    store_id: UUID,
    node: dict[str, Any],
    blog_by_gid: dict[str, ShopifyBlog],
) -> ShopifyArticle:
    gid = node["id"]
    result = await session.execute(
        select(ShopifyArticle).where(
            ShopifyArticle.shopify_store_id == store_id,
            ShopifyArticle.shopify_gid == gid,
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        row = ShopifyArticle(shopify_store_id=store_id, shopify_gid=gid)
        session.add(row)

    seo = node.get("seo") or {}
    author = node.get("author") or {}
    body_html = node.get("body")
    blog_meta = node.get("_blog") or {}
    blog_gid = blog_meta.get("id")
    if blog_gid and blog_gid in blog_by_gid:
        row.blog_id = blog_by_gid[blog_gid].id

    tags = node.get("tags")
    if isinstance(tags, list):
        row.tags = tags
    else:
        row.tags = None

    row.title = node.get("title") or ""
    row.handle = node.get("handle")
    row.body_html = body_html
    row.body_text = html_to_text(body_html)
    row.summary_html = node.get("summary")
    row.seo_title = seo.get("title")
    row.seo_description = seo.get("description")
    row.author = author.get("name")
    row.published_at_shopify = _parse_datetime(node.get("publishedAt"))
    row.raw_payload = node
    return row


async def sync_shopify_collections_only(
    store: ShopifyStore,
    client: ShopifyGraphQLClient,
    session: AsyncSession,
) -> ContentSyncResult:
    """Sync only collections for Product & Collection SEO Optimizer v1."""
    started = time.perf_counter()
    result = ContentSyncResult()
    await _sync_collection_nodes(session, store, client, result)
    await session.commit()
    result.duration_seconds = round(time.perf_counter() - started, 2)
    return result


async def sync_shopify_content(
    store: ShopifyStore,
    client: ShopifyGraphQLClient,
    session: AsyncSession,
) -> ContentSyncResult:
    started = time.perf_counter()
    result = ContentSyncResult()

    await _sync_collection_nodes(session, store, client, result)

    try:
        page_nodes = await client.fetch_all_pages()
        for node in page_nodes:
            await _upsert_page(session, store.id, node)
            result.pages_synced += 1
    except ShopifyAPIError as exc:
        msg = f"Pages sync failed: {exc.message}"
        logger.warning(
            "Shopify content sync: pages failed for store %s: %s",
            store.shop_domain,
            exc.message,
        )
        result.warnings.append(msg)

    blog_by_gid: dict[str, ShopifyBlog] = {}
    try:
        blog_nodes = await client.fetch_all_blogs()
        for node in blog_nodes:
            blog = await _upsert_blog(session, store.id, node)
            blog_by_gid[blog.shopify_gid] = blog
            result.blogs_synced += 1
        await session.flush()
    except ShopifyAPIError as exc:
        msg = f"Blogs sync failed: {exc.message}"
        logger.warning(
            "Shopify content sync: blogs failed for store %s: %s",
            store.shop_domain,
            exc.message,
        )
        result.warnings.append(msg)

    if not blog_by_gid:
        existing = await session.execute(
            select(ShopifyBlog).where(ShopifyBlog.shopify_store_id == store.id)
        )
        for blog in existing.scalars().all():
            blog_by_gid[blog.shopify_gid] = blog

    try:
        article_nodes = await client.fetch_all_articles()
        for node in article_nodes:
            await _upsert_article(session, store.id, node, blog_by_gid)
            result.articles_synced += 1
    except ShopifyAPIError as exc:
        msg = f"Articles sync failed: {exc.message}"
        logger.warning(
            "Shopify content sync: articles failed for store %s: %s",
            store.shop_domain,
            exc.message,
        )
        result.warnings.append(msg)

    await session.commit()
    result.duration_seconds = round(time.perf_counter() - started, 2)
    logger.info(
        "Shopify content sync completed for %s: collections=%s pages=%s blogs=%s articles=%s (%.2fs)",
        store.shop_domain,
        result.collections_synced,
        result.pages_synced,
        result.blogs_synced,
        result.articles_synced,
        result.duration_seconds,
    )
    return result
