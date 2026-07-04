"""Tests for Growth Audit Shopify entity resolver."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.models.growth_audit import GrowthAuditPage
from app.services.growth_audit.shopify_entity_resolver import (
    apply_shopify_entity_mapping_to_page,
    extract_shopify_handle_from_path,
    resolve_shopify_entity_for_page,
)


def test_extract_shopify_handle_from_path_product() -> None:
    result = extract_shopify_handle_from_path("/products/polline-biologico", "product")
    assert result == {
        "entityType": "shopify_product",
        "handle": "polline-biologico",
    }


def test_extract_shopify_handle_from_path_collection() -> None:
    result = extract_shopify_handle_from_path("/collections/miele/", "collection")
    assert result == {
        "entityType": "shopify_collection",
        "handle": "miele",
    }


def test_extract_shopify_handle_from_path_page() -> None:
    result = extract_shopify_handle_from_path("/pages/chi-siamo", "static_page")
    assert result == {
        "entityType": "shopify_page",
        "handle": "chi-siamo",
    }


def test_extract_shopify_handle_from_path_article() -> None:
    result = extract_shopify_handle_from_path("/blogs/news/benefici-polline", "blog_article")
    assert result == {
        "entityType": "shopify_article",
        "handle": "benefici-polline",
        "blogHandle": "news",
    }


def test_extract_shopify_handle_from_path_cart_returns_none() -> None:
    assert extract_shopify_handle_from_path("/cart", "other") is None


def test_apply_shopify_entity_mapping_preserves_existing_on_none() -> None:
    page = GrowthAuditPage(
        run_id=uuid4(),
        project_id=uuid4(),
        url="https://example.com/products/a",
        normalized_url="https://example.com/products/a",
        source_entity_type="shopify_product",
        source_entity_id=uuid4(),
        source_entity_handle="a",
    )

    apply_shopify_entity_mapping_to_page(page, None)

    assert page.source_entity_type == "shopify_product"
    assert page.source_entity_handle == "a"


def test_apply_shopify_entity_mapping_updates_fields() -> None:
    entity_id = uuid4()
    synced_at = datetime(2026, 6, 1, tzinfo=UTC)
    page = GrowthAuditPage(
        run_id=uuid4(),
        project_id=uuid4(),
        url="https://example.com/products/a",
        normalized_url="https://example.com/products/a",
    )
    resolved = {
        "sourceEntityType": "shopify_product",
        "sourceEntityId": entity_id,
        "sourceEntityGid": "gid://shopify/Product/1",
        "sourceEntityHandle": "a",
        "sourceEntityTitle": "Product A",
        "sourceEntitySyncedAt": synced_at,
        "metadata": {
            "shopify": {
                "storeId": str(uuid4()),
                "entityType": "product",
                "entityId": str(entity_id),
                "gid": "gid://shopify/Product/1",
                "handle": "a",
                "title": "Product A",
            }
        },
    }

    apply_shopify_entity_mapping_to_page(page, resolved)

    assert page.source_entity_type == "shopify_product"
    assert page.source_entity_id == entity_id
    assert page.source_entity_gid == "gid://shopify/Product/1"
    assert page.source_entity_handle == "a"
    assert page.source_entity_title == "Product A"
    assert page.source_entity_synced_at == synced_at
    assert page.page_metadata["shopify"]["handle"] == "a"


@pytest.mark.parametrize(
    ("entity_type", "path", "model_path", "entity_attrs"),
    [
        (
            "shopify_product",
            "/products/honey-jar",
            "app.services.growth_audit.shopify_entity_resolver.ShopifyProduct",
            {"handle": "honey-jar", "title": "Honey", "shopify_gid": "gid://shopify/Product/1"},
        ),
        (
            "shopify_collection",
            "/collections/summer",
            "app.services.growth_audit.shopify_entity_resolver.ShopifyCollection",
            {"handle": "summer", "title": "Summer", "shopify_gid": "gid://shopify/Collection/1"},
        ),
        (
            "shopify_page",
            "/pages/about",
            "app.services.growth_audit.shopify_entity_resolver.ShopifyPage",
            {"handle": "about", "title": "About", "shopify_gid": "gid://shopify/Page/1"},
        ),
    ],
)
def test_resolve_shopify_entity_for_page_finds_entity(
    entity_type: str,
    path: str,
    model_path: str,
    entity_attrs: dict,
) -> None:
    async def run() -> None:
        project_id = uuid4()
        store_id = uuid4()
        entity_id = uuid4()

        page = GrowthAuditPage(
            run_id=uuid4(),
            project_id=project_id,
            url=f"https://example.com{path}",
            normalized_url=f"https://example.com{path}",
            path=path,
            page_type="product",
        )

        entity = MagicMock()
        entity.id = entity_id
        entity.updated_at = datetime(2026, 6, 1, tzinfo=UTC)
        for key, value in entity_attrs.items():
            setattr(entity, key, value)
        if entity_type == "shopify_product":
            entity.updated_at_shopify = None

        session = AsyncMock()
        session.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=entity))
        )

        store = MagicMock()
        store.id = store_id

        with patch(
            "app.services.growth_audit.shopify_entity_resolver.get_shopify_store_for_project",
            new=AsyncMock(return_value=store),
        ):
            resolved = await resolve_shopify_entity_for_page(session, page)

        assert resolved is not None
        assert resolved["sourceEntityType"] == entity_type
        assert resolved["sourceEntityId"] == entity_id
        assert resolved["sourceEntityHandle"] == entity_attrs["handle"]

    asyncio.run(run())


def test_resolve_shopify_entity_for_page_returns_none_when_not_found() -> None:
    async def run() -> None:
        page = GrowthAuditPage(
            run_id=uuid4(),
            project_id=uuid4(),
            url="https://example.com/products/missing",
            normalized_url="https://example.com/products/missing",
            path="/products/missing",
            page_type="product",
        )

        session = AsyncMock()
        session.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))
        )
        store = MagicMock()
        store.id = uuid4()

        with patch(
            "app.services.growth_audit.shopify_entity_resolver.get_shopify_store_for_project",
            new=AsyncMock(return_value=store),
        ):
            resolved = await resolve_shopify_entity_for_page(session, page)

        assert resolved is None

    asyncio.run(run())
