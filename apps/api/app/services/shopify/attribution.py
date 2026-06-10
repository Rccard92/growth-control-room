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


def _visit_from_journey(journey: dict[str, Any] | None, *, first: bool) -> dict[str, Any]:
    if not journey:
        return {}
    key = "firstVisit" if first else "lastVisit"
    visit = journey.get(key) or {}
    return visit if isinstance(visit, dict) else {}


def _touch_from_visit(visit: dict[str, Any]) -> dict[str, Any]:
    utm = visit.get("utmParameters") or {}
    return {
        "utm_source": _normalize_source_label(utm.get("source")),
        "utm_medium": _normalize_source_label(utm.get("medium")),
        "utm_campaign": _normalize_source_label(utm.get("campaign")),
        "utm_content": _normalize_source_label(utm.get("content")),
        "utm_term": _normalize_source_label(utm.get("term")),
        "landing_page": _normalize_source_label(visit.get("landingPage")),
        "referral_code": _normalize_source_label(visit.get("referralCode")),
        "source": _normalize_source_label(visit.get("source")),
        "source_type": _normalize_source_label(visit.get("sourceType")),
    }


def extract_first_touch(node: dict[str, Any]) -> dict[str, Any]:
    journey = node.get("customerJourneySummary") or {}
    return _touch_from_visit(_visit_from_journey(journey, first=True))


def extract_last_touch(node: dict[str, Any]) -> dict[str, Any]:
    journey = node.get("customerJourneySummary") or {}
    visit = _visit_from_journey(journey, first=False)
    if not visit:
        visit = _visit_from_journey(journey, first=True)
    return _touch_from_visit(visit)


def extract_journey_meta(node: dict[str, Any]) -> dict[str, Any]:
    journey = node.get("customerJourneySummary") or {}
    ready = journey.get("ready")
    days = journey.get("daysToConversion")
    index = journey.get("customerOrderIndex")
    return {
        "attribution_ready": bool(ready) if ready is not None else None,
        "days_to_conversion": int(days) if days is not None else None,
        "customer_order_index": int(index) if index is not None else None,
    }


def extract_order_attribution(node: dict[str, Any]) -> dict[str, Any]:
    first = extract_first_touch(node)
    last = extract_last_touch(node)
    journey_meta = extract_journey_meta(node)

    channel_info = node.get("channelInformation") or {}
    channel_def = channel_info.get("channelDefinition") or {}

    discount_codes = node.get("discountCodes") or []
    if not isinstance(discount_codes, list):
        discount_codes = []

    return {
        "source_name": _normalize_source_label(node.get("sourceName")),
        "source_identifier": _normalize_source_label(node.get("sourceIdentifier")),
        "registered_source_url": _normalize_source_label(node.get("registeredSourceUrl")),
        "channel_name": _normalize_source_label(channel_def.get("channelName")),
        "channel_handle": _normalize_source_label(channel_def.get("handle")),
        "landing_page": last.get("landing_page"),
        "referrer_source": last.get("source_type") or last.get("source"),
        "referrer_name": last.get("referral_code"),
        "utm_source": last.get("utm_source"),
        "utm_medium": last.get("utm_medium"),
        "utm_campaign": last.get("utm_campaign"),
        "utm_content": last.get("utm_content"),
        "utm_term": last.get("utm_term"),
        "first_utm_source": first.get("utm_source"),
        "first_utm_medium": first.get("utm_medium"),
        "first_utm_campaign": first.get("utm_campaign"),
        "first_utm_content": first.get("utm_content"),
        "first_utm_term": first.get("utm_term"),
        "first_landing_page": first.get("landing_page"),
        "first_referral_code": first.get("referral_code"),
        "first_source": first.get("source"),
        "first_source_type": first.get("source_type"),
        "discount_codes": discount_codes,
        "customer_type": "unknown",
        **journey_meta,
    }


def order_has_tracking_signal(order: ShopifyOrder) -> bool:
    return bool(
        order.utm_source
        or order.source_name
        or order.channel_name
        or order.registered_source_url
        or order.first_utm_source
    )


def _is_direct_like(value: str | None) -> bool:
    if not value:
        return False
    normalized = value.strip().lower()
    return normalized in DIRECT_SOURCES or normalized == "direct"


def resolve_attribution_source(order: ShopifyOrder) -> str:
    for value in (
        order.utm_source,
        order.source_name,
        order.channel_name,
        order.registered_source_url,
    ):
        label = _normalize_source_label(value)
        if not label:
            continue
        if _is_direct_like(label):
            return DIRECT_SOURCE
        return label
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
        lambda: {
            "new_count": 0,
            "returning_count": 0,
            "unknown_count": 0,
            "revenue": Decimal("0"),
        }
    )
    products_by_source: dict[str, set[str]] = defaultdict(set)
    product_revenue_by_source: dict[tuple[str, str], Decimal] = defaultdict(
        lambda: Decimal("0")
    )

    tracking_signals = 0
    direct_count = 0
    unknown_count = 0
    unknown_revenue = Decimal("0")
    has_utm_campaign = False

    for order in orders:
        source = resolve_attribution_source(order)
        revenue = order.current_total_price or order.total_price or Decimal("0")
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
        for src, data in sorted(
            new_returning.items(), key=lambda x: x[1]["revenue"], reverse=True
        )
    ][:15]

    campaign_items = _breakdown_items(revenue_by_campaign, orders_by_campaign, "campaign")
    if not has_utm_campaign:
        campaign_items = []

    return {
        "revenue_by_source": _breakdown_items(
            revenue_by_source, orders_by_source, "source"
        ),
        "orders_by_source": [
            {"source": k, "orders_count": v, "revenue": revenue_by_source[k]}
            for k, v in orders_by_source.most_common(15)
        ],
        "revenue_by_channel": _breakdown_items(
            revenue_by_channel, orders_by_channel, "channel"
        ),
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
        "shopify_order_attribution_available": has_signal
        and intelligence.get("_total_orders", 0) > 0,
        "shopifyql_available": None,
        "message": (
            "Questa vista usa i dati attribution disponibili sugli ordini Shopify. "
            "ShopifyQL non è ancora implementato."
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
