"""Sync a single product or collection from Shopify and re-run SEO analysis."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_seo import ShopifyCollection
from app.models.shopify import ShopifyProduct, ShopifyStore
from app.services.content.seo_entity_analyze_single import (
    analyze_single_collection,
    analyze_single_product,
)
from app.services.content.seo_entity_detail_service import (
    get_collection_seo_detail,
    get_product_seo_detail,
)
from app.services.shopify.client import ShopifyAPIError, ShopifyGraphQLClient
from app.services.shopify.content_sync import _upsert_collection
from app.services.shopify.metafield_definitions_sync import sync_metafield_definitions
from app.services.shopify.sync import _upsert_product, _upsert_variants


async def sync_single_product(
    store: ShopifyStore,
    client: ShopifyGraphQLClient,
    session: AsyncSession,
    product_id: UUID,
) -> dict[str, Any]:
    product = (
        await session.execute(
            select(ShopifyProduct).where(
                ShopifyProduct.id == product_id,
                ShopifyProduct.shopify_store_id == store.id,
            )
        )
    ).scalar_one_or_none()
    if product is None:
        raise ShopifyAPIError("Prodotto non trovato nel progetto", status_code=404)
    if not product.shopify_gid:
        raise ShopifyAPIError(
            "Prodotto senza shopify_gid: impossibile sincronizzare da Shopify",
            status_code=400,
        )

    node = await client.fetch_product_by_gid(product.shopify_gid)
    product = await _upsert_product(session, store.id, node)
    await _upsert_variants(session, store.id, product, node)
    try:
        await sync_metafield_definitions(store, client, session)
    except Exception:
        pass
    await analyze_single_product(store, session, product_id)
    await session.commit()

    detail = await get_product_seo_detail(store, session, product_id)
    if detail is None:
        raise ShopifyAPIError("Dettaglio prodotto non disponibile dopo sync", status_code=500)

    return {
        "entity_type": "product",
        "entity_id": str(product_id),
        "detail": detail,
        "message": "Prodotto sincronizzato da Shopify.",
    }


async def sync_single_collection(
    store: ShopifyStore,
    client: ShopifyGraphQLClient,
    session: AsyncSession,
    collection_id: UUID,
) -> dict[str, Any]:
    collection = (
        await session.execute(
            select(ShopifyCollection).where(
                ShopifyCollection.id == collection_id,
                ShopifyCollection.shopify_store_id == store.id,
            )
        )
    ).scalar_one_or_none()
    if collection is None:
        raise ShopifyAPIError("Collezione non trovata nel progetto", status_code=404)
    if not collection.shopify_gid:
        raise ShopifyAPIError(
            "Collezione senza shopify_gid: impossibile sincronizzare da Shopify",
            status_code=400,
        )

    node = await client.fetch_collection_by_gid(collection.shopify_gid)
    await _upsert_collection(session, store.id, node)
    await analyze_single_collection(store, session, collection_id)
    await session.commit()

    detail = await get_collection_seo_detail(store, session, collection_id)
    if detail is None:
        raise ShopifyAPIError("Dettaglio collezione non disponibile dopo sync", status_code=500)

    return {
        "entity_type": "collection",
        "entity_id": str(collection_id),
        "detail": detail,
        "message": "Collezione sincronizzata da Shopify.",
    }
