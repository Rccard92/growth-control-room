"""Applying a proposal must not silently overwrite a newer Shopify edit."""

import asyncio
from unittest.mock import AsyncMock

import pytest

from app.services.content.seo_apply_drift import (
    SeoApplyDriftError,
    assert_no_upstream_drift,
    detect_drift,
)
from app.services.shopify.client import ShopifyAPIError

SNAPSHOT = {
    "product_title": "Miele di Acacia 500g",
    "handle": "miele-di-acacia-500g",
    "seo_title": "Vecchio SEO title",
    "meta_description": "Vecchia meta",
    "description_html": "<p>Descrizione.</p>",
}
LIVE_UNCHANGED = {
    "title": "Miele di Acacia 500g",
    "handle": "miele-di-acacia-500g",
    "seo": {"title": "Vecchio SEO title", "description": "Vecchia meta"},
    "descriptionHtml": "<p>Descrizione.</p>",
}


def test_no_drift_when_live_matches_snapshot() -> None:
    assert (
        detect_drift(
            entity_type="product",
            snapshot=SNAPSHOT,
            live_node=LIVE_UNCHANGED,
            changed_fields={"seo_title", "meta_description"},
        )
        == []
    )


def test_drift_detected_when_merchant_edited_the_same_field() -> None:
    live = {**LIVE_UNCHANGED, "seo": {"title": "Modificato a mano", "description": "Vecchia meta"}}
    assert detect_drift(
        entity_type="product",
        snapshot=SNAPSHOT,
        live_node=live,
        changed_fields={"seo_title"},
    ) == ["seo_title"]


def test_edit_to_an_untouched_field_is_not_a_conflict() -> None:
    live = {**LIVE_UNCHANGED, "title": "Titolo cambiato a mano"}
    assert (
        detect_drift(
            entity_type="product",
            snapshot=SNAPSHOT,
            live_node=live,
            changed_fields={"seo_title"},
        )
        == []
    )


def test_whitespace_differences_are_not_a_conflict() -> None:
    live = {
        **LIVE_UNCHANGED,
        "seo": {"title": "  Vecchio SEO title ", "description": "Vecchia meta"},
    }
    assert (
        detect_drift(
            entity_type="product",
            snapshot=SNAPSHOT,
            live_node=live,
            changed_fields={"seo_title"},
        )
        == []
    )


def test_assert_raises_with_the_drifted_field_names() -> None:
    client = AsyncMock()
    client.fetch_product_by_gid = AsyncMock(
        return_value={**LIVE_UNCHANGED, "handle": "handle-cambiato"}
    )
    with pytest.raises(SeoApplyDriftError) as exc_info:
        asyncio.run(
            assert_no_upstream_drift(
                client,
                entity_type="product",
                entity_gid="gid://shopify/Product/1",
                snapshot=SNAPSHOT,
                changed_fields={"handle"},
            )
        )
    assert exc_info.value.fields == ["handle"]


def test_a_failed_read_does_not_block_the_apply() -> None:
    client = AsyncMock()
    client.fetch_product_by_gid = AsyncMock(side_effect=ShopifyAPIError("offline"))
    asyncio.run(
        assert_no_upstream_drift(
            client,
            entity_type="product",
            entity_gid="gid://shopify/Product/1",
            snapshot=SNAPSHOT,
            changed_fields={"seo_title"},
        )
    )


def test_image_only_changes_skip_the_remote_read() -> None:
    client = AsyncMock()
    asyncio.run(
        assert_no_upstream_drift(
            client,
            entity_type="product",
            entity_gid="gid://shopify/Product/1",
            snapshot=SNAPSHOT,
            changed_fields=set(),
        )
    )
    client.fetch_product_by_gid.assert_not_called()
