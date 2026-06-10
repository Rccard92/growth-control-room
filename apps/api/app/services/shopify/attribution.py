from collections import Counter, defaultdict
from decimal import Decimal
from typing import Any

from app.models.shopify import ShopifyOrder

DIRECT_SOURCES = {"direct", "(direct)", "none"}
UNKNOWN_SOURCE = "Unknown"
DIRECT_SOURCE = "Direct"


def _parse_decimal(value: str | None) -> Decimal:
    if not value:
        return Decimal("0")
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal("0")


def _normalize_source_label(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = value.strip()
    return cleaned or None


def _visit_data(journey: dict[str, Any] | None, prefer_last: bool = True) -> dict[str, Any]:
    if not journey:
        return {}
    key = "lastVisit" if prefer_last else "firstVisit"
    visit = journey.get(key) or {}
    if not visit and prefer_last:
        visit = journey.get("firstVisit") or {}
    return visit if isinstance(visit, dict) else {}


def resolve_customer_type(customer: dict[str, Any] | None) -> str:
    if not customer:
        return "unknown"
    try:
        count = int(customer.get("numberOfOrders") or 0)
    except (TypeError, ValueError):
        return "unknown"
    if count <= 1:
        return "new"
    return "returning"


def extract_order_attribution(node: dict[str, Any]) -> dict[str, Any]:
    journey = node.get("customerJourneySummary") or {}
    visit = _visit_data(journey, prefer_last=True)
    utm = visit.get("utmParameters") or {}

    channel_info = node.get("channelInformation") or {}
    channel_def = channel_info.get("channelDefinition") or {}
    channel_name = _normalize_source_label(channel_def.get("channelName"))

    source_name = _normalize_source_label(node.get("sourceName"))
    source_identifier = _normalize_source_label(node.get("sourceIdentifier"))
    registered_source_url = _normalize_source_label(node.get("registeredSourceUrl"))

    utm_source = _normalize_source_label(utm.get("source"))
    utm_medium = _normalize_source_label(utm.get("medium"))
    utm_campaign = _normalize_source_label(utm.get("campaign"))
    utm_content = _normalize_source_label(utm.get("content"))
    utm_term = _normalize_source_label(utm.get("term"))

    landing_page = _normalize_source_label(visit.get("landingPage"))
    referrer_source = _normalize_source_label(visit.get("sourceType") or visit.get("source"))
    referrer_name = _normalize_source_label(visit.get("referralCode"))

    customer = node.get("customer") or {}
    customer_type = resolve_customer_type(customer)

    return {
        "source_name": source_name,
        "source_identifier": source_identifier,
        "channel_name": channel_name,
        "landing_page": landing_page,
        "referrer_source": referrer_source,
        "referrer_name": referrer_name,
        "utm_source": utm_source,
        "utm_medium": utm_medium,
        "utm_campaign": utm_campaign,
        "utm_content": utm_content,
        "utm_term": utm_term,
        "customer_type": customer_type,
        "registered_source_url": registered_source_url,
    }


def order_has_tracking_signal(order: ShopifyOrder) -> bool:
    payload = order.raw_payload or {}
    extracted = extract_order_attribution(payload)
    return bool(
        order.utm_source
        or order.source_name
        or order.channel_name
        or extracted.get("registered_source_url")
        or extracted.get("utm_source")
        or extracted.get("source_name")
        or extracted.get("channel_name")
    )


def _is_direct_like(value: str | None) -> bool:
    if not value:
        return False
    normalized = value.strip().lower()
    return normalized in DIRECT_SOURCES or normalized == "direct"


def resolve_attribution_source(order: ShopifyOrder) -> str:
    utm_source = _normalize_source_label(order.utm_source)
    if utm_source:
        if _is_direct_like(utm_source):
            return DIRECT_SOURCE
        return utm_source

    source_name = _normalize_source_label(order.source_name)
    if source_name:
        if _is_direct_like(source_name):
            return DIRECT_SOURCE
        return source_name

    channel_name = _normalize_source_label(order.channel_name)
    if channel_name:
        if _is_direct_like(channel_name):
            return DIRECT_SOURCE
        return channel_name

    payload = order.raw_payload or {}
    extracted = extract_order_attribution(payload)
    registered = extracted.get("registered_source_url")
    if registered:
        if _is_direct_like(registered):
            return DIRECT_SOURCE
        return registered

    if _is_direct_like(source_name) or _is_direct_like(utm_source):
        return DIRECT_SOURCE

    return UNKNOWN_SOURCE


def _iter_line_item_nodes(payload: dict[str, Any]) -> list[dict[str, Any]]:
    line_items = payload.get("lineItems") or {}
    nodes = line_items.get("nodes") or []
    if nodes:
        return [n for n in nodes if isinstance(n, dict)]
    edges = line_items.get("edges") or []
    return [edge.get("node") for edge in edges if edge.get("node")]


def _line_item_title(node: dict[str, Any]) -> str:
    product = node.get("product") or {}
    return product.get("title") or node.get("title") or "Unknown"


def _line_item_revenue(node: dict[str, Any]) -> Decimal:
    discounted = (node.get("discountedTotalSet") or {}).get("shopMoney") or {}
    original_total = (node.get("originalTotalSet") or {}).get("shopMoney") or {}
    unit = (node.get("originalUnitPriceSet") or {}).get("shopMoney") or {}
    revenue = _parse_decimal(discounted.get("amount"))
    if revenue == 0:
        revenue = _parse_decimal(original_total.get("amount"))
    if revenue == 0 and unit.get("amount"):
        qty = int(node.get("quantity") or 0)
        revenue = _parse_decimal(unit.get("amount")) * qty
    return revenue


def compute_attribution_intelligence(orders: list[ShopifyOrder]) -> dict[str, Any]:
    if not orders:
        return _empty_attribution_intelligence()

    revenue_by_source: defaultdict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    orders_by_source: Counter[str] = Counter()
    revenue_by_channel: defaultdict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    orders_by_channel: Counter[str] = Counter()
    revenue_by_campaign: defaultdict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    orders_by_campaign: Counter[str] = Counter()
    new_returning: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"new_count": 0, "returning_count": 0, "unknown_count": 0, "revenue": Decimal("0")}
    )
    products_by_source: dict[str, set[str]] = defaultdict(set)
    product_revenue_by_source: dict[tuple[str, str], Decimal] = defaultdict(lambda: Decimal("0"))

    tracking_signals = 0
    direct_count = 0
    unknown_count = 0
    unknown_revenue = Decimal("0")
    direct_revenue = Decimal("0")
    has_utm_campaign = False

    for order in orders:
        source = resolve_attribution_source(order)
        revenue = order.total_price or Decimal("0")
        channel = _normalize_source_label(order.channel_name) or UNKNOWN_SOURCE
        campaign = _normalize_source_label(order.utm_campaign)

        if order_has_tracking_signal(order):
            tracking_signals += 1

        revenue_by_source[source] += revenue
        orders_by_source[source] += 1

        revenue_by_channel[channel] += revenue
        orders_by_channel[channel] += 1

        if campaign:
            has_utm_campaign = True
            revenue_by_campaign[campaign] += revenue
            orders_by_campaign[campaign] += 1

        bucket = new_returning[source]
        bucket["revenue"] += revenue
        ctype = (order.customer_type or "unknown").lower()
        if ctype == "new":
            bucket["new_count"] += 1
        elif ctype == "returning":
            bucket["returning_count"] += 1
        else:
            bucket["unknown_count"] += 1

        if source == DIRECT_SOURCE:
            direct_count += 1
            direct_revenue += revenue
        if source == UNKNOWN_SOURCE:
            unknown_count += 1
            unknown_revenue += revenue

        payload = order.raw_payload or {}
        for node in _iter_line_item_nodes(payload):
            title = _line_item_title(node)
            products_by_source[source].add(title)
            product_revenue_by_source[(source, title)] += _line_item_revenue(node)

    total_orders = len(orders)
    tracking_quality_score = (
        round((tracking_signals / total_orders) * 100, 1) if total_orders else 0.0
    )

    def _breakdown_items(
        revenue_map: defaultdict[str, Decimal],
        count_map: Counter[str],
        label_key: str = "source",
    ) -> list[dict[str, Any]]:
        items = []
        for key, rev in sorted(revenue_map.items(), key=lambda x: x[1], reverse=True):
            items.append(
                {
                    label_key: key,
                    "revenue": rev,
                    "orders_count": count_map.get(key, 0),
                }
            )
        return items[:15]

    top_products: list[dict[str, Any]] = []
    for (source, title), rev in sorted(
        product_revenue_by_source.items(),
        key=lambda x: x[1],
        reverse=True,
    )[:20]:
        top_products.append(
            {
                "source": source,
                "product_title": title,
                "revenue": rev,
                "orders_count": orders_by_source.get(source, 0),
            }
        )

    new_vs_returning = [
        {
            "source": src,
            "new_count": data["new_count"],
            "returning_count": data["returning_count"],
            "unknown_count": data["unknown_count"],
            "revenue": data["revenue"],
        }
        for src, data in sorted(new_returning.items(), key=lambda x: x[1]["revenue"], reverse=True)
    ][:15]

    campaign_items = _breakdown_items(revenue_by_campaign, orders_by_campaign, "campaign")
    if not has_utm_campaign:
        campaign_items = []

    return {
        "revenue_by_source": _breakdown_items(revenue_by_source, orders_by_source, "source"),
        "orders_by_source": [
            {"source": k, "orders_count": v, "revenue": revenue_by_source[k]}
            for k, v in orders_by_source.most_common(15)
        ],
        "revenue_by_channel": _breakdown_items(revenue_by_channel, orders_by_channel, "channel"),
        "orders_by_channel": [
            {"channel": k, "orders_count": v, "revenue": revenue_by_channel[k]}
            for k, v in orders_by_channel.most_common(15)
        ],
        "revenue_by_utm_campaign": campaign_items,
        "orders_by_utm_campaign": [
            {"campaign": k, "orders_count": v, "revenue": revenue_by_campaign[k]}
            for k, v in orders_by_campaign.most_common(15)
        ],
        "new_vs_returning_by_source": new_vs_returning,
        "top_products_by_source": top_products,
        "unattributed_orders_count": unknown_count,
        "unattributed_revenue": unknown_revenue,
        "direct_orders_count": direct_count,
        "unknown_orders_count": unknown_count,
        "tracking_quality_score": tracking_quality_score,
        "_products_by_source": dict(products_by_source),
        "_total_orders": total_orders,
    }


def _empty_attribution_intelligence() -> dict[str, Any]:
    return {
        "revenue_by_source": [],
        "orders_by_source": [],
        "revenue_by_channel": [],
        "orders_by_channel": [],
        "revenue_by_utm_campaign": [],
        "orders_by_utm_campaign": [],
        "new_vs_returning_by_source": [],
        "top_products_by_source": [],
        "unattributed_orders_count": 0,
        "unattributed_revenue": Decimal("0"),
        "direct_orders_count": 0,
        "unknown_orders_count": 0,
        "tracking_quality_score": 0.0,
        "_products_by_source": {},
        "_total_orders": 0,
    }


def build_marketing_report_availability(
    orders: list[ShopifyOrder],
    intelligence: dict[str, Any],
) -> dict[str, Any]:
    has_signal = any(order_has_tracking_signal(o) for o in orders)
    return {
        "shopify_order_attribution_available": has_signal and intelligence.get("_total_orders", 0) > 0,
        "shopifyql_available": None,
        "message": (
            "Questa vista usa i dati attribution disponibili sugli ordini Shopify. "
            "I report aggregati ShopifyQL verranno testati nello step successivo."
        ),
    }


def build_attribution_alerts(intelligence: dict[str, Any]) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    total = intelligence.get("_total_orders", 0)
    if total == 0:
        return alerts

    score = float(intelligence.get("tracking_quality_score") or 0)
    if score < 70:
        alerts.append(
            {
                "id": "attr-tracking-quality",
                "severity": "warning",
                "title": "Tracking attribution debole",
                "description": (
                    f"Solo il {score}% degli ordini ha una sorgente chiara "
                    "(UTM, sourceName, channel o URL registrato)."
                ),
                "entity_type": "attribution",
                "entity_id": None,
                "action_label": "Verifica tag UTM",
            }
        )

    direct = int(intelligence.get("direct_orders_count") or 0)
    unknown = int(intelligence.get("unknown_orders_count") or 0)
    if total > 0 and ((direct + unknown) / total) > 0.4:
        pct = round(((direct + unknown) / total) * 100, 1)
        alerts.append(
            {
                "id": "attr-direct-unknown",
                "severity": "warning",
                "title": "Alta quota Direct/Unknown",
                "description": (
                    f"{pct}% degli ordini è classificato come Direct o Unknown. "
                    "La visibilità sui canali marketing è limitata."
                ),
                "entity_type": "attribution",
                "entity_id": None,
                "action_label": "Rafforza UTM",
            }
        )

    products_by_source = intelligence.get("_products_by_source") or {}
    revenue_by_source = {
        item["source"]: item["revenue"]
        for item in intelligence.get("revenue_by_source", [])
    }
    for source, revenue in revenue_by_source.items():
        if source in (UNKNOWN_SOURCE, DIRECT_SOURCE):
            continue
        product_count = len(products_by_source.get(source, set()))
        if revenue > 0 and product_count <= 2:
            alerts.append(
                {
                    "id": f"attr-concentrated-{source}",
                    "severity": "opportunity",
                    "title": "Canale concentrato su pochi SKU",
                    "description": (
                        f"La sorgente '{source}' genera vendite ma solo {product_count} "
                        "prodotto/i distinti negli ordini sincronizzati."
                    ),
                    "entity_type": "attribution",
                    "entity_id": source,
                    "action_label": "Espandi catalogo",
                }
            )

    return alerts[:5]
