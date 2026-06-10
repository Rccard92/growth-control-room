from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shopify import ShopifyDailyMetric, ShopifyOrder, ShopifyProduct, ShopifyStore

LOW_STOCK_THRESHOLD = 10
ACTIVE_STATUS = "ACTIVE"
SEO_MIN_LENGTH = 20
PENDING_STATUSES = {"PENDING", "AUTHORIZED", "PARTIALLY_PAID"}
PAID_STATUSES = {"PAID", "PARTIALLY_REFUNDED", "REFUNDED"}


def _is_active_status(status: str | None) -> bool:
    return (status or "").upper() == ACTIVE_STATUS


def _parse_decimal(value: str | None) -> Decimal:
    if not value:
        return Decimal("0")
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal("0")


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


def _parse_line_items(orders: list[ShopifyOrder]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for order in orders:
        payload = order.raw_payload or {}
        line_items = (payload.get("lineItems") or {}).get("edges") or []
        for edge in line_items:
            node = edge.get("node") or {}
            product = node.get("product") or {}
            product_gid = product.get("id")
            if not product_gid:
                continue
            qty = int(node.get("quantity") or 0)
            discounted = (node.get("discountedTotalSet") or {}).get("shopMoney") or {}
            unit = (node.get("originalUnitPriceSet") or {}).get("shopMoney") or {}
            line_revenue = _parse_decimal(discounted.get("amount"))
            if line_revenue == 0 and unit.get("amount"):
                line_revenue = _parse_decimal(unit.get("amount")) * qty
            items.append(
                {
                    "product_gid": product_gid,
                    "product_title": product.get("title") or node.get("title") or "Unknown",
                    "quantity": qty,
                    "revenue": line_revenue,
                }
            )
    return items


def _compute_best_sellers(line_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not line_items:
        return []
    qty_counter: Counter[str] = Counter()
    revenue_counter: defaultdict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    titles: dict[str, str] = {}
    for item in line_items:
        gid = item["product_gid"]
        qty_counter[gid] += item["quantity"]
        revenue_counter[gid] += item["revenue"]
        titles[gid] = item["product_title"]
    ranked = sorted(qty_counter.items(), key=lambda x: x[1], reverse=True)[:10]
    return [
        {
            "product_title": titles.get(gid, gid),
            "quantity_sold": qty,
            "revenue": revenue_counter[gid],
        }
        for gid, qty in ranked
    ]


def _compute_stale_products(
    products: list[ShopifyProduct],
    sold_product_gids: set[str],
) -> list[dict[str, Any]]:
    stale: list[dict[str, Any]] = []
    for product in products:
        if not _is_active_status(product.status):
            continue
        if product.shopify_gid not in sold_product_gids:
            stale.append(_product_to_dict(product))
    return stale[:20]


def _compute_seo_opportunities(products: list[ShopifyProduct]) -> list[dict[str, Any]]:
    opportunities: list[dict[str, Any]] = []
    for product in products:
        if not _is_active_status(product.status):
            continue
        title = (product.seo_title or "").strip()
        description = (product.seo_description or "").strip()
        if not title:
            opportunities.append(
                {
                    "product_title": product.title,
                    "issue": "Missing SEO meta title",
                    "priority": "high",
                }
            )
        elif len(title) < SEO_MIN_LENGTH:
            opportunities.append(
                {
                    "product_title": product.title,
                    "issue": "SEO meta title is too short",
                    "priority": "medium",
                }
            )
        if not description:
            opportunities.append(
                {
                    "product_title": product.title,
                    "issue": "Missing SEO meta description",
                    "priority": "high",
                }
            )
        elif len(description) < SEO_MIN_LENGTH:
            opportunities.append(
                {
                    "product_title": product.title,
                    "issue": "SEO meta description is too short",
                    "priority": "medium",
                }
            )
    return opportunities[:20]


def _build_insights(summary: dict[str, Any], seo_count: int) -> list[dict[str, str]]:
    insights: list[dict[str, str]] = []

    if summary.get("out_of_stock_count", 0) > 0:
        insights.append(
            {
                "message": f"{summary['out_of_stock_count']} active products are out of stock.",
                "severity": "critical",
            }
        )
    if summary.get("low_stock_count", 0) > 0:
        insights.append(
            {
                "message": f"{summary['low_stock_count']} active products have low inventory (≤{LOW_STOCK_THRESHOLD}).",
                "severity": "warning",
            }
        )
    if summary.get("draft_products_count", 0) >= 5:
        insights.append(
            {
                "message": f"{summary['draft_products_count']} products are still in draft status.",
                "severity": "warning",
            }
        )
    if summary.get("pending_orders_count", 0) > 0:
        insights.append(
            {
                "message": f"{summary['pending_orders_count']} orders are pending payment or fulfillment.",
                "severity": "warning",
            }
        )
    if seo_count >= 3:
        insights.append(
            {
                "message": f"{seo_count} products have incomplete or weak SEO metadata.",
                "severity": "opportunity",
            }
        )
    last_sync = summary.get("last_sync_at")
    if last_sync is None:
        insights.append(
            {
                "message": "No sync recorded yet. Run a sync to refresh store data.",
                "severity": "info",
            }
        )
    elif isinstance(last_sync, datetime):
        if last_sync.tzinfo is None:
            last_sync = last_sync.replace(tzinfo=UTC)
        if datetime.now(UTC) - last_sync > timedelta(hours=24):
            insights.append(
                {
                    "message": "Last sync is older than 24 hours. Consider syncing again.",
                    "severity": "info",
                }
            )

    return insights[:5]


async def build_dashboard(
    store: ShopifyStore,
    session: AsyncSession,
) -> dict[str, Any]:
    empty: dict[str, Any] = {
        "summary": {
            "revenue": Decimal("0"),
            "orders_count": 0,
            "average_order_value": Decimal("0"),
            "products_count": 0,
            "active_products_count": 0,
            "draft_products_count": 0,
            "out_of_stock_count": 0,
            "low_stock_count": 0,
            "pending_orders_count": 0,
            "paid_orders_count": 0,
            "last_sync_at": store.last_sync_at,
            "shop_domain": store.shop_domain,
        },
        "recent_orders": [],
        "products": [],
        "low_stock_products": [],
        "out_of_stock_products": [],
        "best_sellers": [],
        "stale_products": [],
        "seo_opportunities": [],
        "insights": [],
    }

    try:
        products_result = await session.execute(
            select(ShopifyProduct)
            .where(ShopifyProduct.shopify_store_id == store.id)
            .order_by(ShopifyProduct.title.asc())
        )
        products = list(products_result.scalars().all())
    except Exception:
        products = []

    try:
        orders_result = await session.execute(
            select(ShopifyOrder)
            .where(ShopifyOrder.shopify_store_id == store.id)
            .order_by(ShopifyOrder.created_at_shopify.desc().nullslast())
        )
        orders = list(orders_result.scalars().all())
    except Exception:
        orders = []

    products_count = len(products)
    active_products = [p for p in products if _is_active_status(p.status)]
    draft_products = [
        p for p in products if (p.status or "").upper() == "DRAFT"
    ]

    out_of_stock = [
        p
        for p in active_products
        if p.total_inventory is not None and p.total_inventory == 0
    ]
    low_stock = [
        p
        for p in active_products
        if p.total_inventory is not None
        and 0 < p.total_inventory <= LOW_STOCK_THRESHOLD
    ]

    pending_orders_count = sum(
        1
        for o in orders
        if (o.financial_status or "").upper() in PENDING_STATUSES
        or (o.fulfillment_status or "").upper() in {"UNFULFILLED", "PARTIAL"}
    )
    paid_orders_count = sum(
        1 for o in orders if (o.financial_status or "").upper() in PAID_STATUSES
    )

    revenue = Decimal("0")
    orders_count = 0
    try:
        metrics_result = await session.execute(
            select(
                func.coalesce(func.sum(ShopifyDailyMetric.gross_sales), 0),
                func.coalesce(func.sum(ShopifyDailyMetric.orders_count), 0),
            ).where(ShopifyDailyMetric.shopify_store_id == store.id)
        )
        revenue, orders_count = metrics_result.one()
        revenue = Decimal(str(revenue))
        orders_count = int(orders_count)
    except Exception:
        revenue = Decimal("0")
        orders_count = 0

    if revenue == 0 and orders_count == 0:
        try:
            revenue = sum((o.total_price for o in orders), Decimal("0"))
            orders_count = len(orders)
        except Exception:
            revenue = Decimal("0")
            orders_count = 0

    average_order_value = revenue / orders_count if orders_count else Decimal("0")

    recent_orders: list[dict[str, Any]] = []
    try:
        for order in orders[:10]:
            recent_orders.append(
                {
                    "order_name": order.order_name,
                    "created_at_shopify": order.created_at_shopify,
                    "financial_status": order.financial_status,
                    "fulfillment_status": order.fulfillment_status,
                    "total_price": order.total_price,
                    "currency": order.currency,
                }
            )
    except Exception:
        recent_orders = []

    product_rows: list[dict[str, Any]] = []
    try:
        product_rows = [_product_to_dict(p) for p in products[:50]]
    except Exception:
        product_rows = []

    low_stock_rows = [_product_to_dict(p) for p in low_stock[:20]]
    out_of_stock_rows = [_product_to_dict(p) for p in out_of_stock[:20]]

    best_sellers: list[dict[str, Any]] = []
    stale_products: list[dict[str, Any]] = []
    try:
        line_items = _parse_line_items(orders)
        best_sellers = _compute_best_sellers(line_items)
        sold_gids = {item["product_gid"] for item in line_items}
        stale_products = _compute_stale_products(products, sold_gids)
    except Exception:
        best_sellers = []
        stale_products = []

    seo_opportunities: list[dict[str, Any]] = []
    try:
        seo_opportunities = _compute_seo_opportunities(products)
    except Exception:
        seo_opportunities = []

    summary = {
        "revenue": revenue,
        "orders_count": orders_count,
        "average_order_value": average_order_value,
        "products_count": products_count,
        "active_products_count": len(active_products),
        "draft_products_count": len(draft_products),
        "out_of_stock_count": len(out_of_stock),
        "low_stock_count": len(low_stock),
        "pending_orders_count": pending_orders_count,
        "paid_orders_count": paid_orders_count,
        "last_sync_at": store.last_sync_at,
        "shop_domain": store.shop_domain,
    }

    insights = _build_insights(summary, len(seo_opportunities))

    return {
        "summary": summary,
        "recent_orders": recent_orders,
        "products": product_rows,
        "low_stock_products": low_stock_rows,
        "out_of_stock_products": out_of_stock_rows,
        "best_sellers": best_sellers,
        "stale_products": stale_products,
        "seo_opportunities": seo_opportunities,
        "insights": insights,
    }
