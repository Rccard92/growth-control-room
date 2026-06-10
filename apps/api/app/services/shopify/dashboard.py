from collections import Counter
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shopify import ShopifyDailyMetric, ShopifyOrder, ShopifyProduct, ShopifyStore

LOW_STOCK_THRESHOLD = 5


async def build_dashboard(
    store: ShopifyStore,
    session: AsyncSession,
) -> dict:
    products_count_result = await session.execute(
        select(func.count()).select_from(ShopifyProduct).where(
            ShopifyProduct.shopify_store_id == store.id
        )
    )
    products_count = products_count_result.scalar_one()

    metrics_result = await session.execute(
        select(
            func.coalesce(func.sum(ShopifyDailyMetric.gross_sales), 0),
            func.coalesce(func.sum(ShopifyDailyMetric.orders_count), 0),
        ).where(ShopifyDailyMetric.shopify_store_id == store.id)
    )
    revenue, orders_count = metrics_result.one()

    if revenue == 0 and orders_count == 0:
        orders_sum_result = await session.execute(
            select(
                func.coalesce(func.sum(ShopifyOrder.total_price), 0),
                func.count(),
            ).where(ShopifyOrder.shopify_store_id == store.id)
        )
        revenue, orders_count = orders_sum_result.one()

    revenue = Decimal(str(revenue))
    orders_count = int(orders_count)
    average_order_value = revenue / orders_count if orders_count else Decimal("0")

    low_stock_result = await session.execute(
        select(ShopifyProduct)
        .where(
            ShopifyProduct.shopify_store_id == store.id,
            ShopifyProduct.total_inventory.is_not(None),
            ShopifyProduct.total_inventory <= LOW_STOCK_THRESHOLD,
        )
        .order_by(ShopifyProduct.total_inventory.asc())
        .limit(10)
    )
    low_stock_products = list(low_stock_result.scalars().all())

    recent_orders_result = await session.execute(
        select(ShopifyOrder)
        .where(ShopifyOrder.shopify_store_id == store.id)
        .order_by(ShopifyOrder.created_at_shopify.desc().nullslast())
        .limit(10)
    )
    recent_orders = list(recent_orders_result.scalars().all())

    top_products = await _compute_top_products(store.id, session)

    return {
        "revenue": revenue,
        "orders_count": orders_count,
        "average_order_value": average_order_value,
        "products_count": products_count,
        "low_stock_products": low_stock_products,
        "top_products": top_products,
        "recent_orders": recent_orders,
        "last_sync_at": store.last_sync_at,
    }


async def _compute_top_products(
    store_id: UUID,
    session: AsyncSession,
) -> list[dict]:
    orders_result = await session.execute(
        select(ShopifyOrder).where(ShopifyOrder.shopify_store_id == store_id)
    )
    orders = orders_result.scalars().all()

    counter: Counter[str] = Counter()
    titles: dict[str, str] = {}

    for order in orders:
        payload = order.raw_payload or {}
        line_items = (payload.get("lineItems") or {}).get("edges") or []
        for edge in line_items:
            node = edge.get("node") or {}
            product = node.get("product") or {}
            product_id = product.get("id")
            if not product_id:
                continue
            qty = int(node.get("quantity") or 0)
            counter[product_id] += qty
            titles[product_id] = product.get("title") or node.get("title") or product_id

    top = counter.most_common(5)
    return [
        {"product_gid": gid, "title": titles.get(gid, gid), "quantity_sold": qty}
        for gid, qty in top
    ]
