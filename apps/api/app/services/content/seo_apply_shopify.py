"""Build minimal Shopify mutation inputs from SEO field deltas."""

from __future__ import annotations

from typing import Any

from app.services.shopify.client import ShopifyAPIError, ShopifyGraphQLClient


def _get_delta(delta: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in delta and delta[key] is not None:
            return delta[key]
    return None


def build_product_update_input(entity_gid: str, delta: dict[str, Any]) -> dict[str, Any] | None:
    input_data: dict[str, Any] = {"id": entity_gid}
    has_scalar = False

    title = _get_delta(delta, "product_title", "proposed_product_title")
    if title is not None:
        input_data["title"] = title
        has_scalar = True

    handle = _get_delta(delta, "handle", "proposed_handle")
    if handle is not None:
        input_data["handle"] = handle
        has_scalar = True

    seo_block: dict[str, str] = {}
    seo_title = _get_delta(delta, "seo_title", "proposed_seo_title")
    if seo_title is not None:
        seo_block["title"] = str(seo_title)
        has_scalar = True
    meta = _get_delta(delta, "meta_description", "proposed_meta_description")
    if meta is not None:
        seo_block["description"] = str(meta)
        has_scalar = True
    if seo_block:
        input_data["seo"] = seo_block

    desc_html = _get_delta(delta, "description_html", "proposed_description_html")
    if desc_html is not None:
        input_data["descriptionHtml"] = desc_html
        has_scalar = True

    if not has_scalar:
        return None
    return input_data


def build_collection_update_input(entity_gid: str, delta: dict[str, Any]) -> dict[str, Any] | None:
    input_data: dict[str, Any] = {"id": entity_gid}
    has_scalar = False

    title = _get_delta(delta, "collection_title", "proposed_collection_title")
    if title is not None:
        input_data["title"] = title
        has_scalar = True

    handle = _get_delta(delta, "handle", "proposed_handle")
    if handle is not None:
        input_data["handle"] = handle
        has_scalar = True

    desc_html = _get_delta(delta, "description_html", "proposed_description", "proposed_description_html")
    if desc_html is not None:
        input_data["descriptionHtml"] = desc_html
        has_scalar = True

    seo_block: dict[str, str] = {}
    seo_title = _get_delta(delta, "seo_title", "proposed_seo_title")
    if seo_title is not None:
        seo_block["title"] = str(seo_title)
        has_scalar = True
    meta = _get_delta(delta, "meta_description", "proposed_meta_description")
    if meta is not None:
        seo_block["description"] = str(meta)
        has_scalar = True
    if seo_block:
        input_data["seo"] = seo_block

    if not has_scalar:
        return None
    return input_data


async def apply_product_scalar_update(
    client: ShopifyGraphQLClient,
    entity_gid: str,
    delta: dict[str, Any],
    shopify_response: dict[str, Any],
) -> None:
    input_data = build_product_update_input(entity_gid, delta)
    if not input_data:
        return
    mutation = """
    mutation ProductUpdate($input: ProductInput!) {
      productUpdate(input: $input) {
        product { id title handle seo { title description } descriptionHtml }
        userErrors { field message }
      }
    }
    """
    data = await client.execute(mutation, {"input": input_data})
    shopify_response["productUpdate"] = data.get("productUpdate")
    errors = (data.get("productUpdate") or {}).get("userErrors") or []
    if errors:
        raise ShopifyAPIError("; ".join(e.get("message", "") for e in errors[:3]))


async def apply_collection_scalar_update(
    client: ShopifyGraphQLClient,
    entity_gid: str,
    delta: dict[str, Any],
    shopify_response: dict[str, Any],
) -> None:
    input_data = build_collection_update_input(entity_gid, delta)
    if not input_data:
        return
    mutation = """
    mutation CollectionUpdate($input: CollectionInput!) {
      collectionUpdate(input: $input) {
        collection { id title handle seo { title description } descriptionHtml }
        userErrors { field message }
      }
    }
    """
    data = await client.execute(mutation, {"input": input_data})
    shopify_response["collectionUpdate"] = data.get("collectionUpdate")
    errors = (data.get("collectionUpdate") or {}).get("userErrors") or []
    if errors:
        raise ShopifyAPIError("; ".join(e.get("message", "") for e in errors[:3]))


async def apply_product_media_alts(
    client: ShopifyGraphQLClient,
    product_gid: str,
    delta: dict[str, Any],
    shopify_response: dict[str, Any],
) -> None:
    media_updates: list[dict[str, str]] = []
    image_alts = _get_delta(delta, "image_alts", "imageAlts") or []
    alt_by_id = {
        str(item.get("image_id") or item.get("imageId") or ""): str(
            item.get("proposed_alt") or item.get("proposedAlt") or item.get("alt") or ""
        )
        for item in image_alts
        if isinstance(item, dict)
    }
    for image_id, alt in alt_by_id.items():
        if image_id and alt.strip():
            media_updates.append({"id": image_id, "alt": alt.strip()})

    if not media_updates:
        return

    mutation = """
    mutation ProductUpdateMedia($productId: ID!, $media: [UpdateMediaInput!]!) {
      productUpdateMedia(productId: $productId, media: $media) {
        media { id alt }
        mediaUserErrors { field message }
      }
    }
    """
    data = await client.execute(
        mutation,
        {"productId": product_gid, "media": media_updates},
    )
    shopify_response["productUpdateMedia"] = data.get("productUpdateMedia")
    errors = (data.get("productUpdateMedia") or {}).get("mediaUserErrors") or []
    if errors:
        raise ShopifyAPIError("; ".join(e.get("message", "") for e in errors[:3]))


async def apply_collection_image_alt(
    client: ShopifyGraphQLClient,
    collection_gid: str,
    delta: dict[str, Any],
    shopify_response: dict[str, Any],
) -> None:
    image_alt = _get_delta(delta, "image_alt", "proposed_image_alt")
    if not image_alt:
        return
    mutation = """
    mutation CollectionUpdateImageAlt($input: CollectionInput!) {
      collectionUpdate(input: $input) {
        collection { id image { altText } }
        userErrors { field message }
      }
    }
    """
    data = await client.execute(
        mutation,
        {"input": {"id": collection_gid, "image": {"altText": str(image_alt)}}},
    )
    shopify_response["collectionImageAltUpdate"] = data.get("collectionUpdate")
    errors = (data.get("collectionUpdate") or {}).get("userErrors") or []
    if errors:
        raise ShopifyAPIError("; ".join(e.get("message", "") for e in errors[:3]))
