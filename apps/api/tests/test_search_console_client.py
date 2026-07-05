"""Tests for Search Console API client."""

from __future__ import annotations

import os
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import quote

import httpx
import pytest

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

from app.services.google.exceptions import (
    GoogleApiRequestError,
    GoogleIntegrationPermissionError,
    GoogleSearchConsolePropertyError,
)
from app.services.google.search_console_client import (
    fetch_search_console_search_analytics,
    fetch_search_console_sites,
)


def test_fetch_search_console_sites_returns_site_entries() -> None:
    async def run() -> None:
        response = MagicMock()
        response.status_code = 200
        response.json = MagicMock(
            return_value={
                "siteEntry": [
                    {"siteUrl": "https://example.com/", "permissionLevel": "siteOwner"},
                ]
            }
        )

        with patch("httpx.AsyncClient") as client_cls:
            client = AsyncMock()
            client.__aenter__.return_value = client
            client.get = AsyncMock(return_value=response)
            client_cls.return_value = client

            sites = await fetch_search_console_sites("access-token")

        assert sites == [
            {"siteUrl": "https://example.com/", "permissionLevel": "siteOwner"},
        ]
        client.get.assert_awaited_once()

    import asyncio

    asyncio.run(run())


def test_fetch_search_console_search_analytics_builds_encoded_endpoint() -> None:
    async def run() -> None:
        site_url = "https://example.com/"
        encoded = quote(site_url, safe="")
        response = MagicMock()
        response.status_code = 200
        response.json = MagicMock(return_value={"rows": []})

        with patch("httpx.AsyncClient") as client_cls:
            client = AsyncMock()
            client.__aenter__.return_value = client
            client.post = AsyncMock(return_value=response)
            client_cls.return_value = client

            payload = await fetch_search_console_search_analytics(
                "access-token",
                site_url=site_url,
                start_date=date(2026, 5, 1),
                end_date=date(2026, 5, 28),
                dimensions=["page"],
            )

        assert payload == {"rows": []}
        called_url = client.post.await_args.args[0]
        assert encoded in called_url
        assert called_url.endswith("/searchAnalytics/query")

    import asyncio

    asyncio.run(run())


def test_fetch_search_console_sites_maps_permission_error() -> None:
    async def run() -> None:
        response = MagicMock()
        response.status_code = 403

        with patch("httpx.AsyncClient") as client_cls:
            client = AsyncMock()
            client.__aenter__.return_value = client
            client.get = AsyncMock(return_value=response)
            client_cls.return_value = client

            with pytest.raises(GoogleIntegrationPermissionError):
                await fetch_search_console_sites("access-token")

    import asyncio

    asyncio.run(run())


def test_fetch_search_console_search_analytics_maps_property_error() -> None:
    async def run() -> None:
        response = MagicMock()
        response.status_code = 404

        with patch("httpx.AsyncClient") as client_cls:
            client = AsyncMock()
            client.__aenter__.return_value = client
            client.post = AsyncMock(return_value=response)
            client_cls.return_value = client

            with pytest.raises(GoogleSearchConsolePropertyError):
                await fetch_search_console_search_analytics(
                    "access-token",
                    site_url="https://missing.example/",
                    start_date=date(2026, 5, 1),
                    end_date=date(2026, 5, 28),
                    dimensions=["page"],
                )

    import asyncio

    asyncio.run(run())


def test_fetch_search_console_sites_maps_network_error() -> None:
    async def run() -> None:
        with patch("httpx.AsyncClient") as client_cls:
            client = AsyncMock()
            client.__aenter__.return_value = client
            client.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
            client_cls.return_value = client

            with pytest.raises(GoogleApiRequestError):
                await fetch_search_console_sites("access-token")

    import asyncio

    asyncio.run(run())
