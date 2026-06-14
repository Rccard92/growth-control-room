"""Tests for generate-field image ALT validation."""

import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

import pytest

from app.services.content.seo_image_utils import resolve_product_image


def test_generate_field_image_alt_missing_image_id() -> None:
    with pytest.raises(ValueError, match="image_id richiesto"):
        resolve_product_image({"media_images": []}, None)


def test_generate_field_image_alt_invalid_synthetic_id() -> None:
    current = {
        "media_images": [{"id": "gid://shopify/MediaImage/1", "url": "https://x", "altText": ""}],
    }
    with pytest.raises(ValueError, match="Shopify"):
        resolve_product_image(current, "0")


def test_generate_field_image_alt_image_not_found() -> None:
    current = {
        "media_images": [{"id": "gid://shopify/MediaImage/1", "url": "https://x", "altText": ""}],
    }
    with pytest.raises(ValueError, match="non trovata"):
        resolve_product_image(current, "gid://shopify/MediaImage/999")


def test_generate_field_image_alt_valid_image() -> None:
    gid = "gid://shopify/MediaImage/42"
    current = {
        "media_images": [{"id": gid, "url": "https://x", "altText": ""}],
    }
    target = resolve_product_image(current, gid)
    assert target["id"] == gid
