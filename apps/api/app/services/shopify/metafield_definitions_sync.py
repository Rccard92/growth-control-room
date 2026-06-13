"""Sync Shopify metafield definitions into local DB."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shopify import ShopifyMetafieldDefinition, ShopifyStore
from app.services.shopify.client import ShopifyGraphQLClient

logger = logging.getLogger(__name__)

OWNER_PRODUCT = "PRODUCT"


def _parse_definition_node(node: dict[str, Any]) -> dict[str, Any] | None:
    gid = node.get("id")
    namespace = node.get("namespace")
    key = node.get("key")
    owner_type = node.get("ownerType") or OWNER_PRODUCT
    type_block = node.get("type") or {}
    type_name = type_block.get("name") if isinstance(type_block, dict) else type_block
    if not gid or not namespace or not key or not type_name:
        return None
    validations_raw = node.get("validations") or []
    validations: list[dict[str, Any]] = []
    if isinstance(validations_raw, list):
        for v in validations_raw:
            if isinstance(v, dict):
                validations.append(v)
    return {
        "shopify_definition_gid": str(gid),
        "owner_type": str(owner_type),
        "namespace": str(namespace),
        "key": str(key),
        "name": node.get("name"),
        "description": node.get("description"),
        "type_name": str(type_name),
        "type_category": type_block.get("category") if isinstance(type_block, dict) else None,
        "validations": validations or None,
        "raw_payload": node,
    }


async def sync_metafield_definitions(
    store: ShopifyStore,
    client: ShopifyGraphQLClient,
    session: AsyncSession,
    *,
    owner_type: str = OWNER_PRODUCT,
) -> dict[str, Any]:
    warnings: list[str] = []
    try:
        nodes = await client.fetch_metafield_definitions(owner_type=owner_type)
    except Exception as exc:
        logger.warning("metafield definitions sync failed: %s", exc)
        raise

    existing = list(
        (
            await session.execute(
                select(ShopifyMetafieldDefinition).where(
                    ShopifyMetafieldDefinition.shopify_store_id == store.id,
                    ShopifyMetafieldDefinition.owner_type == owner_type,
                )
            )
        ).scalars().all()
    )
    by_ns_key = {(r.namespace, r.key): r for r in existing}
    seen_ns_keys: set[tuple[str, str]] = set()
    synced = 0

    for node in nodes:
        parsed = _parse_definition_node(node)
        if parsed is None:
            warnings.append("Definizione metafield ignorata: dati incompleti")
            continue
        ns_key = (parsed["namespace"], parsed["key"])
        seen_ns_keys.add(ns_key)
        row = by_ns_key.get(ns_key)
        if row is None:
            row = ShopifyMetafieldDefinition(
                id=uuid.uuid4(),
                shopify_store_id=store.id,
                **parsed,
            )
            session.add(row)
            by_ns_key[ns_key] = row
        else:
            row.shopify_definition_gid = parsed["shopify_definition_gid"]
            row.name = parsed["name"]
            row.description = parsed["description"]
            row.type_name = parsed["type_name"]
            row.type_category = parsed["type_category"]
            row.validations = parsed["validations"]
            row.raw_payload = parsed["raw_payload"]
        synced += 1

    stale_ids = [
        r.id
        for (ns, k), r in by_ns_key.items()
        if (ns, k) not in seen_ns_keys
    ]
    if stale_ids:
        await session.execute(
            delete(ShopifyMetafieldDefinition).where(
                ShopifyMetafieldDefinition.id.in_(stale_ids)
            )
        )

    await session.flush()
    return {
        "definitions_synced": synced,
        "owner_type": owner_type,
        "warnings": warnings,
    }
