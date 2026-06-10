from collections import defaultdict
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shopify import ShopifyDailyMetric, ShopifyOrder, ShopifyProduct, ShopifyStore
from app.services.shopify.client import ShopifyGraphQLClient


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def _parse_decimal(value: str | None) -> Decimal:
    if not value:
        return Decimal("0")
    return Decimal(value)


async def _upsert_product(
    session: AsyncSession,
    store_id,
    node: dict,
) -> None:
    gid = node["id"]
    result = await session.execute(
        select(ShopifyProduct).where(
            ShopifyProduct.shopify_store_id == store_id,
            ShopifyProduct.shopify_gid == gid,
        )
    )
    product = result.scalar_one_or_none()
    featured = node.get("featuredImage") or {}
    seo = node.get("seo") or {}

    fields = {
        "title": node.get("title") or "",
        "handle": node.get("handle"),
        "status": node.get("status"),
        "vendor": node.get("vendor"),
        "product_type": node.get("productType"),
        "total_inventory": node.get("totalInventory"),
        "featured_image_url": featured.get("url"),
        "seo_title": seo.get("title"),
        "seo_description": seo.get("description"),
        "raw_payload": node,
    }

    if product is None:
        session.add(
            ShopifyProduct(
                shopify_store_id=store_id,
                shopify_gid=gid,
                **fields,
            )
        )
    else:
        for key, val in fields.items():
            setattr(product, key, val)


async def _upsert_order(
    session: AsyncSession,
    store_id,
    node: dict,
) -> None:
    gid = node["id"]
    result = await session.execute(
        select(ShopifyOrder).where(
            ShopifyOrder.shopify_store_id == store_id,
            ShopifyOrder.shopify_gid == gid,
        )
    )
    order = result.scalar_one_or_none()
    total_money = (node.get("totalPriceSet") or {}).get("shopMoney") or {}
    subtotal_money = (node.get("subtotalPriceSet") or {}).get("shopMoney") or {}

    fields = {
        "order_name": node.get("name"),
        "created_at_shopify": _parse_datetime(node.get("createdAt")),
        "processed_at": _parse_datetime(node.get("processedAt")),
        "financial_status": node.get("displayFinancialStatus"),
        "fulfillment_status": node.get("displayFulfillmentStatus"),
        "total_price": _parse_decimal(total_money.get("amount")),
        "subtotal_price": _parse_decimal(subtotal_money.get("amount")),
        "currency": total_money.get("currencyCode"),
        "customer_email": node.get("email"),
        "raw_payload": node,
    }

    if order is None:
        session.add(
            ShopifyOrder(
                shopify_store_id=store_id,
                shopify_gid=gid,
                **fields,
            )
        )
    else:
        for key, val in fields.items():
            setattr(order, key, val)


async def _rebuild_daily_metrics(
    session: AsyncSession,
    store: ShopifyStore,
) -> int:
    result = await session.execute(
        select(ShopifyOrder).where(ShopifyOrder.shopify_store_id == store.id)
    )
    orders = list(result.scalars().all())

    by_date: dict[date, list[ShopifyOrder]] = defaultdict(list)
    for order in orders:
        if order.created_at_shopify is None:
            continue
        order_date = order.created_at_shopify.date()
        by_date[order_date].append(order)

    metrics_count = 0
    for metric_date, day_orders in by_date.items():
        gross = sum((o.total_price for o in day_orders), Decimal("0"))
        count = len(day_orders)
        aov = gross / count if count else Decimal("0")

        metric_result = await session.execute(
            select(ShopifyDailyMetric).where(
                ShopifyDailyMetric.shopify_store_id == store.id,
                ShopifyDailyMetric.date == metric_date,
            )
        )
        metric = metric_result.scalar_one_or_none()
        if metric is None:
            session.add(
                ShopifyDailyMetric(
                    shopify_store_id=store.id,
                    date=metric_date,
                    orders_count=count,
                    gross_sales=gross,
                    net_sales=gross,
                    average_order_value=aov,
                )
            )
        else:
            metric.orders_count = count
            metric.gross_sales = gross
            metric.net_sales = gross
            metric.average_order_value = aov
        metrics_count += 1

    return metrics_count


async def sync_shopify_store(
    store: ShopifyStore,
    client: ShopifyGraphQLClient,
    session: AsyncSession,
) -> dict[str, int]:
    products = await client.fetch_products(limit=50)
    orders = await client.fetch_orders(limit=50)

    for node in products:
        await _upsert_product(session, store.id, node)
    for node in orders:
        await _upsert_order(session, store.id, node)

    metrics_count = await _rebuild_daily_metrics(session, store)

    store.last_sync_at = datetime.now(UTC)
    store.connection_status = "connected"
    await session.flush()

    return {
        "products_synced": len(products),
        "orders_synced": len(orders),
        "metrics_synced": metrics_count,
    }
