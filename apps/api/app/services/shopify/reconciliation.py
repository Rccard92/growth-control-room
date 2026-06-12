from __future__ import annotations

from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shopify import (
    ShopifyOrder,
    ShopifyOrderLineItem,
    ShopifyOrderRefund,
    ShopifyStore,
)
from app.services.shopify.period import ResolvedPeriod

PENDING_STATUSES = {"PENDING", "AUTHORIZED", "PARTIALLY_PAID"}
PAID_STATUSES = {"PAID", "PARTIALLY_REFUNDED", "REFUNDED"}
CANCELLED_STATUSES = {"VOIDED"}
FULFILLED_STATUSES = {"FULFILLED"}
TEST_SOURCE_NAMES = {"shopify_draft_order", "test", "pos"}


def _normalize_status(status: str | None) -> str:
    return (status or "").upper().strip()


def _is_valid_placed_order(order: ShopifyOrder) -> bool:
    source = (order.source_name or "").lower().strip()
    if source in TEST_SOURCE_NAMES:
        return False
    if "test" in source and source != "pos":
        return False
    return order.created_at_shopify is not None


async def fetch_placed_orders(
    session: AsyncSession,
    store_id: Any,
    period: ResolvedPeriod,
) -> list[ShopifyOrder]:
    result = await session.execute(
        select(ShopifyOrder)
        .where(
            ShopifyOrder.shopify_store_id == store_id,
            ShopifyOrder.created_at_shopify.is_not(None),
            ShopifyOrder.created_at_shopify >= period.start_at,
            ShopifyOrder.created_at_shopify < period.end_at_exclusive,
        )
        .order_by(ShopifyOrder.created_at_shopify.desc())
    )
    return [order for order in result.scalars().all() if _is_valid_placed_order(order)]


async def fetch_refunds_in_period(
    session: AsyncSession,
    store_id: Any,
    period: ResolvedPeriod,
) -> list[ShopifyOrderRefund]:
    result = await session.execute(
        select(ShopifyOrderRefund)
        .where(
            ShopifyOrderRefund.shopify_store_id == store_id,
            ShopifyOrderRefund.refund_created_at.is_not(None),
            ShopifyOrderRefund.refund_created_at >= period.start_at,
            ShopifyOrderRefund.refund_created_at < period.end_at_exclusive,
        )
        .order_by(ShopifyOrderRefund.refund_created_at.desc())
    )
    return list(result.scalars().all())


async def _load_line_items_by_order(
    session: AsyncSession,
    store_id: Any,
    order_ids: list[Any],
) -> dict[Any, list[ShopifyOrderLineItem]]:
    if not order_ids:
        return {}

    result = await session.execute(
        select(ShopifyOrderLineItem).where(
            ShopifyOrderLineItem.shopify_store_id == store_id,
            ShopifyOrderLineItem.order_id.in_(order_ids),
        )
    )
    grouped: dict[Any, list[ShopifyOrderLineItem]] = defaultdict(list)
    for item in result.scalars().all():
        grouped[item.order_id].append(item)
    return grouped


def _count_orders_by_status(orders: list[ShopifyOrder]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for order in orders:
        status = _normalize_status(order.financial_status) or "UNKNOWN"
        counts[status] += 1
    return dict(counts)


def _count_orders_by_fulfillment(orders: list[ShopifyOrder]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for order in orders:
        status = _normalize_status(order.fulfillment_status) or "UNKNOWN"
        counts[status] += 1
    return dict(counts)


def _classify_order_buckets(orders: list[ShopifyOrder]) -> dict[str, int]:
    total = len(orders)
    paid = 0
    pending = 0
    cancelled = 0
    unpaid = 0

    for order in orders:
        status = _normalize_status(order.financial_status)
        if status in PAID_STATUSES:
            paid += 1
        if status in PENDING_STATUSES:
            pending += 1
        if status in CANCELLED_STATUSES:
            cancelled += 1
        if status not in PAID_STATUSES and status not in PENDING_STATUSES and status not in CANCELLED_STATUSES:
            unpaid += 1

    return {
        "total": total,
        "paid": paid,
        "pending": pending,
        "cancelled": cancelled,
        "unpaid": unpaid,
    }


def _compute_sales_breakdown(
    placed_orders: list[ShopifyOrder],
    line_items_by_order: dict[Any, list[ShopifyOrderLineItem]],
    refunds_in_period: list[ShopifyOrderRefund],
) -> dict[str, Decimal]:
    gross_sales = Decimal("0")
    discounts = Decimal("0")
    shipping = Decimal("0")
    taxes = Decimal("0")
    current_total_sum = Decimal("0")
    has_tax_data = False

    for order in placed_orders:
        shipping += order.shipping_price or Decimal("0")
        if order.total_tax is not None:
            taxes += order.total_tax
            has_tax_data = True
        current_total_sum += order.current_total_price or order.total_price or Decimal("0")

        items = line_items_by_order.get(order.id, [])
        order_gross = Decimal("0")
        line_discounts = Decimal("0")

        for item in items:
            original = item.original_total or item.discounted_total or Decimal("0")
            discounted = item.discounted_total or original
            order_gross += original
            line_discounts += max(original - discounted, Decimal("0"))

        gross_sales += order_gross

        if order.total_discounts and order.total_discounts > 0:
            discounts += order.total_discounts
        else:
            discounts += line_discounts

    sales_reversals = sum((refund.amount for refund in refunds_in_period), Decimal("0"))
    duties = Decimal("0")
    fees = Decimal("0")
    total_sales = gross_sales - discounts - sales_reversals + taxes + shipping + duties + fees

    return {
        "gross_sales": gross_sales,
        "discounts": discounts,
        "sales_reversals": sales_reversals,
        "returns": sales_reversals,
        "shipping": shipping,
        "taxes": taxes,
        "duties": duties,
        "fees": fees,
        "total_sales": total_sales,
        "current_total_sum": current_total_sum,
        "_has_tax_data": has_tax_data,
    }


def _detect_refund_gaps(
    placed_orders: list[ShopifyOrder],
    refunds_in_period: list[ShopifyOrderRefund],
) -> bool:
    refunds_by_order = sum((refund.amount for refund in refunds_in_period), Decimal("0"))

    orders_with_refunds = [
        order
        for order in placed_orders
        if (order.refund_count or 0) > 0 or (order.refund_total or Decimal("0")) > 0
    ]
    if not orders_with_refunds and refunds_by_order == 0:
        return False

    historical_refund_total = sum(
        (order.refund_total or Decimal("0") for order in placed_orders),
        Decimal("0"),
    )
    if historical_refund_total > refunds_by_order + Decimal("0.01"):
        return True

    for order in placed_orders:
        payload_refunds = ((order.raw_payload or {}).get("refunds") or {}).get("nodes") or []
        if payload_refunds and (order.refund_count or 0) == 0:
            return True

    return False


def _build_data_quality(
    *,
    breakdown: dict[str, Decimal],
    placed_orders: list[ShopifyOrder],
    refunds_in_period: list[ShopifyOrderRefund],
    refund_gap: bool,
) -> dict[str, Any]:
    warnings: list[str] = []
    status = "ok"

    if placed_orders and not breakdown["_has_tax_data"]:
        warnings.append("Taxes non disponibili: calcolate a 0.")
        status = "limited"

    warnings.append("Duties/fees non disponibili: calcolate a 0.")
    if status == "ok":
        status = "limited"

    if refund_gap:
        warnings.append(
            "Alcuni reversal potrebbero non essere presenti se riferiti a ordini "
            "fuori dallo storico sincronizzato."
        )
        status = "warning"

    if placed_orders and not refunds_in_period:
        payload_refund_count = 0
        for order in placed_orders:
            payload_refund_count += len(
                ((order.raw_payload or {}).get("refunds") or {}).get("nodes") or []
            )
        if payload_refund_count > 0:
            warnings.append(
                "Refund rilevati negli ordini ma non ancora sincronizzati con importo. "
                "Esegui un nuovo sync."
            )
            status = "warning" if status != "warning" else status

    current_total_sum = breakdown["current_total_sum"]
    total_sales = breakdown["total_sales"]
    if total_sales > 0:
        delta_ratio = abs(current_total_sum - total_sales) / total_sales
        if delta_ratio > Decimal("0.05"):
            warnings.append(
                "La somma dei totali ordine correnti differisce in modo rilevante "
                "dal total sales Shopify-like."
            )
            status = "warning"

    return {"status": status, "warnings": warnings}


def _serialize_breakdown(breakdown: dict[str, Decimal]) -> dict[str, Decimal]:
    return {
        key: breakdown[key]
        for key in (
            "gross_sales",
            "discounts",
            "sales_reversals",
            "returns",
            "shipping",
            "taxes",
            "duties",
            "fees",
            "total_sales",
            "current_total_sum",
        )
    }


async def compute_reconciliation(
    session: AsyncSession,
    store: ShopifyStore,
    period: ResolvedPeriod,
) -> dict[str, Any]:
    placed_orders = await fetch_placed_orders(session, store.id, period)
    refunds_in_period = await fetch_refunds_in_period(session, store.id, period)
    line_items_by_order = await _load_line_items_by_order(
        session,
        store.id,
        [order.id for order in placed_orders],
    )

    breakdown = _compute_sales_breakdown(placed_orders, line_items_by_order, refunds_in_period)
    refund_gap = _detect_refund_gaps(placed_orders, refunds_in_period)
    data_quality = _build_data_quality(
        breakdown=breakdown,
        placed_orders=placed_orders,
        refunds_in_period=refunds_in_period,
        refund_gap=refund_gap,
    )

    return {
        "metric_mode": "shopify_like_local",
        "period": period.to_dict(),
        "orders": _classify_order_buckets(placed_orders),
        "sales_breakdown": _serialize_breakdown(breakdown),
        "data_quality": data_quality,
        "_placed_orders": placed_orders,
        "_refunds_in_period": refunds_in_period,
    }


def build_reconciliation_diagnosis(
    reconciliation: dict[str, Any],
    *,
    last_sync_at: datetime | None,
) -> list[dict[str, str]]:
    insights: list[dict[str, str]] = []
    breakdown = reconciliation.get("sales_breakdown", {})
    data_quality = reconciliation.get("data_quality", {})
    sales_reversals = Decimal(str(breakdown.get("sales_reversals", 0)))

    if sales_reversals > 0:
        insights.append(
            {
                "message": (
                    f"Resi/rimborsi nel periodo per {sales_reversals:.2f} "
                    "(sales reversals)."
                ),
                "severity": "warning",
            }
        )

    current_total_sum = Decimal(str(breakdown.get("current_total_sum", 0)))
    total_sales = Decimal(str(breakdown.get("total_sales", 0)))
    if total_sales > 0:
        delta_ratio = abs(current_total_sum - total_sales) / total_sales
        if delta_ratio > Decimal("0.05"):
            insights.append(
                {
                    "message": (
                        "I totali ordine correnti differiscono dal total sales "
                        "Shopify-like nel periodo selezionato."
                    ),
                    "severity": "info",
                }
            )

    if data_quality.get("status") in {"limited", "warning"}:
        warnings = data_quality.get("warnings") or []
        if warnings:
            insights.append(
                {
                    "message": warnings[0],
                    "severity": "warning" if data_quality["status"] == "warning" else "info",
                }
            )

    sync_dt = last_sync_at
    if sync_dt is not None and sync_dt.tzinfo is None:
        sync_dt = sync_dt.replace(tzinfo=UTC)
    if sync_dt is None:
        insights.append(
            {
                "message": "Nessuna sincronizzazione registrata: i KPI potrebbero essere incompleti.",
                "severity": "warning",
            }
        )
    elif datetime.now(UTC) - sync_dt > timedelta(hours=24):
        insights.append(
            {
                "message": "Ultimo sync oltre 24 ore fa: i dati potrebbero non essere aggiornati.",
                "severity": "warning",
            }
        )

    return insights


async def build_reconciliation_debug(
    session: AsyncSession,
    store: ShopifyStore,
    period: ResolvedPeriod,
) -> dict[str, Any]:
    reconciliation = await compute_reconciliation(session, store, period)
    placed_orders: list[ShopifyOrder] = reconciliation.pop("_placed_orders")
    refunds_in_period: list[ShopifyOrderRefund] = reconciliation.pop("_refunds_in_period")

    order_ids = {refund.order_id for refund in refunds_in_period}
    orders_by_id = {order.id: order for order in placed_orders}

    missing_order_ids = order_ids - set(orders_by_id.keys())
    if missing_order_ids:
        extra_orders_result = await session.execute(
            select(ShopifyOrder).where(
                ShopifyOrder.shopify_store_id == store.id,
                ShopifyOrder.id.in_(missing_order_ids),
            )
        )
        for order in extra_orders_result.scalars().all():
            orders_by_id[order.id] = order

    refunds_payload = []
    for refund in refunds_in_period[:50]:
        order = orders_by_id.get(refund.order_id)
        refunds_payload.append(
            {
                "refund_created_at": refund.refund_created_at,
                "amount": refund.amount,
                "currency": refund.currency,
                "order_name": order.order_name if order else None,
            }
        )

    sample_orders = []
    for order in placed_orders[:20]:
        sample_orders.append(
            {
                "order_name": order.order_name,
                "created_at": order.created_at_shopify,
                "processed_at": order.processed_at,
                "financial_status": order.financial_status,
                "total_price": order.total_price,
                "current_total_price": order.current_total_price or order.total_price,
                "refund_total": order.refund_total,
            }
        )

    debug_reconciliation = {k: v for k, v in reconciliation.items() if not k.startswith("_")}

    return {
        "period": period.to_dict(),
        "last_sync_at": store.last_sync_at,
        "metric_mode": debug_reconciliation["metric_mode"],
        "order_count_by_financial_status": _count_orders_by_status(placed_orders),
        "order_count_by_fulfillment_status": _count_orders_by_fulfillment(placed_orders),
        "reconciliation": debug_reconciliation,
        "sales_breakdown": debug_reconciliation["sales_breakdown"],
        "refunds_in_period": refunds_payload,
        "sample_orders": sample_orders,
    }
