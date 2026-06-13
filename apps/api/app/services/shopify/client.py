import logging
import re
from typing import Any
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

SHOPIFY_API_VERSION = "2026-04"
DEFAULT_PAGE_SIZE = 100

# Optional GraphQL field blocks for orders (removed on access/validation errors).
ORDER_OPTIONAL_BLOCKS: dict[str, str] = {
    "email": "email",
    "shipping": "totalShippingPriceSet { shopMoney { amount currencyCode } }",
    "channel": "channelInformation { channelDefinition { handle channelName } }",
    "journey": """
                customerJourneySummary {
                  ready
                  daysToConversion
                  customerOrderIndex
                  firstVisit {
                    occurredAt
                    landingPage
                    referralCode
                    source
                    sourceType
                    utmParameters { source medium campaign content term }
                  }
                  lastVisit {
                    occurredAt
                    landingPage
                    referralCode
                    source
                    sourceType
                    utmParameters { source medium campaign content term }
                  }
                }""",
    "refunds": """
                refunds(first: 50) {
                  nodes {
                    id
                    createdAt
                    totalRefundedSet { shopMoney { amount currencyCode } }
                  }
                }""",
    "tax": "currentTotalTaxSet { shopMoney { amount currencyCode } }",
}

ORDER_CORE_FIELDS = """
                id
                name
                createdAt
                processedAt
                displayFinancialStatus
                displayFulfillmentStatus
                sourceName
                sourceIdentifier
                registeredSourceUrl
                totalPriceSet { shopMoney { amount currencyCode } }
                currentTotalPriceSet { shopMoney { amount currencyCode } }
                currentSubtotalPriceSet { shopMoney { amount currencyCode } }
                currentTotalDiscountsSet { shopMoney { amount currencyCode } }
                discountCodes
                lineItems(first: 100) {
                  nodes {
                    id
                    title
                    quantity
                    sku
                    vendor
                    product { id title handle vendor productType }
                    variant { id title sku price compareAtPrice inventoryQuantity }
                    discountedTotalSet { shopMoney { amount currencyCode } }
                    originalTotalSet { shopMoney { amount currencyCode } }
                  }
                }"""

PRODUCT_FIELDS = """
                id
                title
                handle
                status
                vendor
                productType
                tags
                totalInventory
                createdAt
                updatedAt
                featuredImage { url altText }
                descriptionHtml
                media(first: 20) {
                  nodes {
                    id
                    alt
                    mediaContentType
                    preview {
                      image {
                        url
                        altText
                      }
                    }
                  }
                }
                seo { title description }
                variants(first: 100) {
                  nodes {
                    id
                    title
                    sku
                    price
                    compareAtPrice
                    inventoryQuantity
                    selectedOptions { name value }
                  }
                }"""


COLLECTION_FIELDS = """
                id
                title
                handle
                descriptionHtml
                seo { title description }
                image { url altText }
                productsCount"""

PAGE_FIELDS = """
                id
                title
                handle
                body
                seo { title description }
                publishedAt"""

BLOG_FIELDS = """
                id
                title
                handle"""

ARTICLE_FIELDS = """
                id
                title
                handle
                body
                summary
                seo { title description }
                tags
                publishedAt
                author { name }"""


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
        self.degraded_order_blocks: list[str] = []

    async def execute(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        raw = await self.execute_raw(query, variables)
        if raw.get("errors"):
            messages = [
                err.get("message", str(err)) if isinstance(err, dict) else str(err)
                for err in raw["errors"]
            ]
            raise ShopifyAPIError(
                "Errore GraphQL Shopify: " + "; ".join(messages[:3])
            )
        return raw.get("data") or {}

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
            async with httpx.AsyncClient(timeout=60.0) as client:
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

    async def execute_shopifyql(self, shopifyql: str) -> dict[str, Any]:
        query = """
        query ShopifyQL($query: String!) {
          shopifyqlQuery(query: $query) {
            __typename
            tableData {
              columns {
                name
                dataType
              }
              rows
            }
            parseErrors {
              code
              message
            }
          }
        }
        """
        raw = await self.execute_raw(query, {"query": shopifyql})
        graphql_errors = raw.get("errors") or []
        data = raw.get("data") or {}
        result = data.get("shopifyqlQuery") or {}
        table_data = result.get("tableData") or {}
        return {
            "columns": table_data.get("columns") or [],
            "rows": table_data.get("rows") or [],
            "parse_errors": result.get("parseErrors") or [],
            "graphql_errors": graphql_errors,
            "typename": result.get("__typename"),
        }

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

    async def fetch_access_scopes(self) -> list[str]:
        query = """
        query CurrentAppAccessScopes {
          currentAppInstallation {
            accessScopes {
              handle
            }
          }
        }
        """
        try:
            data = await self.execute(query)
            installation = data.get("currentAppInstallation") or {}
            scopes = installation.get("accessScopes") or []
            handles = [
                s.get("handle")
                for s in scopes
                if isinstance(s, dict) and s.get("handle")
            ]
            if handles:
                return sorted(handles)
        except ShopifyAPIError:
            pass
        return await self._fetch_access_scopes_rest()

    async def _fetch_access_scopes_rest(self) -> list[str]:
        url = f"https://{self.shop_domain}/admin/oauth/access_scopes.json"
        headers = {"X-Shopify-Access-Token": self.access_token}
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers)
        except httpx.RequestError as exc:
            raise ShopifyAPIError(
                "Impossibile verificare gli scope Shopify. Riprova più tardi."
            ) from exc
        if response.status_code >= 400:
            raise ShopifyAPIError(
                f"Verifica scope Shopify fallita (HTTP {response.status_code}).",
                status_code=response.status_code,
            )
        payload = response.json()
        scopes = payload.get("access_scopes") or []
        handles = [
            s.get("handle") for s in scopes if isinstance(s, dict) and s.get("handle")
        ]
        return sorted(handles)

    async def _paginate_connection(
        self,
        connection_name: str,
        node_fields: str,
        *,
        page_size: int = DEFAULT_PAGE_SIZE,
        sort_key: str | None = None,
        reverse: bool | None = None,
    ) -> list[dict[str, Any]]:
        sort_args = ""
        if sort_key:
            sort_args += f", sortKey: {sort_key}"
        if reverse is not None:
            sort_args += f", reverse: {'true' if reverse else 'false'}"

        query_template = f"""
        query Paginate($first: Int!, $after: String) {{
          {connection_name}(first: $first, after: $after{sort_args}) {{
            pageInfo {{
              hasNextPage
              endCursor
            }}
            edges {{
              node {{
                {node_fields}
              }}
            }}
          }}
        }}
        """

        all_nodes: list[dict[str, Any]] = []
        cursor: str | None = None

        while True:
            variables: dict[str, Any] = {"first": page_size, "after": cursor}
            data = await self.execute(query_template, variables)
            connection = data.get(connection_name) or {}
            edges = connection.get("edges") or []
            for edge in edges:
                node = edge.get("node")
                if node:
                    all_nodes.append(node)

            page_info = connection.get("pageInfo") or {}
            if not page_info.get("hasNextPage"):
                break
            cursor = page_info.get("endCursor")
            if not cursor:
                break

        return all_nodes

    async def fetch_product_by_gid(self, gid: str) -> dict[str, Any]:
        query = f"""
        query ProductById($id: ID!) {{
          product(id: $id) {{
            {PRODUCT_FIELDS}
          }}
        }}
        """
        data = await self.execute(query, {"id": gid})
        node = data.get("product") or {}
        if not node:
            raise ShopifyAPIError("Prodotto non trovato su Shopify", status_code=404)
        return node

    async def fetch_collection_by_gid(self, gid: str) -> dict[str, Any]:
        query = f"""
        query CollectionById($id: ID!) {{
          collection(id: $id) {{
            {COLLECTION_FIELDS}
          }}
        }}
        """
        data = await self.execute(query, {"id": gid})
        node = data.get("collection") or {}
        if not node:
            raise ShopifyAPIError("Collezione non trovata su Shopify", status_code=404)
        return node

    async def fetch_all_products(
        self,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> list[dict[str, Any]]:
        return await self._paginate_connection(
            "products",
            PRODUCT_FIELDS,
            page_size=page_size,
        )

    async def fetch_all_collections(
        self,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> list[dict[str, Any]]:
        return await self._paginate_connection(
            "collections",
            COLLECTION_FIELDS,
            page_size=page_size,
        )

    async def fetch_all_pages(
        self,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> list[dict[str, Any]]:
        return await self._paginate_connection(
            "pages",
            PAGE_FIELDS,
            page_size=page_size,
        )

    async def fetch_all_blogs(
        self,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> list[dict[str, Any]]:
        return await self._paginate_connection(
            "blogs",
            BLOG_FIELDS,
            page_size=page_size,
        )

    async def fetch_all_articles(
        self,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> list[dict[str, Any]]:
        blogs = await self.fetch_all_blogs(page_size=page_size)
        all_articles: list[dict[str, Any]] = []
        for blog in blogs:
            blog_gid = blog.get("id")
            if not blog_gid:
                continue
            articles = await self._paginate_blog_articles(blog_gid, page_size=page_size)
            for article in articles:
                article["_blog"] = {
                    "id": blog_gid,
                    "title": blog.get("title"),
                    "handle": blog.get("handle"),
                }
            all_articles.extend(articles)
        return all_articles

    async def _paginate_blog_articles(
        self,
        blog_gid: str,
        *,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> list[dict[str, Any]]:
        query_template = f"""
        query BlogArticles($blogId: ID!, $first: Int!, $after: String) {{
          blog(id: $blogId) {{
            articles(first: $first, after: $after) {{
              pageInfo {{
                hasNextPage
                endCursor
              }}
              edges {{
                node {{
                  {ARTICLE_FIELDS}
                }}
              }}
            }}
          }}
        }}
        """

        all_nodes: list[dict[str, Any]] = []
        cursor: str | None = None

        while True:
            variables: dict[str, Any] = {
                "blogId": blog_gid,
                "first": page_size,
                "after": cursor,
            }
            data = await self.execute(query_template, variables)
            blog = data.get("blog") or {}
            connection = blog.get("articles") or {}
            edges = connection.get("edges") or []
            for edge in edges:
                node = edge.get("node")
                if node:
                    all_nodes.append(node)

            page_info = connection.get("pageInfo") or {}
            if not page_info.get("hasNextPage"):
                break
            cursor = page_info.get("endCursor")
            if not cursor:
                break

        return all_nodes

    def _build_orders_query(self, optional_blocks: dict[str, str]) -> str:
        extra = "\n".join(optional_blocks.values())
        node_fields = f"{ORDER_CORE_FIELDS}\n{extra}"
        return f"""
        query Orders($first: Int!, $after: String) {{
          orders(first: $first, after: $after, sortKey: CREATED_AT, reverse: true) {{
            pageInfo {{
              hasNextPage
              endCursor
            }}
            edges {{
              node {{
                {node_fields}
              }}
            }}
          }}
        }}
        """

    @staticmethod
    def _infer_failed_order_blocks(errors: list[Any]) -> set[str]:
        failed: set[str] = set()
        blob = " ".join(
            err.get("message", str(err)) if isinstance(err, dict) else str(err)
            for err in errors
        ).lower()

        if "email" in blob:
            failed.add("email")
        if "totalshippingpriceset" in blob or "shipping" in blob:
            failed.add("shipping")
        if "channelinformation" in blob or "channeldefinition" in blob:
            failed.add("channel")
        if "customerjourneysummary" in blob or "customervisit" in blob:
            failed.add("journey")
        if "refund" in blob:
            failed.add("refunds")

        if not failed and errors:
            failed.add(next(iter(ORDER_OPTIONAL_BLOCKS.keys())))

        return failed

    async def fetch_all_orders(
        self,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> list[dict[str, Any]]:
        self.degraded_order_blocks = []
        active_optional = dict(ORDER_OPTIONAL_BLOCKS)

        while True:
            query = self._build_orders_query(active_optional)
            all_nodes: list[dict[str, Any]] = []
            cursor: str | None = None
            pagination_failed = False

            while True:
                variables: dict[str, Any] = {"first": page_size, "after": cursor}
                raw = await self.execute_raw(query, variables)

                if raw.get("errors"):
                    failed = self._infer_failed_order_blocks(raw["errors"])
                    removed = False
                    for block_key in failed:
                        if block_key in active_optional:
                            del active_optional[block_key]
                            if block_key not in self.degraded_order_blocks:
                                self.degraded_order_blocks.append(block_key)
                            removed = True
                    if removed:
                        pagination_failed = True
                        break
                    messages = [
                        err.get("message", str(err))
                        if isinstance(err, dict)
                        else str(err)
                        for err in raw["errors"]
                    ]
                    raise ShopifyAPIError(
                        "Errore GraphQL Shopify: " + "; ".join(messages[:3])
                    )

                data = raw.get("data") or {}
                connection = data.get("orders") or {}
                edges = connection.get("edges") or []
                for edge in edges:
                    node = edge.get("node")
                    if node:
                        all_nodes.append(node)

                page_info = connection.get("pageInfo") or {}
                if not page_info.get("hasNextPage"):
                    break
                cursor = page_info.get("endCursor")
                if not cursor:
                    break

            if pagination_failed:
                continue

            if self.degraded_order_blocks:
                logger.info(
                    "Shopify order sync: optional blocks degraded: %s",
                    ", ".join(self.degraded_order_blocks),
                )
            return all_nodes

    async def fetch_products(self, limit: int = 50) -> list[dict[str, Any]]:
        """Backward-compatible wrapper for legacy callers."""
        nodes = await self._paginate_connection(
            "products",
            PRODUCT_FIELDS,
            page_size=min(limit, DEFAULT_PAGE_SIZE),
        )
        return nodes[:limit]

    async def fetch_orders(self, limit: int = 50) -> list[dict[str, Any]]:
        """Backward-compatible wrapper for legacy callers."""
        nodes = await self.fetch_all_orders(page_size=min(limit, DEFAULT_PAGE_SIZE))
        return nodes[:limit]
