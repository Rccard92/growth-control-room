"""Shopify synced entity URL discovery for Growth Audit."""

from __future__ import annotations

import logging
from datetime import datetime
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


def _entity_synced_at(entity: Any, *, is_product: bool = False) -> datetime | None:
    if is_product:
        return getattr(entity, "updated_at_shopify", None) or getattr(
            entity, "updated_at", None
        )
    return getattr(entity, "updated_at", None)


def _build_mapped_entity_item(
    *,
    store_id: UUID,
    url: str,
    source: str,
    page_type: str,
    title: str,
    source_entity_type: str,
    entity_label: str,
    entity: Any,
    extra_metadata: dict[str, Any] | None = None,
    is_product: bool = False,
) -> dict[str, Any]:
    synced_at = _entity_synced_at(entity, is_product=is_product)
    metadata: dict[str, Any] = {
        "shopifyGid": entity.shopify_gid,
        "handle": entity.handle,
        "entityType": entity_label,
        "shopify": {
            "storeId": str(store_id),
            "entityType": entity_label,
            "entityId": str(entity.id),
            "gid": entity.shopify_gid,
            "handle": entity.handle,
            "title": entity.title,
        },
        **(extra_metadata or {}),
    }
    item: dict[str, Any] = {
        "url": url,
        "source": source,
        "pageType": page_type,
        "title": title,
        "sourceEntityType": source_entity_type,
        "sourceEntityId": entity.id,
        "sourceEntityGid": entity.shopify_gid,
        "sourceEntityHandle": entity.handle,
        "sourceEntityTitle": entity.title,
        "sourceEntitySyncedAt": synced_at,
        "metadata": metadata,
    }
    return item


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
                _build_mapped_entity_item(
                    store_id=store.id,
                    url=url,
                    source="shopify_product",
                    page_type="product",
                    title=product.title,
                    source_entity_type="shopify_product",
                    entity_label="product",
                    entity=product,
                    is_product=True,
                )
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
                _build_mapped_entity_item(
                    store_id=store.id,
                    url=url,
                    source="shopify_collection",
                    page_type="collection",
                    title=collection.title,
                    source_entity_type="shopify_collection",
                    entity_label="collection",
                    entity=collection,
                )
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
                _build_mapped_entity_item(
                    store_id=store.id,
                    url=url,
                    source="shopify_page",
                    page_type="static_page",
                    title=page.title,
                    source_entity_type="shopify_page",
                    entity_label="page",
                    entity=page,
                )
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
                _build_mapped_entity_item(
                    store_id=store.id,
                    url=url,
                    source="shopify_blog",
                    page_type="blog_article",
                    title=article.title,
                    source_entity_type="shopify_article",
                    entity_label="article",
                    entity=article,
                    extra_metadata={"blogHandle": blog_handle},
                )
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
