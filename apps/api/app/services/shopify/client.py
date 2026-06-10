import re
from typing import Any
from urllib.parse import urlparse

import httpx

SHOPIFY_API_VERSION = "2026-04"


class ShopifyAPIError(Exception):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def normalize_shop_domain(raw: str) -> str:
    value = raw.strip()
    if not value:
        raise ShopifyAPIError("Il dominio dello shop è obbligatorio")

    if "://" in value:
        parsed = urlparse(value)
        value = parsed.netloc or parsed.path.split("/")[0]

    value = value.strip("/").lower()
    if value.startswith("www."):
        value = value[4:]

    if not value.endswith(".myshopify.com"):
        if "." not in value:
            value = f"{value}.myshopify.com"
        elif not value.endswith(".myshopify.com"):
            raise ShopifyAPIError(
                "Dominio non valido. Usa il formato nomesito.myshopify.com"
            )

    if not re.match(r"^[a-z0-9][a-z0-9-]*\.myshopify\.com$", value):
        raise ShopifyAPIError(
            "Dominio non valido. Usa il formato nomesito.myshopify.com"
        )

    return value


class ShopifyGraphQLClient:
    def __init__(self, shop_domain: str, access_token: str) -> None:
        self.shop_domain = normalize_shop_domain(shop_domain)
        self.access_token = access_token.strip()
        if not self.access_token:
            raise ShopifyAPIError("Il token di accesso Admin API è obbligatorio")
        self._url = (
            f"https://{self.shop_domain}/admin/api/{SHOPIFY_API_VERSION}/graphql.json"
        )

    async def execute(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        headers = {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self._url, json=payload, headers=headers)
        except httpx.RequestError as exc:
            raise ShopifyAPIError(
                "Impossibile contattare Shopify. Verifica il dominio dello shop."
            ) from exc

        if response.status_code == 401:
            raise ShopifyAPIError(
                "Token non valido o permessi insufficienti. "
                "Verifica Admin API access token e scope read_products/read_orders.",
                status_code=401,
            )
        if response.status_code == 403:
            raise ShopifyAPIError(
                "Accesso negato. Verifica i permessi della Custom App Shopify.",
                status_code=403,
            )
        if response.status_code >= 400:
            raise ShopifyAPIError(
                f"Errore Shopify (HTTP {response.status_code}). Riprova più tardi.",
                status_code=response.status_code,
            )

        data = response.json()
        if "errors" in data and data["errors"]:
            messages = [
                err.get("message", str(err)) if isinstance(err, dict) else str(err)
                for err in data["errors"]
            ]
            raise ShopifyAPIError(
                "Errore GraphQL Shopify: " + "; ".join(messages[:3])
            )

        return data.get("data") or {}

    async def execute_raw(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        headers = {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self._url, json=payload, headers=headers)
        except httpx.RequestError as exc:
            raise ShopifyAPIError(
                "Impossibile contattare Shopify. Verifica il dominio dello shop."
            ) from exc

        if response.status_code == 401:
            raise ShopifyAPIError(
                "Token non valido o permessi insufficienti. "
                "Verifica Admin API access token e scope read_products/read_orders.",
                status_code=401,
            )
        if response.status_code == 403:
            raise ShopifyAPIError(
                "Accesso negato. Verifica i permessi della Custom App Shopify.",
                status_code=403,
            )
        if response.status_code >= 400:
            raise ShopifyAPIError(
                f"Errore Shopify (HTTP {response.status_code}). Riprova più tardi.",
                status_code=response.status_code,
            )

        return response.json()

    async def fetch_shop(self) -> dict[str, Any]:
        query = """
        query ShopInfo {
          shop {
            name
            currencyCode
            ianaTimezone
            myshopifyDomain
          }
        }
        """
        data = await self.execute(query)
        shop = data.get("shop")
        if not shop:
            raise ShopifyAPIError("Risposta shop non valida da Shopify")
        return shop

    async def fetch_products(self, limit: int = 50) -> list[dict[str, Any]]:
        query = """
        query Products($first: Int!) {
          products(first: $first) {
            edges {
              node {
                id
                title
                handle
                status
                vendor
                productType
                totalInventory
                featuredImage { url }
                seo { title description }
                createdAt
                updatedAt
              }
            }
          }
        }
        """
        data = await self.execute(query, {"first": limit})
        edges = data.get("products", {}).get("edges", [])
        return [edge["node"] for edge in edges if edge.get("node")]

    _ORDERS_QUERY_FULL = """
        query Orders($first: Int!) {
          orders(first: $first, sortKey: CREATED_AT, reverse: true) {
            edges {
              node {
                id
                name
                createdAt
                processedAt
                displayFinancialStatus
                displayFulfillmentStatus
                email
                sourceName
                sourceIdentifier
                registeredSourceUrl
                totalPriceSet { shopMoney { amount currencyCode } }
                subtotalPriceSet { shopMoney { amount currencyCode } }
                currentTotalPriceSet { shopMoney { amount currencyCode } }
                currentSubtotalPriceSet { shopMoney { amount currencyCode } }
                currentTotalDiscountsSet { shopMoney { amount currencyCode } }
                currentTotalTaxSet { shopMoney { amount currencyCode } }
                totalShippingPriceSet { shopMoney { amount currencyCode } }
                customer {
                  id
                  email
                  firstName
                  lastName
                  numberOfOrders
                  amountSpent { amount }
                }
                channelInformation {
                  channelDefinition { channelName }
                }
                customerJourneySummary {
                  firstVisit {
                    occurredAt
                    landingPage
                    referralCode
                    source
                    sourceType
                    utmParameters { campaign content medium source term }
                  }
                  lastVisit {
                    occurredAt
                    landingPage
                    referralCode
                    source
                    sourceType
                    utmParameters { campaign content medium source term }
                  }
                  momentsCount { count }
                }
                discountCodes
                refunds(first: 5) {
                  nodes { id createdAt }
                }
                lineItems(first: 50) {
                  nodes {
                    id
                    title
                    quantity
                    sku
                    vendor
                    product { id title handle productType vendor }
                    variant { id title sku inventoryQuantity }
                    discountedTotalSet { shopMoney { amount currencyCode } }
                    originalTotalSet { shopMoney { amount currencyCode } }
                  }
                }
              }
            }
          }
        }
        """

    _ORDERS_QUERY_STANDARD = """
        query Orders($first: Int!) {
          orders(first: $first, sortKey: CREATED_AT, reverse: true) {
            edges {
              node {
                id
                name
                createdAt
                processedAt
                displayFinancialStatus
                displayFulfillmentStatus
                email
                sourceName
                sourceIdentifier
                registeredSourceUrl
                totalPriceSet { shopMoney { amount currencyCode } }
                subtotalPriceSet { shopMoney { amount currencyCode } }
                customer {
                  id
                  email
                  firstName
                  lastName
                  numberOfOrders
                  amountSpent { amount }
                }
                channelInformation {
                  channelDefinition { channelName }
                }
                discountCodes
                lineItems(first: 50) {
                  nodes {
                    id
                    title
                    quantity
                    sku
                    vendor
                    product { id title handle productType vendor }
                    variant { id title sku inventoryQuantity }
                    discountedTotalSet { shopMoney { amount currencyCode } }
                    originalTotalSet { shopMoney { amount currencyCode } }
                  }
                }
              }
            }
          }
        }
        """

    _ORDERS_QUERY_MINIMAL = """
        query Orders($first: Int!) {
          orders(first: $first, sortKey: CREATED_AT, reverse: true) {
            edges {
              node {
                id
                name
                createdAt
                processedAt
                displayFinancialStatus
                displayFulfillmentStatus
                email
                sourceName
                totalPriceSet { shopMoney { amount currencyCode } }
                subtotalPriceSet { shopMoney { amount currencyCode } }
                lineItems(first: 50) {
                  nodes {
                    id
                    title
                    quantity
                    sku
                    product { id title vendor productType }
                    variant { id }
                    discountedTotalSet { shopMoney { amount currencyCode } }
                    originalTotalSet { shopMoney { amount currencyCode } }
                  }
                }
              }
            }
          }
        }
        """

    async def fetch_orders(self, limit: int = 50) -> list[dict[str, Any]]:
        variables = {"first": limit}
        queries = [
            self._ORDERS_QUERY_FULL,
            self._ORDERS_QUERY_STANDARD,
            self._ORDERS_QUERY_MINIMAL,
        ]

        last_error: str | None = None
        for query in queries:
            raw = await self.execute_raw(query, variables)
            if raw.get("errors"):
                messages = [
                    err.get("message", str(err)) if isinstance(err, dict) else str(err)
                    for err in raw["errors"]
                ]
                last_error = "; ".join(messages[:3])
                continue
            data = raw.get("data") or {}
            edges = data.get("orders", {}).get("edges", [])
            return [edge["node"] for edge in edges if edge.get("node")]

        if last_error:
            raise ShopifyAPIError(f"Errore GraphQL Shopify: {last_error}")
        return []
