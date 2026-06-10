from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shopify import ShopifyDailyMetric, ShopifyOrder, ShopifyOrderLineItem, ShopifyProduct, ShopifyStore
from app.services.shopify.analytics import compute_best_sellers, product_lookup
from app.services.shopify.attribution import UNKNOWN_SOURCE, compute_attribution_intelligence
from app.services.shopify.period import ResolvedPeriod, order_effective_at_column

PENDING_STATUSES = {"PENDING", "AUTHORIZED", "PARTIALLY_PAID"}
PAID_STATUSES = {"PAID", "PARTIALLY_REFUNDED", "REFUNDED"}
FULFILLED_STATUSES = {"FULFILLED"}


@dataclass
class PeriodSnapshot:
    revenue: Decimal
    orders_count: int
    average_order_value: Decimal
    paid_orders_count: int
    pending_orders_count: int
    fulfilled_orders_count: int
    unfulfilled_orders_count: int
    attribution_intelligence: dict[str, Any]
    product_sales: dict[str, dict[str, Any]]
    best_sellers: list[dict[str, Any]]


def compare_scalar(current: Decimal | int | float, previous: Decimal | int | float) -> dict[str, Any]:
    cur = Decimal(str(current))
    prev = Decimal(str(previous))
    delta = cur - prev

    if prev == 0 and cur > 0:
        return {
            "current": cur,
            "previous": prev,
            "delta": delta,
            "delta_percent": None,
            "direction": "up",
        }
    if prev == 0 and cur == 0:
        return {
            "current": cur,
            "previous": prev,
            "delta": delta,
            "delta_percent": None,
            "direction": "flat",
        }

    delta_percent = float((delta / prev) * 100)
    if delta > 0:
        direction = "up"
    elif delta < 0:
        direction = "down"
    else:
        direction = "flat"

    return {
        "current": cur,
        "previous": prev,
        "delta": delta,
        "delta_percent": round(delta_percent, 1),
        "direction": direction,
    }


async def _fetch_period_orders(
    session: AsyncSession,
    store_id: Any,
    period: ResolvedPeriod,
) -> list[ShopifyOrder]:
    effective_at = order_effective_at_column()
    result = await session.execute(
        select(ShopifyOrder)
        .where(
            ShopifyOrder.shopify_store_id == store_id,
            effective_at.is_not(None),
            effective_at >= period.start_at,
            effective_at < period.end_at_exclusive,
        )
        .order_by(effective_at.desc())
    )
    return list(result.scalars().all())


async def compute_period_snapshot(
    session: AsyncSession,
    store: ShopifyStore,
    period: ResolvedPeriod,
    products: list[ShopifyProduct],
) -> PeriodSnapshot:
    period_orders = await _fetch_period_orders(session, store.id, period)

    pending_orders = [
        o for o in period_orders if (o.financial_status or "").upper() in PENDING_STATUSES
    ]
    unfulfilled_orders = [
        o
        for o in period_orders
        if (o.fulfillment_status or "").upper() not in FULFILLED_STATUSES
        and (o.fulfillment_status or "").strip() != ""
    ]
    paid_orders_count = sum(
        1 for o in period_orders if (o.financial_status or "").upper() in PAID_STATUSES
    )
    fulfilled_orders_count = sum(
        1 for o in period_orders if (o.fulfillment_status or "").upper() in FULFILLED_STATUSES
    )

    revenue = Decimal("0")
    orders_count = 0
    metrics_result = await session.execute(
        select(
            func.coalesce(func.sum(ShopifyDailyMetric.gross_sales), 0),
            func.coalesce(func.sum(ShopifyDailyMetric.orders_count), 0),
        ).where(
            ShopifyDailyMetric.shopify_store_id == store.id,
            ShopifyDailyMetric.date >= period.start_date,
            ShopifyDailyMetric.date <= period.end_date,
        )
    )
    revenue, orders_count = metrics_result.one()
    revenue = Decimal(str(revenue))
    orders_count = int(orders_count)

    if revenue == 0 and orders_count == 0 and period_orders:
        revenue = sum(
            (o.current_total_price or o.total_price for o in period_orders),
            Decimal("0"),
        )
        orders_count = len(period_orders)

    average_order_value = revenue / orders_count if orders_count else Decimal("0")

    products_by_gid = product_lookup(products)
    best_sellers = await compute_best_sellers(
        session,
        store.id,
        products_by_gid,
        period=period,
        limit=50,
    )

    product_sales: dict[str, dict[str, Any]] = {}
    for item in best_sellers:
        title = item["product_title"]
        product_sales[title] = {
            "product_title": title,
            "quantity_sold": int(item["quantity_sold"]),
            "revenue": Decimal(str(item["revenue"])),
        }

    raw_attribution = compute_attribution_intelligence(period_orders)

    return PeriodSnapshot(
        revenue=revenue,
        orders_count=orders_count,
        average_order_value=average_order_value,
        paid_orders_count=paid_orders_count,
        pending_orders_count=len(pending_orders),
        fulfilled_orders_count=fulfilled_orders_count,
        unfulfilled_orders_count=len(unfulfilled_orders),
        attribution_intelligence=raw_attribution,
        product_sales=product_sales,
        best_sellers=best_sellers,
    )


def _source_revenue_map(attribution: dict[str, Any]) -> dict[str, Decimal]:
    result: dict[str, Decimal] = {}
    for row in attribution.get("revenue_by_source", []):
        source = row.get("source") or UNKNOWN_SOURCE
        result[source] = Decimal(str(row.get("revenue", 0)))
    return result


def _source_orders_map(attribution: dict[str, Any]) -> dict[str, int]:
    result: dict[str, int] = {}
    for row in attribution.get("orders_by_source", []):
        source = row.get("source") or UNKNOWN_SOURCE
        result[source] = int(row.get("orders_count", 0))
    return result


def _build_source_delta_rows(
    current_map: dict[str, Decimal | int],
    previous_map: dict[str, Decimal | int],
    *,
    value_key: str,
) -> list[dict[str, Any]]:
    keys = set(current_map) | set(previous_map)
    rows: list[dict[str, Any]] = []
    for key in keys:
        current_val = current_map.get(key, 0)
        previous_val = previous_map.get(key, 0)
        comparison = compare_scalar(current_val, previous_val)
        rows.append(
            {
                "source": key,
                value_key: comparison["current"],
                "previous": comparison["previous"],
                "delta": comparison["delta"],
                "delta_percent": comparison["delta_percent"],
                "direction": comparison["direction"],
            }
        )
    rows.sort(key=lambda row: abs(Decimal(str(row["delta"]))), reverse=True)
    return rows


def _build_product_delta_rows(
    current_sales: dict[str, dict[str, Any]],
    previous_sales: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    titles = set(current_sales) | set(previous_sales)
    rows: list[dict[str, Any]] = []
    for title in titles:
        current_rev = Decimal(str(current_sales.get(title, {}).get("revenue", 0)))
        previous_rev = Decimal(str(previous_sales.get(title, {}).get("revenue", 0)))
        current_qty = int(current_sales.get(title, {}).get("quantity_sold", 0))
        previous_qty = int(previous_sales.get(title, {}).get("quantity_sold", 0))
        comparison = compare_scalar(current_rev, previous_rev)
        rows.append(
            {
                "product_title": title,
                "current_revenue": current_rev,
                "previous_revenue": comparison["previous"],
                "current_quantity": current_qty,
                "previous_quantity": previous_qty,
                "delta": comparison["delta"],
                "delta_percent": comparison["delta_percent"],
                "direction": comparison["direction"],
            }
        )
    rows.sort(key=lambda row: abs(Decimal(str(row["delta"]))), reverse=True)
    return rows


def build_period_comparison(
    current: ResolvedPeriod,
    previous: ResolvedPeriod,
    current_snapshot: PeriodSnapshot,
    previous_snapshot: PeriodSnapshot,
) -> dict[str, Any]:
    data_quality = "full" if previous_snapshot.orders_count > 0 else "limited"

    current_attr = current_snapshot.attribution_intelligence
    previous_attr = previous_snapshot.attribution_intelligence

    revenue_by_source_delta = _build_source_delta_rows(
        _source_revenue_map(current_attr),
        _source_revenue_map(previous_attr),
        value_key="revenue",
    )
    orders_by_source_delta = _build_source_delta_rows(
        _source_orders_map(current_attr),
        _source_orders_map(previous_attr),
        value_key="orders_count",
    )

    growing_sources = [
        row for row in revenue_by_source_delta if row["direction"] == "up" and row["delta"] > 0
    ][:5]
    declining_sources = [
        row for row in revenue_by_source_delta if row["direction"] == "down" and row["delta"] < 0
    ][:5]

    product_rows = _build_product_delta_rows(
        current_snapshot.product_sales,
        previous_snapshot.product_sales,
    )
    growing_products = [row for row in product_rows if row["direction"] == "up"][:5]
    declining_products = [row for row in product_rows if row["direction"] == "down"][:5]

    current_titles = set(current_snapshot.product_sales)
    previous_titles = set(previous_snapshot.product_sales)
    products_new = [
        current_snapshot.product_sales[title]
        for title in sorted(current_titles - previous_titles)
    ][:10]
    products_stalled = [
        previous_snapshot.product_sales[title]
        for title in sorted(previous_titles - current_titles)
    ][:10]

    unknown_revenue_delta = compare_scalar(
        Decimal(str(current_attr.get("unattributed_revenue", 0))),
        Decimal(str(previous_attr.get("unattributed_revenue", 0))),
    )
    tracking_quality_delta = compare_scalar(
        float(current_attr.get("tracking_quality_score") or 0),
        float(previous_attr.get("tracking_quality_score") or 0),
    )

    return {
        "current_period": current.to_dict(),
        "previous_period": previous.to_dict(),
        "data_quality": data_quality,
        "metrics": {
            "revenue": compare_scalar(current_snapshot.revenue, previous_snapshot.revenue),
            "orders": compare_scalar(
                current_snapshot.orders_count,
                previous_snapshot.orders_count,
            ),
            "average_order_value": compare_scalar(
                current_snapshot.average_order_value,
                previous_snapshot.average_order_value,
            ),
            "paid_orders": compare_scalar(
                current_snapshot.paid_orders_count,
                previous_snapshot.paid_orders_count,
            ),
            "pending_orders": compare_scalar(
                current_snapshot.pending_orders_count,
                previous_snapshot.pending_orders_count,
            ),
            "unfulfilled_orders": compare_scalar(
                current_snapshot.unfulfilled_orders_count,
                previous_snapshot.unfulfilled_orders_count,
            ),
        },
        "attribution": {
            "revenue_by_source_delta": revenue_by_source_delta[:20],
            "orders_by_source_delta": orders_by_source_delta[:20],
            "top_growing_sources": growing_sources,
            "top_declining_sources": declining_sources,
            "unknown_revenue_delta": unknown_revenue_delta,
            "tracking_quality_delta": tracking_quality_delta,
        },
        "products": {
            "top_growing_products": growing_products,
            "top_declining_products": declining_products,
            "products_new_in_current_period": products_new,
            "products_sold_previously_but_not_now": products_stalled,
        },
    }


def build_trend_diagnosis(comparison: dict[str, Any]) -> list[dict[str, str]]:
    insights: list[dict[str, str]] = []
    metrics = comparison.get("metrics", {})
    attribution = comparison.get("attribution", {})
    products = comparison.get("products", {})

    revenue = metrics.get("revenue", {})
    orders = metrics.get("orders", {})
    aov = metrics.get("average_order_value", {})
    pending = metrics.get("pending_orders", {})

    if revenue.get("direction") == "up" and revenue.get("delta", 0) > 0:
        insights.append(
            {
                "message": "Revenue in crescita rispetto al periodo precedente.",
                "severity": "opportunity",
            }
        )

    if orders.get("direction") == "down" and aov.get("direction") == "up":
        insights.append(
            {
                "message": "Ordini in calo ma AOV in crescita.",
                "severity": "info",
            }
        )

    tracking = attribution.get("tracking_quality_delta", {})
    if tracking.get("direction") == "down":
        insights.append(
            {
                "message": "Tracking quality peggiorata rispetto al periodo precedente.",
                "severity": "warning",
            }
        )

    unknown = attribution.get("unknown_revenue_delta", {})
    if unknown.get("direction") == "up" and unknown.get("delta", 0) > 0:
        insights.append(
            {
                "message": "Source Unknown in aumento rispetto al periodo precedente.",
                "severity": "warning",
            }
        )

    declining = products.get("top_declining_products") or []
    if declining:
        title = declining[0].get("product_title", "Un prodotto")
        insights.append(
            {
                "message": f"{title} risulta in calo rispetto al periodo precedente.",
                "severity": "warning",
            }
        )

    new_products = products.get("products_new_in_current_period") or []
    best_seller_titles = {
        row.get("product_title")
        for row in (products.get("top_growing_products") or [])
    }
    for product in new_products:
        title = product.get("product_title")
        if title in best_seller_titles:
            insights.append(
                {
                    "message": f"{title} è entrato tra i best seller nel periodo corrente.",
                    "severity": "opportunity",
                }
            )
            break

    if pending.get("direction") == "up" and pending.get("delta", 0) > 0:
        insights.append(
            {
                "message": "Ordini pending aumentati rispetto al periodo precedente.",
                "severity": "warning",
            }
        )

    return insights[:5]
