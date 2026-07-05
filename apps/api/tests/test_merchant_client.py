"""Tests for Google Merchant Center client."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.google.exceptions import (
    GoogleIntegrationPermissionError,
    MerchantAccountError,
)
from app.services.google.merchant_client import (
    fetch_merchant_accounts,
    fetch_merchant_products_with_issues,
)


def test_fetch_merchant_accounts_normalizes_primary_accounts() -> None:
    async def run() -> None:
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {
            "accounts": [
                {
                    "name": "accounts/123456",
                    "accountName": "Example Merchant",
                    "accountType": "STANDARD",
                }
            ]
        }

        with patch(
            "app.services.google.merchant_client.httpx.AsyncClient",
        ) as client_cls:
            client = AsyncMock()
            client.__aenter__.return_value = client
            client.__aexit__.return_value = None
            client.get = AsyncMock(return_value=response)
            client_cls.return_value = client

            accounts = await fetch_merchant_accounts("token")

        assert len(accounts) == 1
        assert accounts[0]["accountId"] == "123456"
        assert accounts[0]["displayName"] == "Example Merchant"
        assert accounts[0]["relationship"] == "primary"

    asyncio.run(run())


def test_fetch_merchant_products_maps_status_and_issues() -> None:
    async def run() -> None:
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {
            "products": [
                {
                    "name": "accounts/123/products/online~it~IT~sku-1",
                    "offerId": "sku-1",
                    "contentLanguage": "it",
                    "feedLabel": "IT",
                    "attributes": {
                        "title": "Miele bio",
                        "link": "https://example.com/products/miele",
                        "availability": "IN_STOCK",
                        "price": {"amountMicros": 12990000, "currencyCode": "EUR"},
                        "brand": "Example",
                        "gtin": "8001234567890",
                    },
                    "productStatus": {
                        "destinationStatuses": [
                            {"destination": "Shopping", "status": "APPROVED"}
                        ],
                        "itemLevelIssues": [
                            {
                                "code": "image_link_broken",
                                "severity": "ERROR",
                                "description": "Immagine non valida",
                            }
                        ],
                    },
                }
            ]
        }

        with patch(
            "app.services.google.merchant_client.httpx.AsyncClient",
        ) as client_cls:
            client = AsyncMock()
            client.__aenter__.return_value = client
            client.__aexit__.return_value = None
            client.get = AsyncMock(return_value=response)
            client_cls.return_value = client

            products = await fetch_merchant_products_with_issues("token", account_id="123")

        assert len(products) == 1
        product = products[0]
        assert product["offerId"] == "sku-1"
        assert product["status"] == "approved"
        assert product["price"] == 12.99
        assert product["currency"] == "EUR"
        assert len(product["issues"]) == 1
        assert product["issues"][0]["code"] == "image_link_broken"

    asyncio.run(run())


def test_fetch_merchant_products_maps_404_to_merchant_account_error() -> None:
    async def run() -> None:
        response = MagicMock()
        response.status_code = 404
        response.text = "not found"

        with patch(
            "app.services.google.merchant_client.httpx.AsyncClient",
        ) as client_cls:
            client = AsyncMock()
            client.__aenter__.return_value = client
            client.__aexit__.return_value = None
            client.get = AsyncMock(return_value=response)
            client_cls.return_value = client

            with pytest.raises(MerchantAccountError):
                await fetch_merchant_products_with_issues("token", account_id="missing")

    asyncio.run(run())


def test_fetch_merchant_accounts_maps_403_to_permission_error() -> None:
    async def run() -> None:
        response = MagicMock()
        response.status_code = 403
        response.text = "forbidden"

        with patch(
            "app.services.google.merchant_client.httpx.AsyncClient",
        ) as client_cls:
            client = AsyncMock()
            client.__aenter__.return_value = client
            client.__aexit__.return_value = None
            client.get = AsyncMock(return_value=response)
            client_cls.return_value = client

            with pytest.raises(GoogleIntegrationPermissionError):
                await fetch_merchant_accounts("token")

    asyncio.run(run())
