"""Shopify commerce data helpers for Growth Audit product performance."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app.services.shopify.client import DEFAULT_PAGE_SIZE, ShopifyAPIError, ShopifyGraphQLClient
from app.services.shopify.exceptions import ShopifyCommerceApiError

PRODUCT_SNAPSHOT_FIELDS = """
      ... on Product {
        id
        title
        handle
        status
        totalInventory
        featuredImage { url altText }
        variants(first: 100) {
          nodes {
            id
            title
            price
            compareAtPrice
            inventoryQuantity
            availableForSale
          }
        }
      }
"""

PRODUCT_SNAPSHOT_CHUNK_SIZE = 50


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def _parse_money_amount(money_set: dict[str, Any] | None) -> tuple[Decimal, str | None]:
    if not money_set or not isinstance(money_set, dict):
        return Decimal("0"), None
    shop_money = money_set.get("shopMoney") or {}
    if not isinstance(shop_money, dict):
        return Decimal("0"), None
    amount_raw = shop_money.get("amount")
    currency = shop_money.get("currencyCode")
    try:
        amount = Decimal(str(amount_raw or "0"))
    except Exception:
        amount = Decimal("0")
    return amount, currency if isinstance(currency, str) else None


def _order_in_period(
    created_at: datetime | None,
    *,
    start_date: date,
    end_date: date,
) -> bool:
    if created_at is None:
        return False
    order_date = created_at.date()
    return start_date <= order_date <= end_date


def _aggregate_line_items(
    orders: list[dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], str | None]:
    aggregates: dict[str, dict[str, Any]] = {}
    currency: str | None = None

    for order in orders:
        order_id = str(order.get("id") or "")
        line_items = (order.get("lineItems") or {}).get("nodes") or []
        if not isinstance(line_items, list):
            continue

        for line_item in line_items:
            if not line_item or not isinstance(line_item, dict):
                continue
            product = line_item.get("product") or {}
            product_gid = product.get("id") if isinstance(product, dict) else None
            if not product_gid:
                continue

            quantity = int(line_item.get("quantity") or 0)
            if quantity <= 0:
                continue

            discounted = _parse_money_amount(line_item.get("discountedTotalSet"))
            original = _parse_money_amount(line_item.get("originalTotalSet"))
            line_sales = discounted[0] if discounted[0] > 0 else original[0]
            line_currency = discounted[1] or original[1]
            if line_currency and currency is None:
                currency = line_currency

            bucket = aggregates.setdefault(
                product_gid,
                {
                    "quantitySold": 0,
                    "ordersCount": set(),
                    "sales": Decimal("0"),
                },
            )
            bucket["quantitySold"] += quantity
            if order_id:
                bucket["ordersCount"].add(order_id)
            bucket["sales"] += line_sales

    serialized: dict[str, dict[str, Any]] = {}
    for product_gid, bucket in aggregates.items():
        serialized[product_gid] = {
            "quantitySold": bucket["quantitySold"],
            "ordersCount": len(bucket["ordersCount"]),
            "sales": float(bucket["sales"]),
        }

    return serialized, currency


async def _fetch_orders_page(
    client: ShopifyGraphQLClient,
    *,
    page_size: int,
    cursor: str | None,
) -> tuple[list[dict[str, Any]], bool, str | None]:
    query = client._build_orders_query({})
    variables: dict[str, Any] = {"first": page_size, "after": cursor}
    raw = await client.execute_raw(query, variables)

    if raw.get("errors"):
        messages = [
            err.get("message", str(err)) if isinstance(err, dict) else str(err)
            for err in raw["errors"]
        ]
        raise ShopifyCommerceApiError(
            "Errore GraphQL Shopify ordini: " + "; ".join(messages[:3]),
        )

    connection = (raw.get("data") or {}).get("orders") or {}
    edges = connection.get("edges") or []
    nodes = [edge.get("node") for edge in edges if edge.get("node")]
    page_info = connection.get("pageInfo") or {}
    return (
        nodes,
        bool(page_info.get("hasNextPage")),
        page_info.get("endCursor"),
    )


async def fetch_shopify_orders_for_product_performance(
    *,
    shop_domain: str,
    access_token: str,
    start_date: date,
    end_date: date,
    cursor: str | None = None,
) -> dict[str, Any]:
    """Fetch and aggregate Shopify order line items for product GIDs in a date range."""
    client = ShopifyGraphQLClient(shop_domain, access_token)
    page_size = DEFAULT_PAGE_SIZE
    filtered_orders: list[dict[str, Any]] = []
    next_cursor = cursor
    has_more = False

    while True:
        nodes, page_has_more, end_cursor = await _fetch_orders_page(
            client,
            page_size=page_size,
            cursor=next_cursor,
        )
        if not nodes:
            has_more = page_has_more
            next_cursor = end_cursor
            break

        stop_pagination = False
        for order in nodes:
            if order.get("cancelledAt"):
                continue
            created_at = _parse_iso_datetime(order.get("createdAt"))
            if created_at is None:
                continue
            if created_at.date() < start_date:
                stop_pagination = True
                break
            if _order_in_period(created_at, start_date=start_date, end_date=end_date):
                filtered_orders.append(order)

        if stop_pagination or not page_has_more:
            has_more = False if stop_pagination else page_has_more
            next_cursor = end_cursor
            break

        next_cursor = end_cursor

    aggregates_by_product_gid, currency = _aggregate_line_items(filtered_orders)

    return {
        "orders_count": len(filtered_orders),
        "aggregates_by_product_gid": aggregates_by_product_gid,
        "currency": currency,
        "has_more": has_more,
        "next_cursor": next_cursor,
    }


def _normalize_product_snapshot(node: dict[str, Any]) -> dict[str, Any] | None:
    if not node or not node.get("id"):
        return None

    variants = (node.get("variants") or {}).get("nodes") or []
    prices: list[float] = []
    available_for_sale: bool | None = None

    for variant in variants:
        if not isinstance(variant, dict):
            continue
        price_raw = variant.get("price")
        try:
            if price_raw is not None:
                prices.append(float(price_raw))
        except (TypeError, ValueError):
            pass
        variant_available = variant.get("availableForSale")
        if variant_available is True:
            available_for_sale = True
        elif variant_available is False and available_for_sale is None:
            available_for_sale = False

    featured = node.get("featuredImage") or {}
    total_inventory = node.get("totalInventory")
    stock = int(total_inventory) if total_inventory is not None else None

    if available_for_sale is None and stock is not None:
        available_for_sale = stock > 0 and (node.get("status") or "").upper() == "ACTIVE"

    return {
        "productGid": node.get("id"),
        "title": node.get("title"),
        "handle": node.get("handle"),
        "status": node.get("status"),
        "stock": stock,
        "availableForSale": available_for_sale,
        "priceMin": min(prices) if prices else None,
        "priceMax": max(prices) if prices else None,
        "featuredImageUrl": featured.get("url") if isinstance(featured, dict) else None,
    }


async def fetch_shopify_products_inventory_snapshot(
    *,
    shop_domain: str,
    access_token: str,
    product_gids: list[str],
) -> dict[str, Any]:
    """Fetch inventory and pricing snapshot for product GIDs."""
    unique_gids = sorted({gid for gid in product_gids if gid})
    if not unique_gids:
        return {"products_by_gid": {}}

    client = ShopifyGraphQLClient(shop_domain, access_token)
    products_by_gid: dict[str, dict[str, Any]] = {}

    for index in range(0, len(unique_gids), PRODUCT_SNAPSHOT_CHUNK_SIZE):
        chunk = unique_gids[index : index + PRODUCT_SNAPSHOT_CHUNK_SIZE]
        query = f"""
        query ProductSnapshots($ids: [ID!]!) {{
          nodes(ids: $ids) {{
            {PRODUCT_SNAPSHOT_FIELDS}
          }}
        }}
        """
        try:
            data = await client.execute(query, {"ids": chunk})
        except ShopifyAPIError as exc:
            raise ShopifyCommerceApiError(str(exc), status_code=exc.status_code) from exc

        nodes = data.get("nodes") or []
        for node in nodes:
            if not node:
                continue
            snapshot = _normalize_product_snapshot(node)
            if snapshot and snapshot.get("productGid"):
                products_by_gid[snapshot["productGid"]] = snapshot

    missing_gids = [gid for gid in unique_gids if gid not in products_by_gid]
    for gid in missing_gids:
        try:
            node = await client.fetch_product_by_gid(gid)
            snapshot = _normalize_product_snapshot(node)
            if snapshot:
                products_by_gid[gid] = snapshot
        except ShopifyAPIError:
            continue

    return {"products_by_gid": products_by_gid}
