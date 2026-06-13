"""Product Knowledge from Shopify unit tests."""

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.services.brand_intelligence.product_knowledge_item_service import create_item_from_shopify

_PID = uuid4()
_SHOPIFY_PRODUCT_ID = uuid4()
_STORE_ID = uuid4()


def _shopify_product() -> SimpleNamespace:
    return SimpleNamespace(
        id=_SHOPIFY_PRODUCT_ID,
        shopify_gid="gid://shopify/Product/123",
        handle="miele-limone",
        title="Miele di Limone",
        product_type="Miele",
        shopify_store_id=_STORE_ID,
    )


def test_create_from_shopify_no_store_raises() -> None:
    async def run() -> None:
        mock_session = AsyncMock()
        with (
            patch(
                "app.services.brand_intelligence.product_knowledge_item_service.get_shopify_store_for_project",
                new=AsyncMock(return_value=None),
            ),
            pytest.raises(HTTPException) as exc,
        ):
            await create_item_from_shopify(mock_session, _PID, _SHOPIFY_PRODUCT_ID)
        assert exc.value.status_code == 404

    asyncio.run(run())


def test_create_from_shopify_prefills_and_idempotent() -> None:
    existing = SimpleNamespace(
        id=uuid4(),
        project_id=_PID,
        shopify_product_id=_SHOPIFY_PRODUCT_ID,
        product_name="Miele di Limone",
    )
    product = _shopify_product()
    store = SimpleNamespace(id=_STORE_ID)

    async def run() -> None:
        mock_session = AsyncMock()
        execute_results = [
            SimpleNamespace(scalar_one_or_none=lambda s=store: s),
            SimpleNamespace(scalar_one_or_none=lambda p=product: p),
            SimpleNamespace(scalar_one_or_none=lambda e=existing: e),
        ]
        mock_session.execute = AsyncMock(side_effect=execute_results)

        result = await create_item_from_shopify(mock_session, _PID, _SHOPIFY_PRODUCT_ID)
        assert result is existing

    asyncio.run(run())


def test_create_from_shopify_creates_new_row() -> None:
    product = _shopify_product()
    store = SimpleNamespace(id=_STORE_ID)
    added: list[SimpleNamespace] = []

    async def run() -> None:
        mock_session = AsyncMock()

        def scalar_none():
            return None

        mock_session.execute = AsyncMock(
            side_effect=[
                SimpleNamespace(scalar_one_or_none=lambda: product),
                SimpleNamespace(scalar_one_or_none=scalar_none),
            ]
        )

        def capture_add(row: SimpleNamespace) -> None:
            added.append(row)

        mock_session.add = capture_add
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        with patch(
            "app.services.brand_intelligence.product_knowledge_item_service.get_shopify_store_for_project",
            new=AsyncMock(return_value=store),
        ):
            await create_item_from_shopify(mock_session, _PID, _SHOPIFY_PRODUCT_ID)
        assert len(added) == 1
        row = added[0]
        assert row.product_name == "Miele di Limone"
        assert row.shopify_handle == "miele-limone"
        assert row.product_line == "Miele"
        assert row.source_type == "shopify"

    asyncio.run(run())
