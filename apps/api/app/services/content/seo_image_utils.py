"""Helpers for product/collection image ALT applicability and normalization."""

from __future__ import annotations

from typing import Any

_SHOPIFY_GID_PREFIXES = (
    "gid://shopify/MediaImage/",
    "gid://shopify/ProductImage/",
    "gid://shopify/ImageSource/",
)


def is_shopify_image_gid(image_id: str | None) -> bool:
    if not image_id or not str(image_id).strip():
        return False
    value = str(image_id).strip()
    return any(value.startswith(prefix) for prefix in _SHOPIFY_GID_PREFIXES)


def image_applicability(image: dict[str, Any] | None) -> tuple[bool, str | None]:
    """Return (shopify_applicable, reason_if_not)."""
    if not image or not isinstance(image, dict):
        return False, "missing_image"
    image_id = str(image.get("id") or image.get("image_id") or "").strip()
    url = str(image.get("url") or image.get("src") or "").strip()
    if not image_id:
        if url:
            return False, "missing_shopify_id"
        return False, "missing_url"
    if not is_shopify_image_gid(image_id):
        return False, "invalid_shopify_id"
    return True, None


def normalize_product_image_row(image: dict[str, Any], *, index: int = 0) -> dict[str, Any]:
    row = dict(image)
    image_id = str(row.get("id") or row.get("image_id") or "").strip()
    if image_id:
        row["id"] = image_id
    applicable, reason = image_applicability(row)
    row["shopifyApplicable"] = applicable
    row["applicabilityReason"] = reason
    row.setdefault("position", index + 1)
    if row.get("altText") is None and row.get("alt") is not None:
        row["altText"] = row.get("alt")
    return row


def normalize_product_images(images: list[Any] | None) -> list[dict[str, Any]]:
    if not images:
        return []
    result: list[dict[str, Any]] = []
    for index, item in enumerate(images):
        if isinstance(item, dict):
            result.append(normalize_product_image_row(item, index=index))
    return result


def resolve_product_image(
    current: dict[str, Any],
    image_id: str | None,
) -> dict[str, Any]:
    """Resolve product image by Shopify GID; raise ValueError with explicit message."""
    if not image_id or not str(image_id).strip():
        raise ValueError("image_id richiesto per imageAlt prodotto")
    normalized_id = str(image_id).strip()
    if not is_shopify_image_gid(normalized_id):
        raise ValueError("Immagine senza riferimento Shopify — sincronizza il prodotto")
    media = current.get("media_images") or []
    target = next(
        (m for m in media if str(m.get("id") or m.get("image_id") or "") == normalized_id),
        None,
    )
    if target is None:
        raise ValueError("Immagine non trovata nel prodotto")
    applicable, reason = image_applicability(target if isinstance(target, dict) else {})
    if not applicable:
        if reason == "missing_shopify_id":
            raise ValueError("Immagine senza riferimento Shopify — sincronizza il prodotto")
        if reason == "missing_url":
            raise ValueError("URL immagine mancante")
        raise ValueError("Campo non aggiornabile su Shopify")
    return target if isinstance(target, dict) else {}


def merge_media_image_alts(
    existing: list[Any] | None,
    *,
    alt_by_id: dict[str, str] | None = None,
    proposed_media: list[Any] | None = None,
    shopify_media: list[Any] | None = None,
) -> list[dict[str, Any]]:
    """Merge alt updates into full media_images array (never return partial subset)."""
    base_rows: list[dict[str, Any]] = []
    for index, item in enumerate(existing or []):
        if isinstance(item, dict):
            base_rows.append(dict(item))

    if proposed_media:
        proposed_by_id = {
            str(row.get("id") or row.get("image_id") or ""): dict(row)
            for row in proposed_media
            if isinstance(row, dict) and str(row.get("id") or row.get("image_id") or "")
        }
        if proposed_by_id:
            merged: list[dict[str, Any]] = []
            seen: set[str] = set()
            for index, row in enumerate(base_rows):
                image_id = str(row.get("id") or row.get("image_id") or "")
                if image_id in proposed_by_id:
                    merged.append({**row, **proposed_by_id[image_id]})
                    seen.add(image_id)
                else:
                    merged.append(row)
            for image_id, row in proposed_by_id.items():
                if image_id not in seen:
                    merged.append(row)
            base_rows = merged

    shopify_alt_by_id: dict[str, str] = {}
    for item in shopify_media or []:
        if not isinstance(item, dict):
            continue
        image_id = str(item.get("id") or "")
        alt = str(item.get("alt") or item.get("altText") or "").strip()
        if image_id and alt:
            shopify_alt_by_id[image_id] = alt

    effective_alts = {**(alt_by_id or {}), **shopify_alt_by_id}
    if not effective_alts:
        return [normalize_product_image_row(row, index=i) for i, row in enumerate(base_rows)]

    result: list[dict[str, Any]] = []
    for index, row in enumerate(base_rows):
        image_id = str(row.get("id") or row.get("image_id") or "")
        next_row = dict(row)
        if image_id in effective_alts:
            next_row["altText"] = effective_alts[image_id]
            next_row["alt"] = effective_alts[image_id]
        result.append(normalize_product_image_row(next_row, index=index))
    return result


def extract_shopify_media_alts(shopify_response: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not shopify_response:
        return []
    block = shopify_response.get("productUpdateMedia") or {}
    media = block.get("media") or []
    return [item for item in media if isinstance(item, dict)]


def collection_image_applicable(collection_image_url: str | None, collection_gid: str | None) -> tuple[bool, str | None]:
    if not collection_gid:
        return False, "missing_collection"
    if not collection_image_url or not str(collection_image_url).strip():
        return False, "missing_image"
    return True, None
