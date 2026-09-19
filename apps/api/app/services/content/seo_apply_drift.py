"""Refuse to overwrite a Shopify entity that changed after the proposal was built.

A proposal freezes `current_values` when it is created. If the merchant edits the
product in Shopify Admin in the meantime, applying the proposal would silently
undo their work. The editorial publisher already has this guard; this gives the
SEO optimizer the same one.
"""

from __future__ import annotations

import logging
from typing import Any

from app.services.shopify.client import ShopifyAPIError, ShopifyGraphQLClient

logger = logging.getLogger(__name__)

DRIFT_MESSAGE = (
    "Questo contenuto è cambiato su Shopify dopo la creazione della proposta. "
    "Usa 'Sincronizza da Shopify' e rigenera la proposta prima di applicare."
)

# Only scalar fields are compared: image alts are handled per media id and a
# reordering of the media list is not a conflict.
_PRODUCT_FIELD_PATHS: dict[str, tuple[str, ...]] = {
    "product_title": ("title",),
    "handle": ("handle",),
    "seo_title": ("seo", "title"),
    "meta_description": ("seo", "description"),
    "description_html": ("descriptionHtml",),
}
_COLLECTION_FIELD_PATHS: dict[str, tuple[str, ...]] = {
    "collection_title": ("title",),
    "handle": ("handle",),
    "seo_title": ("seo", "title"),
    "meta_description": ("seo", "description"),
    "description_html": ("descriptionHtml",),
}


class SeoApplyDriftError(RuntimeError):
    """The live Shopify values no longer match the proposal snapshot."""

    def __init__(self, fields: list[str]) -> None:
        self.fields = fields
        super().__init__(DRIFT_MESSAGE)


def _dig(node: dict[str, Any], path: tuple[str, ...]) -> Any:
    value: Any = node
    for key in path:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def _normalize(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def detect_drift(
    *,
    entity_type: str,
    snapshot: dict[str, Any] | None,
    live_node: dict[str, Any],
    changed_fields: set[str],
) -> list[str]:
    """Fields the proposal wants to change whose live value moved away from the snapshot."""
    paths = _PRODUCT_FIELD_PATHS if entity_type == "product" else _COLLECTION_FIELD_PATHS
    snapshot = snapshot or {}
    drifted: list[str] = []
    for field, path in paths.items():
        if field not in changed_fields:
            continue
        if field not in snapshot:
            # Nothing was recorded for this field, so there is nothing to compare.
            continue
        if _normalize(snapshot.get(field)) != _normalize(_dig(live_node, path)):
            drifted.append(field)
    return drifted


async def assert_no_upstream_drift(
    client: ShopifyGraphQLClient,
    *,
    entity_type: str,
    entity_gid: str,
    snapshot: dict[str, Any] | None,
    changed_fields: set[str],
) -> None:
    if not changed_fields:
        return
    try:
        live_node = (
            await client.fetch_product_by_gid(entity_gid)
            if entity_type == "product"
            else await client.fetch_collection_by_gid(entity_gid)
        )
    except ShopifyAPIError:
        # A read failure must not silently disable the guard, but it must not
        # block an apply either: the write below will surface the real problem.
        logger.warning("Drift check non riuscito per %s, apply proseguito", entity_gid)
        return

    drifted = detect_drift(
        entity_type=entity_type,
        snapshot=snapshot,
        live_node=live_node,
        changed_fields=changed_fields,
    )
    if drifted:
        raise SeoApplyDriftError(drifted)
