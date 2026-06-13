"""Apply product metafield changes to Shopify via metafieldsSet."""

from __future__ import annotations

import logging
from typing import Any

from app.services.shopify.client import ShopifyGraphQLClient
from app.services.shopify.metafield_utils import is_editable_metafield_type
from app.services.shopify.metafield_value_format import serialize_metafield_value

logger = logging.getLogger(__name__)

UNSUPPORTED_TYPE_MESSAGE = (
    "Questo tipo di metafield non è ancora modificabile da Growth Control Room."
)


async def apply_product_metafields(
    client: ShopifyGraphQLClient,
    product_gid: str,
    metafields: list[dict[str, Any]],
    shopify_response: dict[str, Any],
) -> list[str]:
    """Apply metafield values. Returns list of warning messages for skipped entries."""
    warnings: list[str] = []
    inputs: list[dict[str, Any]] = []

    for entry in metafields:
        if not isinstance(entry, dict):
            continue
        namespace = str(entry.get("namespace") or "").strip()
        key = str(entry.get("key") or "").strip()
        type_name = str(entry.get("type") or "").strip()
        value = entry.get("value")
        if value is None:
            value = ""
        value_str = str(value)
        if not namespace or not key or not type_name:
            continue
        if not is_editable_metafield_type(type_name, value_str):
            warnings.append(f"{namespace}.{key}: {UNSUPPORTED_TYPE_MESSAGE}")
            continue
        try:
            serialized = serialize_metafield_value(type_name, value_str)
        except ValueError as exc:
            warnings.append(f"{namespace}.{key}: {exc}")
            continue
        inputs.append(
            {
                "ownerId": product_gid,
                "namespace": namespace,
                "key": key,
                "type": type_name,
                "value": serialized,
            }
        )

    if not inputs:
        return warnings

    data = await client.metafields_set(inputs)
    shopify_response["metafieldsSet"] = data.get("metafieldsSet")
    errors = (data.get("metafieldsSet") or {}).get("userErrors") or []
    if errors:
        msg = "; ".join(e.get("message", "") for e in errors[:3])
        logger.warning("metafieldsSet userErrors: %s", msg)
        warnings.append(msg or "Errore durante l'aggiornamento dei metafield su Shopify.")
    return warnings
