"""Tests for Google Analytics 4 API client."""

from __future__ import annotations

import os
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

from app.services.google.analytics_client import (
    fetch_ga4_account_summaries,
    fetch_ga4_landing_pages_report,
)
from app.services.google.exceptions import (
    GoogleAnalyticsPropertyError,
    GoogleIntegrationPermissionError,
)


def test_fetch_ga4_account_summaries_normalizes_properties() -> None:
    async def run() -> None:
        response = MagicMock()
        response.status_code = 200
        response.json = MagicMock(
            return_value={
                "accountSummaries": [
                    {
                        "account": "accounts/100",
                        "displayName": "Example Account",
                        "propertySummaries": [
                            {
                                "property": "properties/123456789",
                                "displayName": "Example GA4",
                            }
                        ],
                    }
                ]
            }
        )

        with patch("httpx.AsyncClient") as client_cls:
            client = AsyncMock()
            client.__aenter__.return_value = client
            client.get = AsyncMock(return_value=response)
            client_cls.return_value = client

            properties = await fetch_ga4_account_summaries("access-token")

        assert properties == [
            {
                "account": "accounts/100",
                "accountDisplayName": "Example Account",
                "property": "properties/123456789",
                "propertyId": "123456789",
                "propertyDisplayName": "Example GA4",
            }
        ]

    import asyncio

    asyncio.run(run())


def test_fetch_ga4_landing_pages_report_returns_extended_metrics() -> None:
    async def run() -> None:
        response = MagicMock()
        response.status_code = 200
        response.json = MagicMock(
            return_value={
                "rows": [
                    {
                        "dimensionValues": [{"value": "/products/a"}],
                        "metricValues": [
                            {"value": "120"},
                            {"value": "90"},
                            {"value": "80"},
                            {"value": "0.42"},
                            {"value": "95.5"},
                            {"value": "3"},
                            {"value": "150.25"},
                            {"value": "2"},
                        ],
                    }
                ]
            }
        )

        with patch("httpx.AsyncClient") as client_cls:
            client = AsyncMock()
            client.__aenter__.return_value = client
            client.post = AsyncMock(return_value=response)
            client_cls.return_value = client

            payload = await fetch_ga4_landing_pages_report(
                "access-token",
                property_id="123456789",
                start_date=date(2026, 5, 1),
                end_date=date(2026, 5, 28),
            )

        assert payload["propertyId"] == "123456789"
        assert "conversions" in payload["metricsUsed"]
        assert payload["rows"][0]["landingPagePlusQueryString"] == "/products/a"
        assert payload["rows"][0]["sessions"] == 120
        assert payload["rows"][0]["conversions"] == 3

    import asyncio

    asyncio.run(run())


def test_fetch_ga4_landing_pages_report_falls_back_on_metric_incompatible() -> None:
    async def run() -> None:
        incompatible_response = MagicMock()
        incompatible_response.status_code = 400
        incompatible_response.json = MagicMock(
            return_value={"error": {"message": "Metric conversions is incompatible"}}
        )

        primary_response = MagicMock()
        primary_response.status_code = 200
        primary_response.json = MagicMock(
            return_value={
                "rows": [
                    {
                        "dimensionValues": [{"value": "/"}],
                        "metricValues": [
                            {"value": "50"},
                            {"value": "40"},
                            {"value": "30"},
                            {"value": "0.5"},
                            {"value": "60"},
                        ],
                    }
                ]
            }
        )

        with patch("httpx.AsyncClient") as client_cls:
            client = AsyncMock()
            client.__aenter__.return_value = client
            client.post = AsyncMock(side_effect=[incompatible_response, primary_response])
            client_cls.return_value = client

            payload = await fetch_ga4_landing_pages_report(
                "access-token",
                property_id="properties/999",
                start_date=date(2026, 5, 1),
                end_date=date(2026, 5, 28),
            )

        assert payload["propertyId"] == "999"
        assert payload["metricsUsed"] == [
            "sessions",
            "totalUsers",
            "engagedSessions",
            "engagementRate",
            "averageSessionDuration",
        ]
        assert payload["rows"][0]["sessions"] == 50
        assert client.post.await_count == 2

    import asyncio

    asyncio.run(run())


def test_fetch_ga4_account_summaries_maps_permission_error() -> None:
    async def run() -> None:
        response = MagicMock()
        response.status_code = 403

        with patch("httpx.AsyncClient") as client_cls:
            client = AsyncMock()
            client.__aenter__.return_value = client
            client.get = AsyncMock(return_value=response)
            client_cls.return_value = client

            with pytest.raises(GoogleIntegrationPermissionError):
                await fetch_ga4_account_summaries("access-token")

    import asyncio

    asyncio.run(run())


def test_fetch_ga4_landing_pages_report_maps_property_error() -> None:
    async def run() -> None:
        response = MagicMock()
        response.status_code = 404
        response.json = MagicMock(return_value={"error": {"message": "not found"}})

        with patch("httpx.AsyncClient") as client_cls:
            client = AsyncMock()
            client.__aenter__.return_value = client
            client.post = AsyncMock(return_value=response)
            client_cls.return_value = client

            with pytest.raises(GoogleAnalyticsPropertyError):
                await fetch_ga4_landing_pages_report(
                    "access-token",
                    property_id="missing",
                    start_date=date(2026, 5, 1),
                    end_date=date(2026, 5, 28),
                )

    import asyncio

    asyncio.run(run())
