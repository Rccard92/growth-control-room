"""Tests for Chrome UX Report client."""

from __future__ import annotations

import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

from app.services.google.crux_client import fetch_crux_record


def test_fetch_crux_record_returns_none_when_no_data() -> None:
    async def run() -> None:
        response = MagicMock()
        response.status_code = 404

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with (
            patch(
                "app.services.google.crux_client.settings.google_crux_api_key",
                "test-crux-key",
            ),
            patch(
                "app.services.google.crux_client.httpx.AsyncClient",
                return_value=mock_client,
            ),
        ):
            result = await fetch_crux_record("https://example.com/products/a")

        assert result is None
        assert mock_client.post.call_count == 2

    asyncio.run(run())


def test_fetch_crux_record_returns_url_level_data() -> None:
    async def run() -> None:
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {
            "record": {
                "key": {"formFactor": "PHONE"},
                "metrics": {
                    "largest_contentful_paint": {"percentiles": {"p75": 2400}},
                },
            }
        }

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with (
            patch(
                "app.services.google.crux_client.settings.google_crux_api_key",
                "test-crux-key",
            ),
            patch(
                "app.services.google.crux_client.httpx.AsyncClient",
                return_value=mock_client,
            ),
        ):
            result = await fetch_crux_record("https://example.com/products/a")

        assert result is not None
        assert result["_cruxSource"] == "url"

    asyncio.run(run())
