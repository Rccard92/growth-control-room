from collections import Counter, defaultdict
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shopify import ShopifyOrder, ShopifyOrderLineItem, ShopifyProduct
from app.services.shopify.attribution import (
    compute_attribution_intelligence,
    order_has_tracking_signal,
    resolve_attribution_source,
)
from app.services.shopify.period import ResolvedPeriod, order_effective_at_column

LOW_STOCK_THRESHOLD = 10
HIGH_STOCK_THRESHOLD = 20
LOW_SALES_THRESHOLD = 2
ACTIVE_STATUS = "ACTIVE"


def _is_active_status(status: str | None) -> bool:
    return (status or "").upper() == ACTIVE_STATUS


def _product_to_dict(product: ShopifyProduct) -> dict[str, Any]:
    return {
        "title": product.title,
        "status": product.status,
        "total_inventory": product.total_inventory,
        "featured_image_url": product.featured_image_url,
        "product_type": product.product_type,
        "vendor": product.vendor,
        "handle": product.handle,
    }


def _period_line_item_filters(period: ResolvedPeriod | None) -> list[Any]:
    if period is None:
        return []
    effective_at = order_effective_at_column()
    return [
        effective_at.is_not(None),
        effective_at >= period.start_at,
        effective_at < period.end_at_exclusive,
    ]


async def compute_best_sellers(
    session: AsyncSession,
    store_id: Any,
    products_by_gid: dict[str, ShopifyProduct],
    *,
    period: ResolvedPeriod | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    query = (
        select(
            ShopifyOrderLineItem.product_gid,
            func.sum(ShopifyOrderLineItem.quantity).label("qty"),
            func.sum(
                func.coalesce(
                    ShopifyOrderLineItem.discounted_total,
                    ShopifyOrderLineItem.original_total,
                    0,
                )
            ).label("revenue"),
            func.max(ShopifyOrderLineItem.title).label("title"),
            func.max(ShopifyOrderLineItem.sku).label("sku"),
        )
        .select_from(ShopifyOrderLineItem)
        .join(ShopifyOrder, ShopifyOrderLineItem.order_id == ShopifyOrder.id)
        .where(
            ShopifyOrderLineItem.shopify_store_id == store_id,
            ShopifyOrderLineItem.product_gid.is_not(None),
            *_period_line_item_filters(period),
        )
        .group_by(ShopifyOrderLineItem.product_gid)
        .order_by(func.sum(ShopifyOrderLineItem.quantity).desc())
        .limit(limit)
    )

    rows = (await session.execute(query)).all()
    items: list[dict[str, Any]] = []
    for row in rows:
        product = products_by_gid.get(row.product_gid or "")
        items.append(
            {
                "product_title": row.title or (product.title if product else row.product_gid),
                "sku": row.sku or (product.handle if product else None),
                "quantity_sold": int(row.qty or 0),
                "revenue": Decimal(str(row.revenue or 0)),
                "current_inventory": product.total_inventory if product else None,
                "status": product.status if product else None,
            }
        )
    return items


async def compute_sold_product_gids(
    session: AsyncSession,
    store_id: Any,
    *,
    period: ResolvedPeriod | None = None,
) -> set[str]:
    query = (
        select(ShopifyOrderLineItem.product_gid)
        .select_from(ShopifyOrderLineItem)
        .join(ShopifyOrder, ShopifyOrderLineItem.order_id == ShopifyOrder.id)
        .where(
            ShopifyOrderLineItem.shopify_store_id == store_id,
            ShopifyOrderLineItem.product_gid.is_not(None),
            *_period_line_item_filters(period),
        )
        .distinct()
    )
    result = await session.execute(query)
    return {row[0] for row in result.all() if row[0]}


async def compute_qty_by_product_gid(
    session: AsyncSession,
    store_id: Any,
    *,
    period: ResolvedPeriod | None = None,
) -> Counter[str]:
    query = (
        select(
            ShopifyOrderLineItem.product_gid,
            func.sum(ShopifyOrderLineItem.quantity),
        )
        .select_from(ShopifyOrderLineItem)
        .join(ShopifyOrder, ShopifyOrderLineItem.order_id == ShopifyOrder.id)
        .where(
            ShopifyOrderLineItem.shopify_store_id == store_id,
            ShopifyOrderLineItem.product_gid.is_not(None),
            *_period_line_item_filters(period),
        )
        .group_by(ShopifyOrderLineItem.product_gid)
    )
    counter: Counter[str] = Counter()
    for gid, qty in (await session.execute(query)).all():
        if gid:
            counter[gid] += int(qty or 0)
    return counter


def compute_products_without_sales(
    products: list[ShopifyProduct],
    sold_product_gids: set[str],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for product in products:
        if not _is_active_status(product.status):
            continue
        if product.shopify_gid in sold_product_gids:
            continue
        seo_issue = not (product.seo_title or "").strip() or not (
            product.seo_description or ""
        ).strip()
        result.append(
            {
                "product_title": product.title,
                "current_inventory": product.total_inventory,
                "status": product.status,
                "product_type": product.product_type,
                "seo_issue": seo_issue,
            }
        )
    return result[:20]


def compute_high_stock_low_sales(
    products: list[ShopifyProduct],
    qty_by_gid: Counter[str],
    *,
    period_label: str | None = None,
) -> list[dict[str, Any]]:
    period_suffix = period_label or "nel periodo selezionato"
    result: list[dict[str, Any]] = []
    for product in products:
        if not _is_active_status(product.status):
            continue
        inv = product.total_inventory
        if inv is None or inv <= HIGH_STOCK_THRESHOLD:
            continue
        sold = qty_by_gid.get(product.shopify_gid, 0)
        if sold > LOW_SALES_THRESHOLD:
            continue
        result.append(
            {
                "product_title": product.title,
                "current_inventory": inv,
                "quantity_sold": sold,
                "issue": (
                    f"Stock alto ({inv} unità) con vendite basse "
                    f"({sold} {period_suffix})"
                ),
            }
        )
    return result[:15]


def compute_revenue_by_source(orders: list[ShopifyOrder]) -> list[dict[str, Any]]:
    revenue_map: defaultdict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    count_map: Counter[str] = Counter()
    for order in orders:
        source = resolve_attribution_source(order)
        revenue = order.current_total_price or order.total_price or Decimal("0")
        revenue_map[source] += revenue
        count_map[source] += 1
    return [
        {
            "source": source,
            "revenue": revenue,
            "orders_count": count_map[source],
        }
        for source, revenue in sorted(revenue_map.items(), key=lambda x: x[1], reverse=True)
    ][:15]


def compute_orders_by_source(orders: list[ShopifyOrder]) -> list[dict[str, Any]]:
    return compute_revenue_by_source(orders)


def compute_tracking_quality_score(orders: list[ShopifyOrder]) -> float:
    if not orders:
        return 0.0
    signals = sum(1 for order in orders if order_has_tracking_signal(order))
    return round((signals / len(orders)) * 100, 1)


def compute_attribution_from_orders(
    orders: list[ShopifyOrder],
) -> dict[str, Any]:
    return compute_attribution_intelligence(orders)


def product_lookup(products: list[ShopifyProduct]) -> dict[str, ShopifyProduct]:
    return {p.shopify_gid: p for p in products}
