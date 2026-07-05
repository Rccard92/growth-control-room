"""Growth Audit GA4 item-level ecommerce funnel analysis."""

from __future__ import annotations

import logging
import re
from datetime import UTC, date, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.growth_audit import GrowthAuditFinding, GrowthAuditPage, GrowthAuditRun
from app.services.google.analytics_client import fetch_ga4_item_ecommerce_report
from app.services.google.google_tokens import get_valid_google_access_token
from app.services.growth_audit.exceptions import (
    GrowthAuditRunNotFoundError,
    GrowthAuditValidationError,
)
from app.services.growth_audit.ga4_item_product_matching import (
    build_assigned_row_keys,
    build_page_match_debug,
    build_product_match_profiles,
    match_ga4_rows_to_pages,
)
from app.services.growth_audit.run_service import (
    _ACTIVE_RUN_STATUSES,
    create_growth_audit_event,
    get_growth_audit_run,
    list_growth_audit_pages,
)
from app.services.projects import get_project_in_default_workspace
from app.services.shopify.client import ShopifyAPIError, ShopifyGraphQLClient
from app.services.shopify.connect import get_shopify_client_for_store, get_shopify_store_for_project

logger = logging.getLogger(__name__)

MAX_GA4_ECOMMERCE_FINDINGS = 10
HIGH_ITEM_VIEWS_THRESHOLD = 50
HIGH_ITEM_VIEWS_STRICT_THRESHOLD = 100
HIGH_CART_THRESHOLD = 5
HIGH_ITEM_REVENUE_THRESHOLD = 100.0
LOW_VIEW_TO_CART_RATE = 0.05
LOW_CART_TO_PURCHASE_RATE = 0.2
HIGH_GSC_IMPRESSIONS = 200
HIGH_GA4_SESSIONS = 50

VARIANT_MATCH_CHUNK_SIZE = 50
VARIANT_MATCH_FIELDS = """
      ... on Product {
        id
        variants(first: 100) {
          nodes {
            id
            title
            sku
            price
            inventoryQuantity
            selectedOptions {
              name
              value
            }
          }
        }
      }
"""


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _is_product_page(page: GrowthAuditPage) -> bool:
    page_type = (page.page_type or "").lower()
    source_type = (page.source_entity_type or "").lower()
    return page_type == "product" or source_type == "shopify_product"


def _filter_product_pages(pages: list[GrowthAuditPage]) -> list[GrowthAuditPage]:
    return [
        page
        for page in pages
        if _is_product_page(page) and (page.source_entity_gid or "").strip()
    ]


def _normalize_days(days: int) -> int:
    normalized = max(7, min(days, 90))
    if normalized not in {7, 30, 90}:
        normalized = 30 if normalized > 30 else (7 if normalized < 15 else 30)
    return normalized


def _safe_float(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _safe_rate(numerator: float | int, denominator: float | int) -> float:
    if denominator <= 0:
        return 0.0
    return round(float(numerator) / float(denominator), 4)


def _extract_legacy_id(gid: str | None) -> str | None:
    if not gid:
        return None
    match = re.search(r"/(\d+)$", gid.strip())
    return match.group(1) if match else None


async def _fetch_shopify_variant_match_data(
    *,
    shop_domain: str,
    access_token: str,
    product_gids: list[str],
) -> dict[str, dict[str, Any]]:
    unique_gids = sorted({gid for gid in product_gids if gid})
    if not unique_gids:
        return {}

    client = ShopifyGraphQLClient(shop_domain, access_token)
    variant_data_by_gid: dict[str, dict[str, Any]] = {}

    for index in range(0, len(unique_gids), VARIANT_MATCH_CHUNK_SIZE):
        chunk = unique_gids[index : index + VARIANT_MATCH_CHUNK_SIZE]
        query = f"""
        query ProductVariantMatch($ids: [ID!]!) {{
          nodes(ids: $ids) {{
            {VARIANT_MATCH_FIELDS}
          }}
        }}
        """
        try:
            data = await client.execute(query, {"ids": chunk})
        except ShopifyAPIError:
            continue

        nodes = data.get("nodes") or []
        for node in nodes:
            if not node or not node.get("id"):
                continue
            product_gid = node["id"]
            variant_legacy_ids: list[str] = []
            skus: list[str] = []
            variant_entries: list[dict[str, Any]] = []
            variants = (node.get("variants") or {}).get("nodes") or []
            for variant in variants:
                if not isinstance(variant, dict):
                    continue
                legacy_id = _extract_legacy_id(variant.get("id"))
                variant_gid = variant.get("id")
                sku = variant.get("sku")
                price_raw = variant.get("price")
                price = _safe_float(price_raw) if price_raw is not None else None
                stock_raw = variant.get("inventoryQuantity")
                stock = int(stock_raw) if stock_raw is not None else None
                selected_options = variant.get("selectedOptions")
                if legacy_id:
                    variant_legacy_ids.append(legacy_id)
                if sku:
                    skus.append(str(sku))
                variant_entries.append(
                    {
                        "variantGid": variant_gid,
                        "variantLegacyId": legacy_id,
                        "title": variant.get("title"),
                        "sku": str(sku) if sku else None,
                        "price": price,
                        "stock": stock,
                        "selectedOptions": selected_options if isinstance(selected_options, list) else None,
                    }
                )
            variant_data_by_gid[product_gid] = {
                "variantLegacyIds": variant_legacy_ids,
                "skus": skus,
                "variants": variant_entries,
            }

    return variant_data_by_gid


def _get_page_gsc_impressions(page: GrowthAuditPage) -> int:
    meta = (page.page_metadata or {}).get("searchConsole") or {}
    if not isinstance(meta, dict):
        return 0
    return int(meta.get("impressions") or 0)


def _get_page_ga4_sessions(page: GrowthAuditPage) -> int:
    meta = (page.page_metadata or {}).get("analytics") or {}
    if not isinstance(meta, dict):
        return 0
    return int(meta.get("sessions") or 0)


def _get_page_shopify_sales(page: GrowthAuditPage) -> float:
    meta = (page.page_metadata or {}).get("shopifyCommerce") or {}
    if not isinstance(meta, dict):
        return 0.0
    return _safe_float(meta.get("sales"))


def _page_has_open_critical_findings(
    page: GrowthAuditPage,
    open_findings: list[GrowthAuditFinding],
) -> bool:
    for finding in open_findings:
        if finding.page_id != page.id or finding.status != "open":
            continue
        if finding.severity in {"critical", "high"}:
            return True
    return False


def _has_funnel_signal(aggregate: dict[str, Any] | None) -> bool:
    if not aggregate:
        return False
    return any(
        int(aggregate.get(key) or 0) > 0
        for key in (
            "itemViews",
            "itemViewEvents",
            "itemsAddedToCart",
            "itemsCheckedOut",
            "itemsPurchased",
        )
    ) or _safe_float(aggregate.get("itemRevenue")) > 0


def _has_variant_funnel_signal(variant_row: dict[str, Any]) -> bool:
    return any(
        int(variant_row.get(key) or 0) > 0
        for key in (
            "itemViews",
            "itemViewEvents",
            "itemsAddedToCart",
            "itemsCheckedOut",
            "itemsPurchased",
        )
    ) or _safe_float(variant_row.get("itemRevenue")) > 0


def _serialize_variant_bucket_row(
    *,
    variant_key: str,
    metrics: dict[str, Any] | None,
    catalog_variant: dict[str, Any] | None,
) -> dict[str, Any]:
    metrics = metrics or {}
    catalog_variant = catalog_variant or {}
    item_views = int(metrics.get("itemViews") or 0)
    item_view_events = int(metrics.get("itemViewEvents") or 0)
    views_base = item_views if item_views > 0 else item_view_events
    items_added_to_cart = int(metrics.get("itemsAddedToCart") or 0)
    items_checked_out = int(metrics.get("itemsCheckedOut") or 0)
    items_purchased = int(metrics.get("itemsPurchased") or 0)
    item_revenue = round(_safe_float(metrics.get("itemRevenue")), 2)
    variant_matched_by = metrics.get("matchedBy") or "none"
    has_signal = _has_variant_funnel_signal(metrics)
    item_ids_raw = metrics.get("itemIds") or []
    if isinstance(item_ids_raw, set):
        item_ids = sorted(item_ids_raw)
    else:
        item_ids = sorted(item_ids_raw)
    item_names_raw = metrics.get("itemNames") or []
    if isinstance(item_names_raw, set):
        item_names = sorted(item_names_raw)
    else:
        item_names = sorted(item_names_raw)

    if variant_key == "unknown":
        variant_title = "Variante non identificata"
        variant_legacy_id = "unknown"
    else:
        variant_legacy_id = variant_key
        variant_title = catalog_variant.get("title") or metrics.get("variantTitle")

    return {
        "variantLegacyId": variant_legacy_id,
        "variantGid": catalog_variant.get("variantGid") or metrics.get("variantGid"),
        "variantTitle": variant_title,
        "sku": catalog_variant.get("sku") or metrics.get("sku"),
        "price": catalog_variant.get("price") if catalog_variant.get("price") is not None else metrics.get("price"),
        "stock": catalog_variant.get("stock") if catalog_variant.get("stock") is not None else metrics.get("stock"),
        "itemIds": item_ids,
        "itemNames": item_names,
        "itemViews": item_views,
        "itemViewEvents": item_view_events,
        "itemsAddedToCart": items_added_to_cart,
        "itemsCheckedOut": items_checked_out,
        "itemsPurchased": items_purchased,
        "itemRevenue": item_revenue,
        "viewToCartRate": _safe_rate(items_added_to_cart, views_base),
        "cartToCheckoutRate": _safe_rate(items_checked_out, items_added_to_cart),
        "checkoutToPurchaseRate": _safe_rate(items_purchased, items_checked_out),
        "viewToPurchaseRate": _safe_rate(items_purchased, views_base),
        "cartToPurchaseRate": _safe_rate(items_purchased, items_added_to_cart),
        "matchedBy": variant_matched_by if has_signal else "none",
    }


def _build_variant_breakdown(
    aggregate: dict[str, Any] | None,
    variant_catalog: list[dict[str, Any]] | None,
) -> dict[str, Any] | None:
    catalog = variant_catalog or []
    if not catalog and not (aggregate or {}).get("variants"):
        return None

    aggregate_variants: dict[str, dict[str, Any]] = (aggregate or {}).get("variants") or {}
    catalog_by_id = {
        str(variant.get("variantLegacyId")): variant
        for variant in catalog
        if variant.get("variantLegacyId")
    }

    breakdown_rows: list[dict[str, Any]] = []
    seen_keys: set[str] = set()

    for catalog_variant in catalog:
        variant_key = str(catalog_variant.get("variantLegacyId") or "")
        if not variant_key:
            continue
        seen_keys.add(variant_key)
        metrics = aggregate_variants.get(variant_key)
        breakdown_rows.append(
            _serialize_variant_bucket_row(
                variant_key=variant_key,
                metrics=metrics,
                catalog_variant=catalog_variant,
            )
        )

    for variant_key, metrics in aggregate_variants.items():
        if variant_key in seen_keys:
            continue
        breakdown_rows.append(
            _serialize_variant_bucket_row(
                variant_key=variant_key,
                metrics=metrics,
                catalog_variant=catalog_by_id.get(variant_key),
            )
        )

    if not breakdown_rows:
        return None

    catalog_count = len([row for row in breakdown_rows if row.get("variantLegacyId") != "unknown"])
    variants_with_funnel_data = sum(
        1 for row in breakdown_rows if row.get("matchedBy") not in {None, "none"}
    )
    best_by_revenue = max(
        breakdown_rows,
        key=lambda row: _safe_float(row.get("itemRevenue")),
        default=None,
    )
    best_by_purchase = max(
        breakdown_rows,
        key=lambda row: int(row.get("itemsPurchased") or 0),
        default=None,
    )

    return {
        "variantBreakdown": breakdown_rows,
        "variantsCount": catalog_count,
        "variantsWithFunnelData": variants_with_funnel_data,
        "bestVariantByRevenue": best_by_revenue.get("variantLegacyId") if best_by_revenue else None,
        "bestVariantByPurchase": best_by_purchase.get("variantLegacyId") if best_by_purchase else None,
        "variantMatchingMode": "strict",
    }


def _build_page_ga4_ecommerce_metadata(
    *,
    period_days: int,
    aggregate: dict[str, Any] | None,
    synced_at: str,
    currency: str | None = None,
    match_debug: dict[str, Any] | None = None,
    variant_catalog: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    agg = aggregate or {}
    item_views = int(agg.get("itemViews") or 0)
    item_view_events = int(agg.get("itemViewEvents") or 0)
    views_base = item_views if item_views > 0 else item_view_events
    items_added_to_cart = int(agg.get("itemsAddedToCart") or 0)
    items_checked_out = int(agg.get("itemsCheckedOut") or 0)
    items_purchased = int(agg.get("itemsPurchased") or 0)
    item_revenue = round(_safe_float(agg.get("itemRevenue")), 2)

    matched_by = agg.get("matchedBy") or "none"
    matched_item_ids = sorted(agg.get("matchedItemIds") or [])
    matched_item_names = sorted(agg.get("matchedItemNames") or [])

    metadata: dict[str, Any] = {
        "periodDays": period_days,
        "itemViews": item_views,
        "itemViewEvents": item_view_events,
        "itemsAddedToCart": items_added_to_cart,
        "itemsCheckedOut": items_checked_out,
        "itemsPurchased": items_purchased,
        "itemRevenue": item_revenue,
        "currency": currency,
        "viewToCartRate": _safe_rate(items_added_to_cart, views_base),
        "cartToCheckoutRate": _safe_rate(items_checked_out, items_added_to_cart),
        "checkoutToPurchaseRate": _safe_rate(items_purchased, items_checked_out),
        "viewToPurchaseRate": _safe_rate(items_purchased, views_base),
        "cartToPurchaseRate": _safe_rate(items_purchased, items_added_to_cart),
        "dropoffViewToCart": max(views_base - items_added_to_cart, 0),
        "dropoffCartToCheckout": max(items_added_to_cart - items_checked_out, 0),
        "dropoffCheckoutToPurchase": max(items_checked_out - items_purchased, 0),
        "matchedBy": matched_by if _has_funnel_signal(agg) else "none",
        "matchedItemIds": matched_item_ids,
        "matchedItemNames": matched_item_names,
        "source": "ga4",
        "syncedAt": synced_at,
    }
    if match_debug:
        metadata["matchDebug"] = match_debug

    variant_summary = _build_variant_breakdown(aggregate, variant_catalog)
    if variant_summary:
        metadata.update(variant_summary)

    return metadata


def _compute_run_ga4_ecommerce_summary(
    product_pages: list[GrowthAuditPage],
    *,
    period_days: int,
    synced_at: str,
    unmatched_items: int,
    ambiguous_items: int = 0,
    currency: str | None = None,
) -> dict[str, Any]:
    total_item_views = 0
    total_items_added_to_cart = 0
    total_items_checked_out = 0
    total_items_purchased = 0
    total_item_revenue = 0.0
    products_with_funnel_data = 0
    products_without_funnel_data = 0
    high_view_low_cart_products = 0
    high_cart_low_purchase_products = 0
    view_to_cart_rates: list[float] = []
    cart_to_purchase_rates: list[float] = []
    top_candidates: list[tuple[float, dict[str, Any]]] = []
    top_variant_candidates: list[tuple[float, dict[str, Any]]] = []
    variants_with_funnel_data = 0
    variants_without_funnel_data = 0

    for page in product_pages:
        funnel = (page.page_metadata or {}).get("ga4Ecommerce") or {}
        if not isinstance(funnel, dict):
            continue

        item_views = int(funnel.get("itemViews") or funnel.get("itemViewEvents") or 0)
        items_added_to_cart = int(funnel.get("itemsAddedToCart") or 0)
        items_checked_out = int(funnel.get("itemsCheckedOut") or 0)
        items_purchased = int(funnel.get("itemsPurchased") or 0)
        item_revenue = _safe_float(funnel.get("itemRevenue"))
        matched_by = funnel.get("matchedBy") or "none"

        has_data = matched_by != "none" and (
            item_views > 0
            or items_added_to_cart > 0
            or items_checked_out > 0
            or items_purchased > 0
            or item_revenue > 0
        )

        if has_data:
            products_with_funnel_data += 1
        else:
            products_without_funnel_data += 1

        total_item_views += item_views
        total_items_added_to_cart += items_added_to_cart
        total_items_checked_out += items_checked_out
        total_items_purchased += items_purchased
        total_item_revenue += item_revenue

        view_to_cart = _safe_float(funnel.get("viewToCartRate"))
        cart_to_purchase = _safe_float(funnel.get("cartToPurchaseRate"))
        if has_data and view_to_cart > 0:
            view_to_cart_rates.append(view_to_cart)
        if has_data and cart_to_purchase > 0:
            cart_to_purchase_rates.append(cart_to_purchase)

        if item_views > HIGH_ITEM_VIEWS_THRESHOLD and items_added_to_cart == 0:
            high_view_low_cart_products += 1
        if items_added_to_cart > HIGH_CART_THRESHOLD and items_purchased == 0:
            high_cart_low_purchase_products += 1

        if has_data:
            top_candidates.append(
                (
                    item_revenue if item_revenue > 0 else float(item_views),
                    {
                        "pageId": str(page.id),
                        "title": page.source_entity_title or page.title,
                        "itemViews": item_views,
                        "itemsAddedToCart": items_added_to_cart,
                        "itemsPurchased": items_purchased,
                        "itemRevenue": round(item_revenue, 2),
                    },
                )
            )

        variant_breakdown = funnel.get("variantBreakdown") or []
        if isinstance(variant_breakdown, list):
            for variant_row in variant_breakdown:
                if not isinstance(variant_row, dict):
                    continue
                variant_matched_by = variant_row.get("matchedBy") or "none"
                variant_views = int(variant_row.get("itemViews") or variant_row.get("itemViewEvents") or 0)
                variant_revenue = _safe_float(variant_row.get("itemRevenue"))
                variant_has_data = variant_matched_by != "none" and (
                    variant_views > 0
                    or int(variant_row.get("itemsAddedToCart") or 0) > 0
                    or int(variant_row.get("itemsPurchased") or 0) > 0
                    or variant_revenue > 0
                )
                if variant_has_data:
                    variants_with_funnel_data += 1
                else:
                    variants_without_funnel_data += 1

                if variant_has_data:
                    top_variant_candidates.append(
                        (
                            variant_revenue if variant_revenue > 0 else float(variant_views),
                            {
                                "pageId": str(page.id),
                                "productTitle": page.source_entity_title or page.title,
                                "variantLegacyId": variant_row.get("variantLegacyId"),
                                "variantTitle": variant_row.get("variantTitle"),
                                "sku": variant_row.get("sku"),
                                "itemViews": variant_views,
                                "itemsAddedToCart": int(variant_row.get("itemsAddedToCart") or 0),
                                "itemsPurchased": int(variant_row.get("itemsPurchased") or 0),
                                "itemRevenue": round(variant_revenue, 2),
                            },
                        )
                    )

    top_candidates.sort(key=lambda item: item[0], reverse=True)
    top_variant_candidates.sort(key=lambda item: item[0], reverse=True)
    average_view_to_cart = (
        round(sum(view_to_cart_rates) / len(view_to_cart_rates), 4)
        if view_to_cart_rates
        else 0.0
    )
    average_cart_to_purchase = (
        round(sum(cart_to_purchase_rates) / len(cart_to_purchase_rates), 4)
        if cart_to_purchase_rates
        else 0.0
    )

    products_with_no_reliable_match = 0
    for page in product_pages:
        funnel = (page.page_metadata or {}).get("ga4Ecommerce") or {}
        if isinstance(funnel, dict) and funnel.get("syncedAt"):
            matched_by = funnel.get("matchedBy") or "none"
            if matched_by == "none":
                products_with_no_reliable_match += 1

    return {
        "periodDays": period_days,
        "totalItemViews": total_item_views,
        "totalItemsAddedToCart": total_items_added_to_cart,
        "totalItemsCheckedOut": total_items_checked_out,
        "totalItemsPurchased": total_items_purchased,
        "totalItemRevenue": round(total_item_revenue, 2),
        "averageViewToCartRate": average_view_to_cart,
        "averageCartToPurchaseRate": average_cart_to_purchase,
        "productsWithFunnelData": products_with_funnel_data,
        "productsWithoutFunnelData": products_without_funnel_data,
        "unmatchedItems": unmatched_items,
        "matchedProducts": products_with_funnel_data,
        "productsWithNoReliableMatch": products_with_no_reliable_match,
        "ambiguousItemsCount": ambiguous_items,
        "matchingMode": "strict",
        "matchingWarning": (
            "I dati item-level sono assegnati solo quando item_id, variant_id, SKU o "
            "nome prodotto coincidono in modo affidabile."
        ),
        "matchingSupportedPatterns": [
            "shopify_composite_item_id",
            "product_legacy_id",
            "variant_legacy_id",
            "sku",
            "item_name_exact",
        ],
        "highViewLowCartProducts": high_view_low_cart_products,
        "highCartLowPurchaseProducts": high_cart_low_purchase_products,
        "topFunnelProducts": [item[1] for item in top_candidates[:10]],
        "variantsWithFunnelData": variants_with_funnel_data,
        "variantsWithoutFunnelData": variants_without_funnel_data,
        "topVariants": [item[1] for item in top_variant_candidates[:10]],
        "currency": currency,
        "lastSyncedAt": synced_at,
    }


def _build_ga4_ecommerce_findings(
    product_pages: list[GrowthAuditPage],
    open_findings: list[GrowthAuditFinding],
) -> list[dict[str, Any]]:
    candidates: list[tuple[int, dict[str, Any]]] = []

    for page in product_pages:
        funnel = (page.page_metadata or {}).get("ga4Ecommerce") or {}
        if not isinstance(funnel, dict):
            continue

        item_views = int(funnel.get("itemViews") or funnel.get("itemViewEvents") or 0)
        items_added_to_cart = int(funnel.get("itemsAddedToCart") or 0)
        items_checked_out = int(funnel.get("itemsCheckedOut") or 0)
        items_purchased = int(funnel.get("itemsPurchased") or 0)
        item_revenue = _safe_float(funnel.get("itemRevenue"))
        matched_by = funnel.get("matchedBy") or "none"
        gsc_impressions = _get_page_gsc_impressions(page)
        ga4_sessions = _get_page_ga4_sessions(page)
        shopify_sales = _get_page_shopify_sales(page)
        has_critical = _page_has_open_critical_findings(page, open_findings)

        if item_views > HIGH_ITEM_VIEWS_THRESHOLD and items_added_to_cart == 0:
            candidates.append(
                (
                    item_views,
                    {
                        "page_id": page.id,
                        "category": "cro",
                        "severity": "high",
                        "priority": "high",
                        "title": "Molte view item ma pochi add to cart",
                        "description": (
                            f"GA4 mostra {item_views} view item ma zero add to cart "
                            f"nel periodo."
                        ),
                        "recommendation": (
                            "Migliora offerta, immagini, prezzo, trust e CTA sulla pagina prodotto."
                        ),
                        "how_to_validate": "Monitora View → Cart rate nei prossimi 14/30 giorni.",
                        "owner_type": "cro",
                    },
                )
            )

        if items_added_to_cart > HIGH_CART_THRESHOLD and items_purchased == 0:
            candidates.append(
                (
                    items_added_to_cart,
                    {
                        "page_id": page.id,
                        "category": "cro",
                        "severity": "high",
                        "priority": "high",
                        "title": "Add to cart senza acquisti GA4",
                        "description": (
                            f"GA4 mostra {items_added_to_cart} add to cart ma zero purchase "
                            f"nel periodo."
                        ),
                        "recommendation": (
                            "Analizza frizione tra carrello, checkout, spedizione e costi finali."
                        ),
                        "how_to_validate": "Controlla Cart → Purchase rate dopo gli interventi.",
                        "owner_type": "cro",
                    },
                )
            )

        if item_views > HIGH_ITEM_VIEWS_STRICT_THRESHOLD and items_purchased == 0:
            candidates.append(
                (
                    item_views,
                    {
                        "page_id": page.id,
                        "category": "cro",
                        "severity": "medium",
                        "priority": "medium",
                        "title": "View item elevate senza purchase",
                        "description": (
                            f"Il prodotto ha {item_views} view item ma zero purchase GA4."
                        ),
                        "recommendation": (
                            "Rafforza proposta commerciale e funnel completo fino all'acquisto."
                        ),
                        "how_to_validate": "Verifica purchase e item revenue dopo le modifiche.",
                        "owner_type": "cro",
                    },
                )
            )

        if item_revenue >= HIGH_ITEM_REVENUE_THRESHOLD and has_critical:
            candidates.append(
                (
                    int(item_revenue),
                    {
                        "page_id": page.id,
                        "category": "cro",
                        "severity": "high",
                        "priority": "high",
                        "title": "Item revenue alta con criticità aperte",
                        "description": (
                            f"GA4 item revenue {item_revenue:.2f} con problemi SEO/CRO ancora aperti."
                        ),
                        "recommendation": (
                            "Prioritizza fix su pagina prodotto per amplificare un funnel già monetizzato."
                        ),
                        "how_to_validate": "Confronta item revenue e conversioni dopo i fix.",
                        "owner_type": "cro",
                    },
                )
            )

        has_external_demand = (
            gsc_impressions >= HIGH_GSC_IMPRESSIONS
            or ga4_sessions >= HIGH_GA4_SESSIONS
            or shopify_sales > 0
        )
        if matched_by == "none" and has_external_demand:
            candidates.append(
                (
                    gsc_impressions + ga4_sessions + int(shopify_sales),
                    {
                        "page_id": page.id,
                        "category": "cro",
                        "severity": "medium",
                        "priority": "medium",
                        "title": "Funnel GA4 non abbinato al prodotto",
                        "description": (
                            "Il prodotto ha traffico o vendite ma GA4 non ha restituito "
                            "un match item-level affidabile."
                        ),
                        "recommendation": (
                            "Verifica tracking ecommerce GA4: item_id, SKU e Shopify channel."
                        ),
                        "how_to_validate": "Rilancia GA4 Ecommerce Funnel e controlla matchedBy.",
                        "owner_type": "dev",
                    },
                )
            )

    candidates.sort(key=lambda item: item[0], reverse=True)
    return [item[1] for item in candidates[:MAX_GA4_ECOMMERCE_FINDINGS]]


async def analyze_growth_audit_analytics_ecommerce(
    session: AsyncSession,
    *,
    project_id: UUID,
    run_id: UUID,
    days: int = 30,
) -> dict[str, Any]:
    run = await get_growth_audit_run(session, project_id, run_id)
    if run is None:
        raise GrowthAuditRunNotFoundError(f"Growth Audit run {run_id} not found")

    if run.status in _ACTIVE_RUN_STATUSES:
        raise GrowthAuditValidationError(
            "Impossibile sincronizzare GA4 Ecommerce mentre il run è ancora in corso."
        )

    project = await get_project_in_default_workspace(project_id, session)
    property_id = (project.google_analytics_property_id or "").strip()
    if not property_id:
        raise GrowthAuditValidationError(
            "Seleziona prima una proprietà GA4 per leggere eventi ecommerce prodotto."
        )

    pages = await list_growth_audit_pages(session, project_id, run_id)
    product_pages = _filter_product_pages(pages)
    if not product_pages:
        raise GrowthAuditValidationError(
            "Nessuna pagina prodotto collegata a Shopify in questa run."
        )

    normalized_days = _normalize_days(days)
    end_date = date.today() - timedelta(days=1)
    start_date = end_date - timedelta(days=normalized_days - 1)

    logger.info(
        "Starting GA4 ecommerce analysis project_id=%s run_id=%s days=%s",
        project_id,
        run_id,
        normalized_days,
    )

    await create_growth_audit_event(
        session,
        run_id=run.id,
        project_id=project_id,
        event_type="ga4_ecommerce_analysis_started",
        phase="ga4_ecommerce",
        message="Sincronizzazione funnel ecommerce GA4 avviata",
        progress_percent=run.progress_percent,
        payload={"days": normalized_days},
    )
    await session.flush()

    access_token = await get_valid_google_access_token(session, project_id, provider="ga4")
    report = await fetch_ga4_item_ecommerce_report(
        access_token,
        property_id=property_id,
        start_date=start_date,
        end_date=end_date,
    )
    rows = report.get("rows") or []

    variant_data_by_gid: dict[str, dict[str, Any]] = {}
    store = await get_shopify_store_for_project(project_id, session)
    if store is not None and store.connection_status == "connected":
        try:
            client = await get_shopify_client_for_store(store)
            product_gids = [page.source_entity_gid for page in product_pages if page.source_entity_gid]
            variant_data_by_gid = await _fetch_shopify_variant_match_data(
                shop_domain=client.shop_domain,
                access_token=client.access_token,
                product_gids=[gid for gid in product_gids if gid],
            )
        except ShopifyAPIError:
            logger.warning(
                "Shopify variant match data unavailable project_id=%s",
                project_id,
            )

    profiles = build_product_match_profiles(
        product_pages,
        variant_data_by_gid=variant_data_by_gid,
    )
    profile_by_page_id = {profile.page_id: profile for profile in profiles}
    page_aggregates, unmatched_items, ambiguous_items = match_ga4_rows_to_pages(profiles, rows)
    assigned_row_keys = build_assigned_row_keys(profiles, rows)
    has_ga4_rows = len(rows) > 0

    synced_at = _utcnow().isoformat()
    pages_updated = 0

    for page in product_pages:
        aggregate = page_aggregates.get(page.id)
        if aggregate:
            serialized_variants: dict[str, dict[str, Any]] = {}
            for variant_key, variant_bucket in (aggregate.get("variants") or {}).items():
                serialized_variants[variant_key] = {
                    **variant_bucket,
                    "itemIds": sorted(variant_bucket.get("itemIds") or []),
                    "itemNames": sorted(variant_bucket.get("itemNames") or []),
                }
            aggregate = {
                **aggregate,
                "matchedItemIds": sorted(aggregate.get("matchedItemIds") or []),
                "matchedItemNames": sorted(aggregate.get("matchedItemNames") or []),
                "variants": serialized_variants,
            }
        profile = profile_by_page_id.get(page.id)
        product_gid = (page.source_entity_gid or "").strip()
        variant_catalog = (variant_data_by_gid.get(product_gid) or {}).get("variants") or []
        match_debug = (
            build_page_match_debug(
                profile,
                aggregate=aggregate,
                rows=rows,
                assigned_row_keys=assigned_row_keys,
            )
            if profile
            else None
        )
        funnel_meta = _build_page_ga4_ecommerce_metadata(
            period_days=normalized_days,
            aggregate=aggregate,
            synced_at=synced_at,
            match_debug=match_debug,
            variant_catalog=variant_catalog,
        )
        page.page_metadata = {
            **(page.page_metadata or {}),
            "ga4Ecommerce": funnel_meta,
        }
        pages_updated += 1
        session.add(page)

    summary = _compute_run_ga4_ecommerce_summary(
        product_pages,
        period_days=normalized_days,
        synced_at=synced_at,
        unmatched_items=unmatched_items,
        ambiguous_items=ambiguous_items,
    )
    existing_summary = dict(run.summary or {})
    run.summary = {**existing_summary, "ga4Ecommerce": summary}

    findings_result = await session.execute(
        select(GrowthAuditFinding).where(
            GrowthAuditFinding.run_id == run.id,
            GrowthAuditFinding.project_id == project_id,
            GrowthAuditFinding.status == "open",
        )
    )
    open_findings = list(findings_result.scalars().all())
    finding_specs = (
        _build_ga4_ecommerce_findings(product_pages, open_findings) if has_ga4_rows else []
    )
    findings_created = 0
    for spec in finding_specs:
        finding = GrowthAuditFinding(
            run_id=run.id,
            page_id=spec["page_id"],
            project_id=project_id,
            category=spec["category"],
            severity=spec["severity"],
            priority=spec["priority"],
            title=spec["title"],
            description=spec.get("description"),
            recommendation=spec.get("recommendation"),
            how_to_validate=spec.get("how_to_validate"),
            status="open",
            finding_metadata={"source": "ga4_ecommerce"},
        )
        session.add(finding)
        findings_created += 1

    completion_message = (
        "Funnel ecommerce GA4 aggiornato. Nessun dato item-level trovato nel periodo selezionato."
        if not has_ga4_rows
        else f"Funnel ecommerce GA4 aggiornato: {summary['productsWithFunnelData']} prodotti con dati."
    )

    await create_growth_audit_event(
        session,
        run_id=run.id,
        project_id=project_id,
        event_type="ga4_ecommerce_analysis_completed",
        phase="ga4_ecommerce",
        message=completion_message,
        progress_percent=run.progress_percent,
        payload={
            "pagesUpdated": pages_updated,
            "findingsCreated": findings_created,
            "summary": summary,
        },
    )

    session.add(run)
    await session.commit()
    await session.refresh(run)

    return {
        "run": run,
        "summary": summary,
        "pages_updated": pages_updated,
        "findings_created": findings_created,
        "message": (
            "Funnel ecommerce GA4 aggiornato. Nessun dato item-level trovato nel periodo selezionato."
            if not has_ga4_rows
            else "Funnel ecommerce GA4 aggiornato"
        ),
    }
