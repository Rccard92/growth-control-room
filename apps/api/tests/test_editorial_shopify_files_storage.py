"""Tests for Shopify Files editorial image upload orchestrator."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.content.editorial_shopify_files_storage import (
    extract_shopify_cdn_url,
    upload_editorial_image_to_shopify_files,
)
from app.services.shopify.client import ShopifyAPIError


def test_extract_shopify_cdn_url_prefers_image_url() -> None:
    node = {
        "image": {"url": "https://cdn.shopify.com/s/files/1/hero.jpg"},
        "preview": {"image": {"url": "https://cdn.shopify.com/s/files/1/preview.jpg"}},
    }
    assert extract_shopify_cdn_url(node) == "https://cdn.shopify.com/s/files/1/hero.jpg"


def test_extract_shopify_cdn_url_falls_back_to_preview() -> None:
    node = {"preview": {"image": {"url": "https://cdn.shopify.com/s/files/1/preview.jpg"}}}
    assert extract_shopify_cdn_url(node) == "https://cdn.shopify.com/s/files/1/preview.jpg"


def test_upload_editorial_image_to_shopify_files_happy_path() -> None:
    async def _run() -> None:
        client = MagicMock()
        client.create_staged_upload_for_image = AsyncMock(
            return_value={
                "url": "https://upload.shopify.com/staged",
                "resourceUrl": "https://shopify.com/staged/resource",
                "parameters": [{"name": "key", "value": "uploads/hero.jpg"}],
            }
        )
        client.upload_to_staged_target = AsyncMock(return_value=None)
        client.file_create_from_staged_upload = AsyncMock(
            return_value={"id": "gid://shopify/MediaImage/123", "fileStatus": "PROCESSING"}
        )
        client.wait_until_file_ready = AsyncMock(
            return_value={
                "id": "gid://shopify/MediaImage/123",
                "fileStatus": "READY",
                "image": {
                    "url": "https://cdn.shopify.com/s/files/1/hero.jpg",
                    "width": 1600,
                    "height": 900,
                },
            }
        )

        result = await upload_editorial_image_to_shopify_files(
            client,
            filename="guida-al-miele.jpg",
            alt_text="Guida al miele",
            image_bytes=b"jpeg-bytes",
            mime_type="image/jpeg",
        )

        client.create_staged_upload_for_image.assert_awaited_once_with(
            filename="guida-al-miele.jpg",
            mime_type="image/jpeg",
            file_size=10,
        )
        client.upload_to_staged_target.assert_awaited_once()
        client.file_create_from_staged_upload.assert_awaited_once_with(
            "https://shopify.com/staged/resource",
            "Guida al miele",
        )
        assert result.media_gid == "gid://shopify/MediaImage/123"
        assert result.cdn_url == "https://cdn.shopify.com/s/files/1/hero.jpg"
        assert result.file_status == "READY"

    asyncio.run(_run())


def test_upload_editorial_image_raises_when_cdn_missing() -> None:
    async def _run() -> None:
        client = MagicMock()
        client.create_staged_upload_for_image = AsyncMock(
            return_value={
                "url": "https://upload.shopify.com/staged",
                "resourceUrl": "https://shopify.com/staged/resource",
                "parameters": [],
            }
        )
        client.upload_to_staged_target = AsyncMock(return_value=None)
        client.file_create_from_staged_upload = AsyncMock(
            return_value={"id": "gid://shopify/MediaImage/123", "fileStatus": "PROCESSING"}
        )
        client.wait_until_file_ready = AsyncMock(return_value={"fileStatus": "READY"})

        with pytest.raises(ShopifyAPIError, match="URL CDN"):
            await upload_editorial_image_to_shopify_files(
                client,
                filename="hero.jpg",
                alt_text="Hero",
                image_bytes=b"x",
            )

    asyncio.run(_run())
