"""A handle change must always create the Shopify 301 from the old URL."""

from app.services.content.seo_apply_shopify import (
    build_collection_update_input,
    build_product_update_input,
)


def test_product_handle_change_requests_redirect() -> None:
    result = build_product_update_input("gid://shopify/Product/1", {"handle": "nuovo-handle"})
    assert result == {
        "id": "gid://shopify/Product/1",
        "handle": "nuovo-handle",
        "redirectNewHandle": True,
    }


def test_collection_handle_change_requests_redirect() -> None:
    result = build_collection_update_input(
        "gid://shopify/Collection/1", {"proposed_handle": "nuovo-handle"}
    )
    assert result["handle"] == "nuovo-handle"
    assert result["redirectNewHandle"] is True


def test_redirect_flag_absent_when_handle_unchanged() -> None:
    for build, gid in (
        (build_product_update_input, "gid://shopify/Product/1"),
        (build_collection_update_input, "gid://shopify/Collection/1"),
    ):
        result = build(gid, {"seo_title": "Titolo", "meta_description": "Meta"})
        assert result is not None
        assert "redirectNewHandle" not in result
