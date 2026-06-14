"""Unit tests for SEO image ALT utilities."""

from app.services.content.seo_image_utils import (
    image_applicability,
    merge_media_image_alts,
    normalize_product_images,
    resolve_product_image,
)


def test_resolve_product_image_requires_gid() -> None:
    current = {
        "media_images": [{"id": "gid://shopify/MediaImage/1", "url": "https://x", "altText": ""}],
    }
    try:
        resolve_product_image(current, "0")
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "Shopify" in str(exc)


def test_resolve_product_image_found() -> None:
    gid = "gid://shopify/MediaImage/99"
    current = {
        "media_images": [{"id": gid, "url": "https://x", "altText": "old"}],
    }
    target = resolve_product_image(current, gid)
    assert target["id"] == gid


def test_merge_media_image_alts_keeps_all_images() -> None:
    existing = [
        {"id": "gid://shopify/MediaImage/1", "altText": "a", "url": "u1"},
        {"id": "gid://shopify/MediaImage/2", "altText": "b", "url": "u2"},
    ]
    merged = merge_media_image_alts(
        existing,
        alt_by_id={"gid://shopify/MediaImage/1": "new a"},
    )
    assert len(merged) == 2
    assert merged[0]["altText"] == "new a"
    assert merged[1]["altText"] == "b"


def test_normalize_product_images_marks_missing_gid() -> None:
    rows = normalize_product_images([{"url": "https://img", "altText": None}])
    assert rows[0]["shopifyApplicable"] is False
    assert rows[0]["applicabilityReason"] == "missing_shopify_id"


def test_image_applicability_valid_gid() -> None:
    ok, reason = image_applicability(
        {"id": "gid://shopify/MediaImage/1", "url": "https://x"},
    )
    assert ok is True
    assert reason is None
