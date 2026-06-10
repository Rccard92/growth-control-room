from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shopify import ShopifyDailyMetric, ShopifyOrder, ShopifyProduct, ShopifyStore
from app.services.shopify.attribution import (
    build_attribution_alerts,
    build_marketing_report_availability,
    compute_attribution_intelligence,
)

LOW_STOCK_THRESHOLD = 10
HIGH_STOCK_THRESHOLD = 20
LOW_SALES_THRESHOLD = 2
ACTIVE_STATUS = "ACTIVE"
SEO_MIN_LENGTH = 20
PENDING_STATUSES = {"PENDING", "AUTHORIZED", "PARTIALLY_PAID"}
PAID_STATUSES = {"PAID", "PARTIALLY_REFUNDED", "REFUNDED"}
FULFILLED_STATUSES = {"FULFILLED"}
UNFULFILLED_STATUSES = {"UNFULFILLED", "PARTIAL", "IN_PROGRESS", "ON_HOLD", "SCHEDULED"}
SEVERITY_ORDER = {"critical": 0, "warning": 1, "opportunity": 2, "info": 3}


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


def _order_to_dict(order: ShopifyOrder) -> dict[str, Any]:
    return {
        "order_name": order.order_name,
        "created_at_shopify": order.created_at_shopify,
        "financial_status": order.financial_status,
        "fulfillment_status": order.fulfillment_status,
        "total_price": order.total_price,
        "currency": order.currency,
    }


def _iter_line_item_nodes(payload: dict[str, Any]) -> list[dict[str, Any]]:
    line_items = payload.get("lineItems") or {}
    nodes = line_items.get("nodes") or []
    if nodes:
        return [n for n in nodes if isinstance(n, dict)]
    edges = line_items.get("edges") or []
    return [edge.get("node") for edge in edges if edge.get("node")]


def _parse_line_items(orders: list[ShopifyOrder]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for order in orders:
        payload = order.raw_payload or {}
        for node in _iter_line_item_nodes(payload):
            product = node.get("product") or {}
            variant = node.get("variant") or {}
            product_gid = product.get("id")
            if not product_gid:
                continue
            qty = int(node.get("quantity") or 0)
            unit = (node.get("originalUnitPriceSet") or {}).get("shopMoney") or {}
            original_total = (node.get("originalTotalSet") or {}).get("shopMoney") or {}
            discounted = (node.get("discountedTotalSet") or {}).get("shopMoney") or {}
            discount = (node.get("totalDiscountSet") or {}).get("shopMoney") or {}
            line_revenue = _parse_decimal(discounted.get("amount"))
            if line_revenue == 0:
                line_revenue = _parse_decimal(original_total.get("amount"))
            if line_revenue == 0 and unit.get("amount"):
                line_revenue = _parse_decimal(unit.get("amount")) * qty
            items.append(
                {
                    "product_gid": product_gid,
                    "variant_id": variant.get("id"),
                    "product_title": product.get("title") or node.get("title") or "Unknown",
                    "sku": node.get("sku") or variant.get("sku"),
                    "quantity": qty,
                    "price": _parse_decimal(unit.get("amount") or original_total.get("amount")),
                    "total_discount": _parse_decimal(discount.get("amount")),
                    "vendor": product.get("vendor") or node.get("vendor"),
                    "product_type": product.get("productType"),
                    "revenue": line_revenue,
                }
            )
    return items


def _product_lookup(products: list[ShopifyProduct]) -> dict[str, ShopifyProduct]:
    return {p.shopify_gid: p for p in products}


def _compute_best_sellers(
    line_items: list[dict[str, Any]],
    products_by_gid: dict[str, ShopifyProduct],
) -> list[dict[str, Any]]:
    if not line_items:
        return []
    qty_counter: Counter[str] = Counter()
    revenue_counter: defaultdict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    titles: dict[str, str] = {}
    skus: dict[str, str | None] = {}
    for item in line_items:
        gid = item["product_gid"]
        qty_counter[gid] += item["quantity"]
        revenue_counter[gid] += item["revenue"]
        titles[gid] = item["product_title"]
        if item.get("sku"):
            skus[gid] = item["sku"]
    ranked = sorted(qty_counter.items(), key=lambda x: x[1], reverse=True)[:10]
    result: list[dict[str, Any]] = []
    for gid, qty in ranked:
        product = products_by_gid.get(gid)
        result.append(
            {
                "product_title": titles.get(gid, gid),
                "sku": skus.get(gid) or (product.handle if product else None),
                "quantity_sold": qty,
                "revenue": revenue_counter[gid],
                "current_inventory": product.total_inventory if product else None,
                "status": product.status if product else None,
            }
        )
    return result


def _compute_no_sales_products(
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


def _compute_high_stock_low_sales(
    products: list[ShopifyProduct],
    qty_by_gid: Counter[str],
) -> list[dict[str, Any]]:
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
                "issue": f"Stock alto ({inv} unità) con vendite basse ({sold} negli ordini sincronizzati)",
            }
        )
    return result[:15]


def _compute_seo_section(products: list[ShopifyProduct]) -> dict[str, Any]:
    missing_title: list[dict[str, Any]] = []
    missing_description: list[dict[str, Any]] = []
    missing_both: list[dict[str, Any]] = []
    opportunities: list[dict[str, Any]] = []

    for product in products:
        if not _is_active_status(product.status):
            continue
        title = (product.seo_title or "").strip()
        description = (product.seo_description or "").strip()
        row = _product_to_dict(product)

        if not title and not description:
            missing_both.append(row)
            opportunities.append(
                {
                    "product_title": product.title,
                    "issue": "Meta title e description mancanti",
                    "priority": "high",
                }
            )
        elif not title:
            missing_title.append(row)
            opportunities.append(
                {
                    "product_title": product.title,
                    "issue": "Meta title mancante",
                    "priority": "high",
                }
            )
        elif not description:
            missing_description.append(row)
            opportunities.append(
                {
                    "product_title": product.title,
                    "issue": "Meta description mancante",
                    "priority": "high",
                }
            )
        elif len(title) < SEO_MIN_LENGTH:
            opportunities.append(
                {
                    "product_title": product.title,
                    "issue": "Meta title troppo corto",
                    "priority": "medium",
                }
            )
        elif len(description) < SEO_MIN_LENGTH:
            opportunities.append(
                {
                    "product_title": product.title,
                    "issue": "Meta description troppo corta",
                    "priority": "medium",
                }
            )

    return {
        "products_missing_meta_title": missing_title[:15],
        "products_missing_meta_description": missing_description[:15],
        "products_missing_both": missing_both[:15],
        "seo_opportunities": opportunities[:20],
    }


def _build_alerts(
    products: list[ShopifyProduct],
    orders: list[ShopifyOrder],
    sold_product_gids: set[str],
    has_line_items: bool,
    last_sync_at: datetime | None,
    attribution_alerts: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []

    for product in products:
        if not _is_active_status(product.status):
            continue
        inv = product.total_inventory
        if inv is not None and inv == 0:
            alerts.append(
                {
                    "id": f"oos-{product.shopify_gid}",
                    "severity": "critical",
                    "title": "Prodotto out of stock",
                    "description": f"{product.title} è attivo ma senza scorte.",
                    "entity_type": "inventory",
                    "entity_id": product.shopify_gid,
                    "action_label": "Verifica inventario",
                }
            )
        elif inv is not None and 0 < inv <= LOW_STOCK_THRESHOLD:
            alerts.append(
                {
                    "id": f"low-{product.shopify_gid}",
                    "severity": "warning",
                    "title": "Scorte basse",
                    "description": f"{product.title} ha solo {inv} unità disponibili.",
                    "entity_type": "inventory",
                    "entity_id": product.shopify_gid,
                    "action_label": "Rifornisci",
                }
            )

    for order in orders:
        fin = (order.financial_status or "").upper()
        if fin in PENDING_STATUSES:
            alerts.append(
                {
                    "id": f"pending-{order.shopify_gid}",
                    "severity": "warning",
                    "title": "Ordine pending",
                    "description": f"Ordine {order.order_name or order.shopify_gid} in attesa di pagamento.",
                    "entity_type": "order",
                    "entity_id": order.shopify_gid,
                    "action_label": "Controlla ordine",
                }
            )

    for product in products:
        if not _is_active_status(product.status):
            continue
        if product.shopify_gid not in sold_product_gids:
            alerts.append(
                {
                    "id": f"nosales-{product.shopify_gid}",
                    "severity": "opportunity",
                    "title": "Prodotto senza vendite",
                    "description": f"{product.title} non compare negli ordini sincronizzati.",
                    "entity_type": "product",
                    "entity_id": product.shopify_gid,
                    "action_label": "Valuta promozione",
                }
            )

    for product in products:
        if not _is_active_status(product.status):
            continue
        if not (product.seo_title or "").strip() or not (product.seo_description or "").strip():
            alerts.append(
                {
                    "id": f"seo-{product.shopify_gid}",
                    "severity": "opportunity",
                    "title": "SEO incompleto",
                    "description": f"{product.title} ha meta title o description mancanti.",
                    "entity_type": "seo",
                    "entity_id": product.shopify_gid,
                    "action_label": "Completa SEO",
                }
            )

    sync_dt = last_sync_at
    if sync_dt is not None and sync_dt.tzinfo is None:
        sync_dt = sync_dt.replace(tzinfo=UTC)
    if sync_dt is None:
        alerts.append(
            {
                "id": "sync-never",
                "severity": "warning",
                "title": "Sync non eseguito",
                "description": "Nessuna sincronizzazione registrata. Esegui un sync per aggiornare i dati.",
                "entity_type": "sync",
                "entity_id": None,
                "action_label": "Sincronizza",
            }
        )
    elif datetime.now(UTC) - sync_dt > timedelta(hours=24):
        alerts.append(
            {
                "id": "sync-stale",
                "severity": "warning",
                "title": "Dati non aggiornati",
                "description": "Ultimo sync oltre 24 ore fa. I dati potrebbero non essere aggiornati.",
                "entity_type": "sync",
                "entity_id": None,
                "action_label": "Sincronizza",
            }
        )

    if orders and not has_line_items:
        alerts.append(
            {
                "id": "line-items-missing",
                "severity": "info",
                "title": "Line items non disponibili",
                "description": "Gli ordini sincronizzati non contengono line items. Esegui un nuovo sync.",
                "entity_type": "sync",
                "entity_id": None,
                "action_label": "Sincronizza",
            }
        )

    if attribution_alerts:
        alerts.extend(attribution_alerts)

    alerts.sort(key=lambda a: SEVERITY_ORDER.get(a["severity"], 99))
    return alerts[:50]


def _build_daily_diagnosis(
    summary: dict[str, Any],
    attribution_intelligence: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    diagnosis: list[dict[str, str]] = []

    oos = summary.get("out_of_stock_count", 0)
    if oos > 0:
        diagnosis.append(
            {
                "message": f"{oos} prodotti attivi sono senza stock.",
                "severity": "critical",
            }
        )

    no_sales = summary.get("products_without_sales_count", 0)
    if no_sales > 0:
        diagnosis.append(
            {
                "message": f"{no_sales} prodotti attivi non compaiono negli ordini sincronizzati.",
                "severity": "opportunity",
            }
        )

    pending = summary.get("pending_orders_count", 0)
    if pending > 0:
        diagnosis.append(
            {
                "message": f"{pending} ordini risultano pending.",
                "severity": "warning",
            }
        )

    seo = summary.get("seo_issues_count", 0)
    if seo > 0:
        diagnosis.append(
            {
                "message": f"{seo} prodotti hanno dati SEO incompleti.",
                "severity": "opportunity",
            }
        )

    low = summary.get("low_stock_count", 0)
    if low > 0 and len(diagnosis) < 5:
        diagnosis.append(
            {
                "message": f"{low} prodotti attivi hanno scorte basse (≤{LOW_STOCK_THRESHOLD}).",
                "severity": "warning",
            }
        )

    if attribution_intelligence and attribution_intelligence.get("_total_orders", 0) > 0:
        score = float(attribution_intelligence.get("tracking_quality_score") or 0)
        if len(diagnosis) < 5:
            diagnosis.append(
                {
                    "message": (
                        f"Tracking quality Shopify: {score}% degli ordini ha una sorgente utile. "
                        "Collega GA4 per analisi cross-channel avanzata."
                    ),
                    "severity": "info" if score >= 70 else "warning",
                }
            )
    elif len(diagnosis) < 5:
        diagnosis.append(
            {
                "message": "Collega GA4 per capire la provenienza degli acquisti.",
                "severity": "info",
            }
        )

    return diagnosis[:5]


def _build_attribution_placeholder() -> dict[str, Any]:
    return {
        "connected_sources": [],
        "channel_breakdown": [],
        "utm_coverage": None,
        "message": (
            "Collega GA4, Meta Ads, Google Ads e Klaviyo per analisi canali, UTM e ROAS."
        ),
    }


async def build_dashboard(
    store: ShopifyStore,
    session: AsyncSession,
) -> dict[str, Any]:
    empty_summary = {
        "revenue": Decimal("0"),
        "orders_count": 0,
        "average_order_value": Decimal("0"),
        "products_count": 0,
        "active_products_count": 0,
        "draft_products_count": 0,
        "paid_orders_count": 0,
        "pending_orders_count": 0,
        "fulfilled_orders_count": 0,
        "unfulfilled_orders_count": 0,
        "low_stock_count": 0,
        "out_of_stock_count": 0,
        "products_without_sales_count": 0,
        "seo_issues_count": 0,
        "critical_alerts_count": 0,
        "last_sync_at": store.last_sync_at,
        "shop_domain": store.shop_domain,
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

    active_products = [p for p in products if _is_active_status(p.status)]
    draft_products = [p for p in products if (p.status or "").upper() == "DRAFT"]

    out_of_stock = [
        p for p in active_products if p.total_inventory is not None and p.total_inventory == 0
    ]
    low_stock = [
        p
        for p in active_products
        if p.total_inventory is not None and 0 < p.total_inventory <= LOW_STOCK_THRESHOLD
    ]

    pending_orders = [
        o for o in orders if (o.financial_status or "").upper() in PENDING_STATUSES
    ]
    unfulfilled_orders = [
        o
        for o in orders
        if (o.fulfillment_status or "").upper() not in FULFILLED_STATUSES
        and (o.fulfillment_status or "").strip() != ""
    ]

    paid_orders_count = sum(
        1 for o in orders if (o.financial_status or "").upper() in PAID_STATUSES
    )
    fulfilled_orders_count = sum(
        1 for o in orders if (o.fulfillment_status or "").upper() in FULFILLED_STATUSES
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
            pass

    average_order_value = revenue / orders_count if orders_count else Decimal("0")

    line_items: list[dict[str, Any]] = []
    try:
        line_items = _parse_line_items(orders)
    except Exception:
        line_items = []

    sold_gids = {item["product_gid"] for item in line_items}
    qty_by_gid: Counter[str] = Counter()
    for item in line_items:
        qty_by_gid[item["product_gid"]] += item["quantity"]

    products_by_gid = _product_lookup(products)
    no_sales = _compute_no_sales_products(products, sold_gids)

    seo_section: dict[str, Any] = {
        "products_missing_meta_title": [],
        "products_missing_meta_description": [],
        "products_missing_both": [],
        "seo_opportunities": [],
    }
    try:
        seo_section = _compute_seo_section(products)
    except Exception:
        pass

    seo_issues_count = (
        len(seo_section["products_missing_meta_title"])
        + len(seo_section["products_missing_meta_description"])
        + len(seo_section["products_missing_both"])
    )

    product_performance: dict[str, Any] = {
        "best_sellers": [],
        "no_sales_products": [],
        "high_stock_low_sales": [],
    }
    try:
        product_performance = {
            "best_sellers": _compute_best_sellers(line_items, products_by_gid),
            "no_sales_products": no_sales,
            "high_stock_low_sales": _compute_high_stock_low_sales(products, qty_by_gid),
        }
    except Exception:
        pass

    total_units = sum(p.total_inventory or 0 for p in active_products if p.total_inventory is not None)

    inventory_section: dict[str, Any] = {
        "low_stock_products": [_product_to_dict(p) for p in low_stock[:20]],
        "out_of_stock_products": [_product_to_dict(p) for p in out_of_stock[:20]],
        "inventory_summary": {
            "total_units": total_units,
            "active_products": len(active_products),
            "zero_stock_active_products": len(out_of_stock),
            "low_stock_active_products": len(low_stock),
        },
    }

    orders_section: dict[str, Any] = {
        "recent_orders": [],
        "pending_orders": [],
        "unfulfilled_orders": [],
    }
    try:
        orders_section = {
            "recent_orders": [_order_to_dict(o) for o in orders[:10]],
            "pending_orders": [_order_to_dict(o) for o in pending_orders[:10]],
            "unfulfilled_orders": [_order_to_dict(o) for o in unfulfilled_orders[:10]],
        }
    except Exception:
        pass

    summary = {
        **empty_summary,
        "revenue": revenue,
        "orders_count": orders_count,
        "average_order_value": average_order_value,
        "products_count": len(products),
        "active_products_count": len(active_products),
        "draft_products_count": len(draft_products),
        "paid_orders_count": paid_orders_count,
        "pending_orders_count": len(pending_orders),
        "fulfilled_orders_count": fulfilled_orders_count,
        "unfulfilled_orders_count": len(unfulfilled_orders),
        "low_stock_count": len(low_stock),
        "out_of_stock_count": len(out_of_stock),
        "products_without_sales_count": len(no_sales),
        "seo_issues_count": seo_issues_count,
    }

    raw_attribution_intelligence: dict[str, Any] = compute_attribution_intelligence([])
    attribution_intelligence: dict[str, Any] = {}
    marketing_report_availability: dict[str, Any] = {}
    attribution_alerts: list[dict[str, Any]] = []
    try:
        raw_attribution_intelligence = compute_attribution_intelligence(orders)
        marketing_report_availability = build_marketing_report_availability(
            orders,
            raw_attribution_intelligence,
        )
        attribution_alerts = build_attribution_alerts(raw_attribution_intelligence)
        attribution_intelligence = {
            k: v
            for k, v in raw_attribution_intelligence.items()
            if not k.startswith("_")
        }
    except Exception:
        attribution_intelligence = {
            k: v
            for k, v in raw_attribution_intelligence.items()
            if not k.startswith("_")
        }
        marketing_report_availability = build_marketing_report_availability([], {})

    alerts: list[dict[str, Any]] = []
    try:
        alerts = _build_alerts(
            products,
            orders,
            sold_gids,
            bool(line_items),
            store.last_sync_at,
            attribution_alerts,
        )
    except Exception:
        alerts = []

    summary["critical_alerts_count"] = sum(1 for a in alerts if a["severity"] == "critical")

    daily_diagnosis: list[dict[str, str]] = []
    try:
        daily_diagnosis = _build_daily_diagnosis(summary, raw_attribution_intelligence)
    except Exception:
        daily_diagnosis = []

    return {
        "summary": summary,
        "alerts": alerts,
        "product_performance": product_performance,
        "inventory": inventory_section,
        "orders": orders_section,
        "seo": seo_section,
        "attribution": _build_attribution_placeholder(),
        "attribution_intelligence": attribution_intelligence,
        "marketing_report_availability": marketing_report_availability,
        "daily_diagnosis": daily_diagnosis,
    }
