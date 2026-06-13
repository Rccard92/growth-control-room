"""Tests for non-silent Shopify collections sync."""

import asyncio
import os
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

from app.services.shopify.client import ShopifyAPIError
from app.services.shopify.content_sync import (
    ContentSyncResult,
    _sync_collection_nodes,
    get_last_collection_sync_errors,
)


def test_sync_collection_nodes_records_error_on_api_failure() -> None:
    store_id = uuid4()
    store = MagicMock()
    store.id = store_id
    store.shop_domain = "test.myshopify.com"

    client = MagicMock()
    client.fetch_all_collections = AsyncMock(
        side_effect=ShopifyAPIError(
            "Field must have selections (field 'productsCount' returns Count but has no selections)"
        )
    )

    session = MagicMock()
    result = ContentSyncResult()

    asyncio.run(_sync_collection_nodes(session, store, client, result))

    assert result.collections_synced == 0
    assert len(result.errors) == 1
    assert result.errors[0].startswith("Collections sync failed:")
    assert len(result.warnings) == 1
    assert get_last_collection_sync_errors(store_id) == result.errors


def test_sync_collection_nodes_increments_on_success() -> None:
    store_id = uuid4()
    store = MagicMock()
    store.id = store_id
    store.shop_domain = "test.myshopify.com"

    client = MagicMock()
    client.fetch_all_collections = AsyncMock(
        return_value=[
            {"id": "gid://shopify/Collection/1", "title": "A"},
            {"id": "gid://shopify/Collection/2", "title": "B"},
        ]
    )

    session = MagicMock()

    async def fake_upsert(_session, _store_id, _node):
        return MagicMock()

    from app.services.shopify import content_sync

    original_upsert = content_sync._upsert_collection
    content_sync._upsert_collection = fake_upsert
    try:
        result = ContentSyncResult()
        asyncio.run(_sync_collection_nodes(session, store, client, result))
        assert result.collections_synced == 2
        assert result.errors == []
        assert get_last_collection_sync_errors(store_id) == []
    finally:
        content_sync._upsert_collection = original_upsert
