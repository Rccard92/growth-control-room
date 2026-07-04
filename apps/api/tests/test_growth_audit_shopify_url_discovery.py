"""Tests for Growth Audit Shopify URL discovery."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.services.growth_audit.shopify_url_discovery import discover_shopify_urls


def _store(store_id):
    store = MagicMock()
    store.id = store_id
    return store


def test_discover_shopify_urls_builds_product_and_collection_urls() -> None:
    async def run() -> None:
        project_id = uuid4()
        store_id = uuid4()
        session = AsyncMock()

        product = MagicMock()
        product.handle = "honey-jar"
        product.title = "Honey Jar"
        product.shopify_gid = "gid://shopify/Product/1"

        collection = MagicMock()
        collection.handle = "summer"
        collection.title = "Summer"
        collection.shopify_gid = "gid://shopify/Collection/1"

        query_results = [
            [product],
            [collection],
            [],
            [],
            [],
        ]

        async def fake_execute(_stmt):
            result = MagicMock()
            result.scalars.return_value.all.return_value = query_results.pop(0)
            return result

        session.execute = AsyncMock(side_effect=fake_execute)

        with patch(
            "app.services.growth_audit.shopify_url_discovery.get_shopify_store_for_project",
            new=AsyncMock(return_value=_store(store_id)),
        ):
            items, events = await discover_shopify_urls(
                session,
                project_id,
                "https://example.com",
                max_urls=10,
            )

        assert len(items) == 2
        assert items[0]["url"] == "https://example.com/products/honey-jar"
        assert items[1]["url"] == "https://example.com/collections/summer"
        assert any(event["type"] == "shopify_urls_found" for event in events)

    asyncio.run(run())


def test_discover_shopify_urls_skips_records_without_handle() -> None:
    async def run() -> None:
        project_id = uuid4()
        store_id = uuid4()
        session = AsyncMock()

        product = MagicMock()
        product.handle = None
        product.title = "No Handle"
        product.shopify_gid = "gid://shopify/Product/2"

        query_results = [
            [product],
            [],
            [],
            [],
            [],
        ]

        async def fake_execute(_stmt):
            result = MagicMock()
            result.scalars.return_value.all.return_value = query_results.pop(0)
            return result

        session.execute = AsyncMock(side_effect=fake_execute)

        with patch(
            "app.services.growth_audit.shopify_url_discovery.get_shopify_store_for_project",
            new=AsyncMock(return_value=_store(store_id)),
        ):
            items, events = await discover_shopify_urls(
                session,
                project_id,
                "https://example.com",
                max_urls=10,
            )

        assert items == []
        assert any(event["type"] == "shopify_urls_missing" for event in events)

    asyncio.run(run())


def test_discover_shopify_urls_without_store() -> None:
    async def run() -> None:
        session = AsyncMock()
        with patch(
            "app.services.growth_audit.shopify_url_discovery.get_shopify_store_for_project",
            new=AsyncMock(return_value=None),
        ):
            items, events = await discover_shopify_urls(
                session,
                uuid4(),
                "https://example.com",
            )

        assert items == []
        assert events[0]["type"] == "shopify_urls_missing"

    asyncio.run(run())
