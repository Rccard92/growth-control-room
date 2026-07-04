"""Shopify synced entity URL discovery for Growth Audit."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.content_seo import ShopifyArticle, ShopifyBlog, ShopifyCollection, ShopifyPage
from app.models.shopify import ShopifyProduct
from app.services.growth_audit.url_utils import normalize_root_url
from app.services.shopify.connect import get_shopify_store_for_project

logger = logging.getLogger(__name__)


def _build_url(root_url: str, path: str) -> str | None:
    if not path:
        return None
    normalized = normalize_root_url(root_url)
    base = normalized.rstrip("/")
    if not path.startswith("/"):
        path = f"/{path}"
    return f"{base}{path}"


def _shopify_event(event_type: str, message: str, count: int = 0) -> dict[str, Any]:
    return {"type": event_type, "message": message, "count": count}


async def discover_shopify_urls(
    session: AsyncSession,
    project_id: UUID,
    root_url: str,
    max_urls: int = 200,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    events: list[dict[str, Any]] = []
    items: list[dict[str, Any]] = []

    store = await get_shopify_store_for_project(project_id, session)
    if store is None:
        events.append(
            _shopify_event(
                "shopify_urls_missing",
                "Nessuno store Shopify collegato al progetto.",
            )
        )
        return items, events

    remaining = max(0, max_urls)

    if remaining > 0:
        products = list(
            (
                await session.execute(
                    select(ShopifyProduct)
                    .where(ShopifyProduct.shopify_store_id == store.id)
                    .where(ShopifyProduct.handle.is_not(None))
                    .order_by(ShopifyProduct.updated_at.desc())
                    .limit(remaining)
                )
            ).scalars().all()
        )
        for product in products:
            if not product.handle:
                continue
            url = _build_url(root_url, f"/products/{product.handle}")
            if not url:
                continue
            items.append(
                {
                    "url": url,
                    "source": "shopify_product",
                    "pageType": "product",
                    "title": product.title,
                    "metadata": {
                        "shopifyGid": product.shopify_gid,
                        "handle": product.handle,
                        "entityType": "product",
                    },
                }
            )
        remaining = max(0, max_urls - len(items))

    if remaining > 0:
        collections = list(
            (
                await session.execute(
                    select(ShopifyCollection)
                    .where(ShopifyCollection.shopify_store_id == store.id)
                    .where(ShopifyCollection.handle.is_not(None))
                    .order_by(ShopifyCollection.updated_at.desc())
                    .limit(remaining)
                )
            ).scalars().all()
        )
        for collection in collections:
            if not collection.handle:
                continue
            url = _build_url(root_url, f"/collections/{collection.handle}")
            if not url:
                continue
            items.append(
                {
                    "url": url,
                    "source": "shopify_collection",
                    "pageType": "collection",
                    "title": collection.title,
                    "metadata": {
                        "shopifyGid": collection.shopify_gid,
                        "handle": collection.handle,
                        "entityType": "collection",
                    },
                }
            )
        remaining = max(0, max_urls - len(items))

    if remaining > 0:
        pages = list(
            (
                await session.execute(
                    select(ShopifyPage)
                    .where(ShopifyPage.shopify_store_id == store.id)
                    .where(ShopifyPage.handle.is_not(None))
                    .order_by(ShopifyPage.updated_at.desc())
                    .limit(remaining)
                )
            ).scalars().all()
        )
        for page in pages:
            if not page.handle:
                continue
            url = _build_url(root_url, f"/pages/{page.handle}")
            if not url:
                continue
            items.append(
                {
                    "url": url,
                    "source": "shopify_page",
                    "pageType": "static_page",
                    "title": page.title,
                    "metadata": {
                        "shopifyGid": page.shopify_gid,
                        "handle": page.handle,
                        "entityType": "page",
                    },
                }
            )
        remaining = max(0, max_urls - len(items))

    if remaining > 0:
        blogs = list(
            (
                await session.execute(
                    select(ShopifyBlog)
                    .where(ShopifyBlog.shopify_store_id == store.id)
                    .where(ShopifyBlog.handle.is_not(None))
                    .order_by(ShopifyBlog.updated_at.desc())
                    .limit(remaining)
                )
            ).scalars().all()
        )
        for blog in blogs:
            if not blog.handle:
                continue
            url = _build_url(root_url, f"/blogs/{blog.handle}")
            if not url:
                continue
            items.append(
                {
                    "url": url,
                    "source": "shopify_blog",
                    "pageType": "blog",
                    "title": blog.title,
                    "metadata": {
                        "shopifyGid": blog.shopify_gid,
                        "handle": blog.handle,
                        "entityType": "blog",
                    },
                }
            )
        remaining = max(0, max_urls - len(items))

    if remaining > 0:
        articles = list(
            (
                await session.execute(
                    select(ShopifyArticle)
                    .where(ShopifyArticle.shopify_store_id == store.id)
                    .where(ShopifyArticle.handle.is_not(None))
                    .options(selectinload(ShopifyArticle.blog))
                    .order_by(ShopifyArticle.updated_at.desc())
                    .limit(remaining)
                )
            ).scalars().all()
        )
        for article in articles:
            if not article.handle:
                continue
            blog_handle = article.blog.handle if article.blog and article.blog.handle else None
            if not blog_handle:
                continue
            url = _build_url(root_url, f"/blogs/{blog_handle}/{article.handle}")
            if not url:
                continue
            items.append(
                {
                    "url": url,
                    "source": "shopify_blog",
                    "pageType": "blog_article",
                    "title": article.title,
                    "metadata": {
                        "shopifyGid": article.shopify_gid,
                        "handle": article.handle,
                        "blogHandle": blog_handle,
                        "entityType": "article",
                    },
                }
            )

    if items:
        events.append(
            _shopify_event(
                "shopify_urls_found",
                f"Trovate {len(items)} URL da dati Shopify sincronizzati.",
                count=len(items),
            )
        )
    else:
        events.append(
            _shopify_event(
                "shopify_urls_missing",
                "Nessuna URL Shopify disponibile dai dati sincronizzati.",
            )
        )

    return items[:max_urls], events
