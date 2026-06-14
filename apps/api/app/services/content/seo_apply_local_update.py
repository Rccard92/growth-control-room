"""Apply proposed SEO values to local Shopify entity records after Shopify mutation."""

from __future__ import annotations

import uuid
from copy import deepcopy
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_seo import ShopifyCollection
from app.models.shopify import (
    ShopifyMetafieldDefinition,
    ShopifyProduct,
    ShopifyProductMetafield,
    ShopifyStore,
)
from app.services.content.seo_image_utils import (
    extract_shopify_media_alts,
    merge_media_image_alts,
    normalize_product_images,
)
from app.services.shopify.html_utils import html_to_text
from app.services.shopify.metafield_value_format import serialize_metafield_value


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


async def _upsert_product_metafields_from_proposed(
    session: AsyncSession,
    store_id: UUID,
    product_id: UUID,
    proposed: dict[str, Any],
    shopify_response: dict[str, Any] | None,
) -> None:
    metafields = proposed.get("metafields")
    if not isinstance(metafields, list):
        return

    shopify_by_ns_key: dict[tuple[str, str], dict[str, Any]] = {}
    if shopify_response:
        set_block = shopify_response.get("metafieldsSet") or {}
        for node in set_block.get("metafields") or []:
            if isinstance(node, dict):
                ns = str(node.get("namespace") or "")
                key = str(node.get("key") or "")
                if ns and key:
                    shopify_by_ns_key[(ns, key)] = node

    for entry in metafields:
        if not isinstance(entry, dict):
            continue
        namespace = str(entry.get("namespace") or "")
        key = str(entry.get("key") or "")
        type_name = str(entry.get("type") or "")
        display_val = str(entry.get("value") or "")
        if not namespace or not key or not type_name:
            continue
        try:
            raw_value = serialize_metafield_value(type_name, display_val)
        except ValueError:
            raw_value = display_val

        shopify_node = shopify_by_ns_key.get((namespace, key))
        shopify_gid = str(shopify_node.get("id") or "") if shopify_node else ""

        mid = entry.get("metafield_id") or entry.get("id")
        row: ShopifyProductMetafield | None = None
        if mid:
            try:
                mf_uuid = UUID(str(mid))
                row = (
                    await session.execute(
                        select(ShopifyProductMetafield).where(
                            ShopifyProductMetafield.id == mf_uuid,
                            ShopifyProductMetafield.product_id == product_id,
                        )
                    )
                ).scalar_one_or_none()
            except ValueError:
                row = None
        if row is None:
            row = (
                await session.execute(
                    select(ShopifyProductMetafield).where(
                        ShopifyProductMetafield.shopify_store_id == store_id,
                        ShopifyProductMetafield.product_id == product_id,
                        ShopifyProductMetafield.namespace == namespace,
                        ShopifyProductMetafield.key == key,
                    )
                )
            ).scalar_one_or_none()

        definition_id = entry.get("definition_id") or entry.get("definitionId")
        def_name: str | None = None
        def_desc: str | None = None
        if definition_id:
            try:
                def_row = (
                    await session.execute(
                        select(ShopifyMetafieldDefinition).where(
                            ShopifyMetafieldDefinition.id == UUID(str(definition_id)),
                            ShopifyMetafieldDefinition.shopify_store_id == store_id,
                        )
                    )
                ).scalar_one_or_none()
                if def_row is not None:
                    def_name = def_row.name
                    def_desc = def_row.description
            except ValueError:
                pass

        if row is not None:
            row.value = raw_value
            if shopify_gid:
                row.shopify_metafield_gid = shopify_gid
            if def_name:
                row.definition_name = def_name
            if def_desc:
                row.definition_description = def_desc
            continue

        if not shopify_gid:
            shopify_gid = f"gid://shopify/Metafield/pending-{namespace}-{key}"
        row = ShopifyProductMetafield(
            id=uuid.uuid4(),
            shopify_store_id=store_id,
            product_id=product_id,
            shopify_metafield_gid=shopify_gid,
            namespace=namespace,
            key=key,
            type=type_name,
            value=raw_value,
            definition_name=def_name,
            definition_description=def_desc,
            raw_payload=shopify_node,
        )
        session.add(row)


async def apply_proposed_values_to_product(
    session: AsyncSession,
    product_id: UUID,
    proposed: dict[str, Any],
    *,
    shopify_node: dict[str, Any] | None = None,
    shopify_response: dict[str, Any] | None = None,
    store_id: UUID | None = None,
) -> ShopifyProduct | None:
    product = (
        await session.execute(select(ShopifyProduct).where(ShopifyProduct.id == product_id))
    ).scalar_one_or_none()
    if product is None:
        return None

    if shopify_node:
        _apply_shopify_product_node(product, shopify_node)

    title = _get_proposed(proposed, "product_title", "proposed_product_title")
    if title and not shopify_node:
        product.title = title
    handle = _get_proposed(proposed, "handle", "proposed_handle")
    if handle and not shopify_node:
        product.handle = handle
    seo_title = _get_proposed(proposed, "seo_title", "proposed_seo_title")
    if seo_title and not shopify_node:
        product.seo_title = seo_title
    meta = _get_proposed(proposed, "meta_description", "proposed_meta_description")
    if meta and not shopify_node:
        product.seo_description = meta
    desc_html = _get_proposed(proposed, "description_html", "proposed_description_html")
    if desc_html and not shopify_node:
        product.description_html = desc_html
        product.description_text = html_to_text(desc_html)

    alt_by_id: dict[str, str] = {}
    image_alts = proposed.get("image_alts") or proposed.get("imageAlts") or []
    if isinstance(image_alts, list):
        for entry in image_alts:
            if not isinstance(entry, dict):
                continue
            image_id = str(entry.get("image_id") or entry.get("imageId") or "")
            proposed_alt = str(
                entry.get("proposed_alt") or entry.get("proposedAlt") or entry.get("alt") or ""
            ).strip()
            if image_id and proposed_alt:
                alt_by_id[image_id] = proposed_alt

    proposed_media = _get_proposed(proposed, "media_images", "images")
    shopify_media = extract_shopify_media_alts(shopify_response)
    if alt_by_id or proposed_media is not None or shopify_media:
        product.media_images = merge_media_image_alts(
            product.media_images,
            alt_by_id=alt_by_id or None,
            proposed_media=proposed_media if isinstance(proposed_media, list) else None,
            shopify_media=shopify_media or None,
        )
    elif proposed_media is not None and not shopify_node:
        product.media_images = normalize_product_images(proposed_media)

    if store_id is not None:
        await _upsert_product_metafields_from_proposed(
            session,
            store_id,
            product_id,
            proposed,
            shopify_response,
        )

    product.raw_payload = _merge_raw_payload(
        product.raw_payload,
        {
            "title": product.title,
            "handle": product.handle,
            "seo": {"title": product.seo_title, "description": product.seo_description},
            "descriptionHtml": product.description_html,
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
    shopify_response: dict[str, Any] | None = None,
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

    title = _get_proposed(proposed, "collection_title", "proposed_collection_title")
    if title and not shopify_node:
        collection.title = title
    handle = _get_proposed(proposed, "handle", "proposed_handle")
    if handle and not shopify_node:
        collection.handle = handle
    seo_title = _get_proposed(proposed, "seo_title", "proposed_seo_title")
    if seo_title and not shopify_node:
        collection.seo_title = seo_title
    meta = _get_proposed(proposed, "meta_description", "proposed_meta_description")
    if meta and not shopify_node:
        collection.seo_description = meta
    desc_html = _get_proposed(
        proposed, "description_html", "proposed_description", "proposed_description_html"
    )
    if desc_html and not shopify_node:
        collection.description_html = desc_html
        collection.description_text = html_to_text(desc_html)

    image_alt = _get_proposed(proposed, "image_alt", "proposed_image_alt")
    if image_alt:
        collection.image_alt = image_alt
    elif shopify_response:
        alt_block = shopify_response.get("collectionImageAltUpdate") or {}
        collection_node = alt_block.get("collection") or {}
        image = collection_node.get("image") or {}
        alt_from_shopify = image.get("altText")
        if alt_from_shopify is not None:
            collection.image_alt = alt_from_shopify

    collection.raw_payload = _merge_raw_payload(
        collection.raw_payload,
        {
            "title": collection.title,
            "handle": collection.handle,
            "seo": {"title": collection.seo_title, "description": collection.seo_description},
            "descriptionHtml": collection.description_html,
            "image": {"altText": collection.image_alt},
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
    store_id: UUID | None = None,
) -> ShopifyProduct | ShopifyCollection | None:
    shopify_node: dict[str, Any] | None = None
    if shopify_response:
        if entity_type == "product":
            shopify_node = (shopify_response.get("productUpdate") or {}).get("product")
        elif entity_type == "collection":
            shopify_node = (shopify_response.get("collectionUpdate") or {}).get("collection")

    if entity_type == "product":
        return await apply_proposed_values_to_product(
            session,
            entity_id,
            proposed,
            shopify_node=shopify_node,
            shopify_response=shopify_response,
            store_id=store_id,
        )
    if entity_type == "collection":
        return await apply_proposed_values_to_collection(
            session,
            entity_id,
            proposed,
            shopify_node=shopify_node,
            shopify_response=shopify_response,
        )
    return None
