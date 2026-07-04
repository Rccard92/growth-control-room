"""Resolve Growth Audit pages to locally synced Shopify entities."""

from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.content_seo import (
    ShopifyArticle,
    ShopifyBlog,
    ShopifyCollection,
    ShopifyPage,
)
from app.models.growth_audit import GrowthAuditPage
from app.models.shopify import ShopifyProduct
from app.services.growth_audit.url_utils import get_url_path
from app.services.shopify.connect import get_shopify_store_for_project

logger = logging.getLogger(__name__)

_PATH_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "shopify_product",
        re.compile(r"^/products/(?P<handle>[^/]+)/?$", re.IGNORECASE),
    ),
    (
        "shopify_collection",
        re.compile(r"^/collections/(?P<handle>[^/]+)/?$", re.IGNORECASE),
    ),
    (
        "shopify_page",
        re.compile(r"^/pages/(?P<handle>[^/]+)/?$", re.IGNORECASE),
    ),
    (
        "shopify_article",
        re.compile(
            r"^/blogs/(?P<blog_handle>[^/]+)/(?P<handle>[^/]+)/?$",
            re.IGNORECASE,
        ),
    ),
]

_ENTITY_TYPE_LABELS = {
    "shopify_product": "product",
    "shopify_collection": "collection",
    "shopify_page": "page",
    "shopify_article": "article",
}


def _normalize_path(path: str | None) -> str | None:
    if not path or not path.strip():
        return None
    normalized = path.strip()
    if not normalized.startswith("/"):
        normalized = f"/{normalized}"
    if len(normalized) > 1 and normalized.endswith("/"):
        normalized = normalized.rstrip("/")
    return normalized or None


def extract_shopify_handle_from_path(path: str, page_type: str = "") -> dict[str, str] | None:
    del page_type  # reserved for future heuristics
    normalized_path = _normalize_path(path)
    if not normalized_path:
        return None

    for entity_type, pattern in _PATH_PATTERNS:
        match = pattern.match(normalized_path)
        if not match:
            continue
        handle = match.group("handle").strip()
        if not handle:
            return None
        result: dict[str, str] = {
            "entityType": entity_type,
            "handle": handle,
        }
        if entity_type == "shopify_article":
            blog_handle = match.group("blog_handle").strip()
            if not blog_handle:
                return None
            result["blogHandle"] = blog_handle
        return result

    return None


def _entity_synced_at(entity: Any, entity_type: str) -> datetime | None:
    if entity_type == "shopify_product":
        return getattr(entity, "updated_at_shopify", None) or getattr(
            entity, "updated_at", None
        )
    return getattr(entity, "updated_at", None)


def _build_resolved_mapping(
    *,
    store_id: UUID,
    entity_type: str,
    entity: Any,
) -> dict[str, Any]:
    entity_label = _ENTITY_TYPE_LABELS.get(entity_type, entity_type)
    synced_at = _entity_synced_at(entity, entity_type)
    return {
        "sourceEntityType": entity_type,
        "sourceEntityId": entity.id,
        "sourceEntityGid": entity.shopify_gid,
        "sourceEntityHandle": entity.handle,
        "sourceEntityTitle": entity.title,
        "sourceEntitySyncedAt": synced_at,
        "metadata": {
            "shopify": {
                "storeId": str(store_id),
                "entityType": entity_label,
                "entityId": str(entity.id),
                "gid": entity.shopify_gid,
                "handle": entity.handle,
                "title": entity.title,
            }
        },
    }


async def resolve_shopify_entity_for_page(
    session: AsyncSession,
    page: GrowthAuditPage,
) -> dict[str, Any] | None:
    path = _normalize_path(page.path) or _normalize_path(get_url_path(page.normalized_url))
    if not path:
        return None

    extracted = extract_shopify_handle_from_path(path, page.page_type)
    if extracted is None:
        return None

    store = await get_shopify_store_for_project(page.project_id, session)
    if store is None:
        return None

    entity_type = extracted["entityType"]
    handle = extracted["handle"]

    if entity_type == "shopify_product":
        entity = (
            await session.execute(
                select(ShopifyProduct)
                .where(ShopifyProduct.shopify_store_id == store.id)
                .where(ShopifyProduct.handle == handle)
                .limit(1)
            )
        ).scalar_one_or_none()
    elif entity_type == "shopify_collection":
        entity = (
            await session.execute(
                select(ShopifyCollection)
                .where(ShopifyCollection.shopify_store_id == store.id)
                .where(ShopifyCollection.handle == handle)
                .limit(1)
            )
        ).scalar_one_or_none()
    elif entity_type == "shopify_page":
        entity = (
            await session.execute(
                select(ShopifyPage)
                .where(ShopifyPage.shopify_store_id == store.id)
                .where(ShopifyPage.handle == handle)
                .limit(1)
            )
        ).scalar_one_or_none()
    elif entity_type == "shopify_article":
        blog_handle = extracted.get("blogHandle")
        query = (
            select(ShopifyArticle)
            .where(ShopifyArticle.shopify_store_id == store.id)
            .where(ShopifyArticle.handle == handle)
            .options(selectinload(ShopifyArticle.blog))
            .limit(1)
        )
        entity = (await session.execute(query)).scalar_one_or_none()
        if entity is not None and blog_handle:
            if entity.blog is None or entity.blog.handle != blog_handle:
                entity = None
    else:
        return None

    if entity is None:
        return None

    return _build_resolved_mapping(
        store_id=store.id,
        entity_type=entity_type,
        entity=entity,
    )


def apply_shopify_entity_mapping_to_page(
    page: GrowthAuditPage,
    resolved: dict[str, Any] | None,
) -> None:
    if resolved is None:
        return

    page.source_entity_type = resolved.get("sourceEntityType")
    page.source_entity_id = resolved.get("sourceEntityId")
    page.source_entity_gid = resolved.get("sourceEntityGid")
    page.source_entity_handle = resolved.get("sourceEntityHandle")
    page.source_entity_title = resolved.get("sourceEntityTitle")
    page.source_entity_synced_at = resolved.get("sourceEntitySyncedAt")

    shopify_metadata = (resolved.get("metadata") or {}).get("shopify")
    if shopify_metadata:
        page.page_metadata = {
            **(page.page_metadata or {}),
            "shopify": {
                **((page.page_metadata or {}).get("shopify") or {}),
                **shopify_metadata,
            },
        }


async def resolve_shopify_entities_for_pages(
    session: AsyncSession,
    pages: list[GrowthAuditPage],
) -> int:
    mapped_count = 0
    for page in pages:
        if page.source_entity_id is not None:
            continue
        try:
            resolved = await resolve_shopify_entity_for_page(session, page)
            if resolved is None:
                continue
            apply_shopify_entity_mapping_to_page(page, resolved)
            mapped_count += 1
        except Exception as exc:
            logger.warning(
                "Failed to resolve Shopify entity for page %s: %s",
                page.id,
                exc,
            )
    return mapped_count
