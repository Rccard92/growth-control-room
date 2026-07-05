"""Tests for PageSpeed Insights client."""

from __future__ import annotations

import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

from app.services.google.exceptions import GoogleApiRequestError, GoogleIntegrationNotConfiguredError
from app.services.google.pagespeed_client import fetch_pagespeed_insights


def test_fetch_pagespeed_insights_builds_request_with_api_key(monkeypatch) -> None:
    async def run() -> None:
        monkeypatch.setattr(
            "app.services.google.pagespeed_client.settings.google_pagespeed_api_key",
            "test-pagespeed-key",
        )

        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {
            "lighthouseResult": {
                "categories": {"performance": {"score": 0.8}},
                "audits": {},
            }
        }

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "app.services.google.pagespeed_client.httpx.AsyncClient",
            return_value=mock_client,
        ):
            data = await fetch_pagespeed_insights("https://example.com/products/a")

        assert data["lighthouseResult"]["categories"]["performance"]["score"] == 0.8
        called_params = mock_client.get.call_args.kwargs["params"]
        assert ("key", "test-pagespeed-key") in called_params
        assert ("url", "https://example.com/products/a") in called_params
        assert ("strategy", "mobile") in called_params

    asyncio.run(run())


def test_fetch_pagespeed_insights_missing_api_key() -> None:
    async def run() -> None:
        with (
            patch(
                "app.services.google.pagespeed_client.settings.google_pagespeed_api_key",
                None,
            ),
            pytest.raises(GoogleIntegrationNotConfiguredError),
        ):
            await fetch_pagespeed_insights("https://example.com")

    asyncio.run(run())


def test_fetch_pagespeed_insights_http_error() -> None:
    async def run() -> None:
        response = MagicMock()
        response.status_code = 500

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with (
            patch(
                "app.services.google.pagespeed_client.settings.google_pagespeed_api_key",
                "test-key",
            ),
            patch(
                "app.services.google.pagespeed_client.httpx.AsyncClient",
                return_value=mock_client,
            ),
            pytest.raises(GoogleApiRequestError),
        ):
            await fetch_pagespeed_insights("https://example.com")

    asyncio.run(run())
