import logging
import time
from dataclasses import dataclass
from datetime import datetime
from html.parser import HTMLParser
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

logger = logging.getLogger(__name__)


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        stripped = data.strip()
        if stripped:
            self._parts.append(stripped)

    def get_text(self) -> str:
        return " ".join(self._parts)


def html_to_text(html: str | None) -> str | None:
    if not html or not html.strip():
        return None
    parser = _TextExtractor()
    try:
        parser.feed(html)
        parser.close()
    except Exception:
        return None
    text = parser.get_text().strip()
    return text or None


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
    row.products_count = node.get("productsCount")
    row.raw_payload = node
    return row


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


async def sync_shopify_content(
    store: ShopifyStore,
    client: ShopifyGraphQLClient,
    session: AsyncSession,
) -> ContentSyncResult:
    started = time.perf_counter()
    result = ContentSyncResult()

    try:
        collection_nodes = await client.fetch_all_collections()
        for node in collection_nodes:
            await _upsert_collection(session, store.id, node)
            result.collections_synced += 1
    except ShopifyAPIError as exc:
        logger.warning(
            "Shopify content sync: collections failed for store %s: %s",
            store.shop_domain,
            exc.message,
        )

    try:
        page_nodes = await client.fetch_all_pages()
        for node in page_nodes:
            await _upsert_page(session, store.id, node)
            result.pages_synced += 1
    except ShopifyAPIError as exc:
        logger.warning(
            "Shopify content sync: pages failed for store %s: %s",
            store.shop_domain,
            exc.message,
        )

    blog_by_gid: dict[str, ShopifyBlog] = {}
    try:
        blog_nodes = await client.fetch_all_blogs()
        for node in blog_nodes:
            blog = await _upsert_blog(session, store.id, node)
            blog_by_gid[blog.shopify_gid] = blog
            result.blogs_synced += 1
        await session.flush()
    except ShopifyAPIError as exc:
        logger.warning(
            "Shopify content sync: blogs failed for store %s: %s",
            store.shop_domain,
            exc.message,
        )

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
        logger.warning(
            "Shopify content sync: articles failed for store %s: %s",
            store.shop_domain,
            exc.message,
        )

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
