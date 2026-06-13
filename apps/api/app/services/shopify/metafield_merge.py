"""Merge store metafield definitions with product metafield values."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shopify import (
    ShopifyMetafieldDefinition,
    ShopifyProductMetafield,
    ShopifyStore,
)
from app.services.shopify.metafield_utils import merged_metafield_item


async def build_product_metafields_merged(
    store: ShopifyStore,
    session: AsyncSession,
    product_id: UUID,
) -> tuple[list[dict[str, Any]], int]:
    definitions = list(
        (
            await session.execute(
                select(ShopifyMetafieldDefinition)
                .where(
                    ShopifyMetafieldDefinition.shopify_store_id == store.id,
                    ShopifyMetafieldDefinition.owner_type == "PRODUCT",
                )
                .order_by(ShopifyMetafieldDefinition.namespace, ShopifyMetafieldDefinition.key)
            )
        ).scalars().all()
    )
    value_rows = list(
        (
            await session.execute(
                select(ShopifyProductMetafield)
                .where(
                    ShopifyProductMetafield.shopify_store_id == store.id,
                    ShopifyProductMetafield.product_id == product_id,
                )
                .order_by(ShopifyProductMetafield.namespace, ShopifyProductMetafield.key)
            )
        ).scalars().all()
    )

    values_by_ns_key: dict[tuple[str, str], ShopifyProductMetafield] = {
        (r.namespace, r.key): r for r in value_rows
    }
    matched_keys: set[tuple[str, str]] = set()
    items: list[dict[str, Any]] = []

    for definition in definitions:
        ns_key = (definition.namespace, definition.key)
        matched_keys.add(ns_key)
        value_row = values_by_ns_key.get(ns_key)
        items.append(
            merged_metafield_item(
                definition=definition,
                value_row=value_row,
            )
        )

    for ns_key, value_row in values_by_ns_key.items():
        if ns_key in matched_keys:
            continue
        items.append(
            merged_metafield_item(
                definition=None,
                value_row=value_row,
            )
        )

    items.sort(key=_sort_key)
    return items, len(definitions)


def _sort_key(item: dict[str, Any]) -> tuple[int, int, str, str]:
    readonly = 0 if item.get("editable") else 2
    empty_ai = 0 if item.get("is_empty") and item.get("ai_generatable") else 1
    if not item.get("is_empty") and item.get("editable"):
        empty_ai = 1
    name = str(item.get("definition_name") or item.get("namespace") or "")
    key = str(item.get("key") or "")
    return (readonly, empty_ai, name.lower(), key.lower())
