"""Apply proposed SEO values to local Shopify entity records after Shopify mutation."""

from __future__ import annotations

from copy import deepcopy
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_seo import ShopifyCollection
from app.models.shopify import ShopifyProduct
from app.services.shopify.html_utils import html_to_text


def _get_proposed(proposed: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in proposed and proposed[key] is not None:
            return proposed[key]
    return None


def _merge_raw_payload(
    existing: dict[str, Any] | None,
    updates: dict[str, Any],
) -> dict[str, Any]:
    base = deepcopy(existing) if isinstance(existing, dict) else {}
    for key, val in updates.items():
        if val is not None:
            base[key] = val
    return base


def _apply_shopify_product_node(product: ShopifyProduct, node: dict[str, Any]) -> None:
    seo = node.get("seo") or {}
    product.title = node.get("title") or product.title
    product.handle = node.get("handle") or product.handle
    product.seo_title = seo.get("title") if seo.get("title") is not None else product.seo_title
    product.seo_description = (
        seo.get("description")
        if seo.get("description") is not None
        else product.seo_description
    )
    if node.get("descriptionHtml") is not None:
        product.description_html = node.get("descriptionHtml")
        product.description_text = html_to_text(product.description_html)
    product.raw_payload = _merge_raw_payload(
        product.raw_payload,
        {
            "title": product.title,
            "handle": product.handle,
            "seo": seo,
            "descriptionHtml": product.description_html,
        },
    )


def _apply_shopify_collection_node(collection: ShopifyCollection, node: dict[str, Any]) -> None:
    seo = node.get("seo") or {}
    collection.title = node.get("title") or collection.title
    collection.handle = node.get("handle") or collection.handle
    collection.seo_title = seo.get("title") if seo.get("title") is not None else collection.seo_title
    collection.seo_description = (
        seo.get("description")
        if seo.get("description") is not None
        else collection.seo_description
    )
    if node.get("descriptionHtml") is not None:
        collection.description_html = node.get("descriptionHtml")
        collection.description_text = html_to_text(collection.description_html)
    image = node.get("image") or {}
    if image.get("altText") is not None:
        collection.image_alt = image.get("altText")
    collection.raw_payload = _merge_raw_payload(
        collection.raw_payload,
        {
            "title": collection.title,
            "handle": collection.handle,
            "seo": seo,
            "descriptionHtml": collection.description_html,
            "image": image,
        },
    )


async def apply_proposed_values_to_product(
    session: AsyncSession,
    product_id: UUID,
    proposed: dict[str, Any],
    *,
    shopify_node: dict[str, Any] | None = None,
) -> ShopifyProduct | None:
    product = (
        await session.execute(select(ShopifyProduct).where(ShopifyProduct.id == product_id))
    ).scalar_one_or_none()
    if product is None:
        return None

    if shopify_node:
        _apply_shopify_product_node(product, shopify_node)
    else:
        title = _get_proposed(proposed, "product_title", "proposed_product_title")
        if title:
            product.title = title
        handle = _get_proposed(proposed, "handle", "proposed_handle")
        if handle:
            product.handle = handle
        seo_title = _get_proposed(proposed, "seo_title", "proposed_seo_title")
        if seo_title:
            product.seo_title = seo_title
        meta = _get_proposed(proposed, "meta_description", "proposed_meta_description")
        if meta:
            product.seo_description = meta
        desc_html = _get_proposed(proposed, "description_html", "proposed_description_html")
        if desc_html:
            product.description_html = desc_html
            product.description_text = html_to_text(desc_html)
        tags = _get_proposed(proposed, "tags", "proposed_tags")
        if tags is not None:
            product.tags = tags
        media = _get_proposed(proposed, "media_images", "images")
        if media is not None:
            product.media_images = media

        product.raw_payload = _merge_raw_payload(
            product.raw_payload,
            {
                "title": product.title,
                "handle": product.handle,
                "seo": {"title": product.seo_title, "description": product.seo_description},
                "descriptionHtml": product.description_html,
                "tags": product.tags,
            },
        )

    await session.flush()
    return product


async def apply_proposed_values_to_collection(
    session: AsyncSession,
    collection_id: UUID,
    proposed: dict[str, Any],
    *,
    shopify_node: dict[str, Any] | None = None,
) -> ShopifyCollection | None:
    collection = (
        await session.execute(
            select(ShopifyCollection).where(ShopifyCollection.id == collection_id)
        )
    ).scalar_one_or_none()
    if collection is None:
        return None

    if shopify_node:
        _apply_shopify_collection_node(collection, shopify_node)
    else:
        title = _get_proposed(proposed, "collection_title", "proposed_collection_title")
        if title:
            collection.title = title
        handle = _get_proposed(proposed, "handle", "proposed_handle")
        if handle:
            collection.handle = handle
        seo_title = _get_proposed(proposed, "seo_title", "proposed_seo_title")
        if seo_title:
            collection.seo_title = seo_title
        meta = _get_proposed(proposed, "meta_description", "proposed_meta_description")
        if meta:
            collection.seo_description = meta
        desc_html = _get_proposed(
            proposed, "description_html", "proposed_description", "proposed_description_html"
        )
        if desc_html:
            collection.description_html = desc_html
            collection.description_text = html_to_text(desc_html)
        image_alt = _get_proposed(proposed, "image_alt", "proposed_image_alt")
        if image_alt:
            collection.image_alt = image_alt

        collection.raw_payload = _merge_raw_payload(
            collection.raw_payload,
            {
                "title": collection.title,
                "handle": collection.handle,
                "seo": {"title": collection.seo_title, "description": collection.seo_description},
                "descriptionHtml": collection.description_html,
            },
        )

    await session.flush()
    return collection


async def apply_proposed_values_to_entity(
    session: AsyncSession,
    entity_type: str,
    entity_id: UUID,
    proposed: dict[str, Any],
    *,
    shopify_response: dict[str, Any] | None = None,
) -> ShopifyProduct | ShopifyCollection | None:
    shopify_node: dict[str, Any] | None = None
    if shopify_response:
        if entity_type == "product":
            shopify_node = (shopify_response.get("productUpdate") or {}).get("product")
        elif entity_type == "collection":
            shopify_node = (shopify_response.get("collectionUpdate") or {}).get("collection")

    if entity_type == "product":
        return await apply_proposed_values_to_product(
            session, entity_id, proposed, shopify_node=shopify_node
        )
    if entity_type == "collection":
        return await apply_proposed_values_to_collection(
            session, entity_id, proposed, shopify_node=shopify_node
        )
    return None
