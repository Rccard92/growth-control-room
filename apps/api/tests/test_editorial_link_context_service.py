"""Tests for editorial link context service."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.services.content.editorial_link_context_service import (
    build_editorial_link_context,
    format_editorial_link_context_for_prompt,
    split_link_targets_by_type,
    EditorialLinkTarget,
)


def test_format_editorial_link_context_empty() -> None:
    text = format_editorial_link_context_for_prompt([])
    assert "LINK INTERNI VERIFICATI: []" in text


def test_format_editorial_link_context_with_targets() -> None:
    targets = [
        EditorialLinkTarget(
            entity_type="product",
            title="Miele millefiori",
            handle="miele-millefiori",
            path="/products/miele-millefiori",
        )
    ]
    text = format_editorial_link_context_for_prompt(targets)
    assert "miele-millefiori" in text
    assert "/products/miele-millefiori" in text


def test_split_link_targets_by_type() -> None:
    targets = [
        EditorialLinkTarget("product", "Miele", "miele", "/products/miele"),
        EditorialLinkTarget("collection", "Mieli bio", "mieli-bio", "/collections/mieli-bio"),
    ]
    products, collections = split_link_targets_by_type(targets)
    assert products == ["Miele"]
    assert collections == ["Mieli bio"]


def test_build_editorial_link_context_from_item_handle() -> None:
    project_id = uuid4()
    item = SimpleNamespace(
        linked_shopify_product_id=None,
        linked_shopify_product_handle="miele-classico",
        linked_shopify_product_title="Miele classico",
        primary_keyword=None,
        brief_payload=None,
    )
    mock_session = AsyncMock()
    store = SimpleNamespace(id=uuid4())

    async def run() -> None:
        with patch(
            "app.services.content.editorial_link_context_service.get_shopify_store_for_project",
            new=AsyncMock(return_value=store),
        ):
            targets = await build_editorial_link_context(mock_session, project_id, item)
        assert len(targets) == 1
        assert targets[0].path == "/products/miele-classico"

    asyncio.run(run())
