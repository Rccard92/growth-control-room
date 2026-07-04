"""Merge and normalize discovered URLs into Growth Audit page inventory."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from app.services.growth_audit.page_classifier import classify_page_type
from app.services.growth_audit.url_utils import (
    get_url_path,
    is_excluded_audit_url,
    normalize_url,
)


def _normalize_hostname(hostname: str) -> str:
    host = hostname.lower().strip().rstrip(".")
    if host.startswith("www."):
        return host[4:]
    return host


def same_domain(url: str, root_domain: str) -> bool:
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            return False
        return _normalize_hostname(hostname) == _normalize_hostname(root_domain)
    except Exception:
        return False


def _build_inventory_item(
    *,
    url: str,
    source: str,
    page_type: str | None = None,
    title: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    if is_excluded_audit_url(url):
        return None
    try:
        normalized_url = normalize_url(url)
    except Exception:
        return None

    resolved_page_type = page_type or classify_page_type(
        normalized_url,
        title=title,
        metadata=metadata,
    )
    return {
        "url": normalized_url,
        "normalizedUrl": normalized_url,
        "path": get_url_path(normalized_url),
        "source": source,
        "pageType": resolved_page_type,
        "title": title,
        "metadata": metadata or {},
    }


_SOURCE_ENTITY_KEYS = (
    "sourceEntityType",
    "sourceEntityId",
    "sourceEntityGid",
    "sourceEntityHandle",
    "sourceEntityTitle",
    "sourceEntitySyncedAt",
)


def _attach_source_entity_fields(
    item: dict[str, Any] | None,
    source: dict[str, Any],
) -> dict[str, Any] | None:
    if item is None:
        return None
    for key in _SOURCE_ENTITY_KEYS:
        if key in source:
            item[key] = source[key]
    return item


def merge_discovered_urls(
    seed_url: str,
    sitemap_urls: list[str],
    shopify_items: list[dict[str, Any]],
    max_pages: int,
    root_domain: str,
) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    by_normalized: dict[str, dict[str, Any]] = {}

    def _upsert(item: dict[str, Any] | None, *, prefer_shopify: bool = False) -> None:
        if item is None:
            return
        normalized = item["normalizedUrl"]
        if not same_domain(normalized, root_domain):
            return
        existing = by_normalized.get(normalized)
        if existing is None:
            by_normalized[normalized] = item
            return
        if prefer_shopify:
            by_normalized[normalized] = {
                **existing,
                **item,
                "metadata": {
                    **(existing.get("metadata") or {}),
                    **(item.get("metadata") or {}),
                },
            }

    seed_item = _build_inventory_item(url=seed_url, source="seed")
    if seed_item is not None:
        _upsert(seed_item)

    for shopify_item in shopify_items:
        item = _build_inventory_item(
            url=shopify_item["url"],
            source=shopify_item.get("source", "shopify_product"),
            page_type=shopify_item.get("pageType"),
            title=shopify_item.get("title"),
            metadata=shopify_item.get("metadata"),
        )
        item = _attach_source_entity_fields(item, shopify_item)
        _upsert(item, prefer_shopify=True)

    for sitemap_url in sitemap_urls:
        item = _build_inventory_item(url=sitemap_url, source="sitemap")
        _upsert(item)

    seed_normalized = None
    if seed_item is not None:
        seed_normalized = seed_item["normalizedUrl"]

    ordered_keys: list[str] = []
    if seed_normalized and seed_normalized in by_normalized:
        ordered_keys.append(seed_normalized)

    shopify_keys = [
        key
        for key, value in by_normalized.items()
        if key not in ordered_keys and value.get("source", "").startswith("shopify_")
    ]
    shopify_keys.sort()
    ordered_keys.extend(shopify_keys)

    sitemap_keys = [
        key
        for key, value in by_normalized.items()
        if key not in ordered_keys and value.get("source") == "sitemap"
    ]
    sitemap_keys.sort()
    ordered_keys.extend(sitemap_keys)

    other_keys = [key for key in by_normalized if key not in ordered_keys]
    other_keys.sort()
    ordered_keys.extend(other_keys)

    for key in ordered_keys[:max_pages]:
        merged.append(by_normalized[key])

    return merged
