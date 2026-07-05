"""Google Analytics 4 Admin + Data API client."""

from __future__ import annotations

import logging
import re
import unicodedata
from datetime import date
from typing import Any

import httpx

logger = logging.getLogger(__name__)

from app.services.google.exceptions import (
    GoogleAnalyticsPropertyError,
    GoogleApiRequestError,
    GoogleIntegrationPermissionError,
)

ANALYTICS_ADMIN_API_BASE = "https://analyticsadmin.googleapis.com/v1beta"
ANALYTICS_DATA_API_BASE = "https://analyticsdata.googleapis.com/v1beta"
REQUEST_TIMEOUT_SECONDS = 60.0

PRIMARY_METRICS = [
    "sessions",
    "totalUsers",
    "engagedSessions",
    "engagementRate",
    "averageSessionDuration",
]

EXTENDED_METRICS = [
    "conversions",
    "totalRevenue",
    "ecommercePurchases",
]

ITEM_ECOMMERCE_BASE_DIMENSIONS = ["itemId", "itemName"]
ITEM_ECOMMERCE_EXTENDED_DIMENSIONS = ["itemId", "itemName", "itemVariant"]
ITEM_ECOMMERCE_NAME_ONLY_DIMENSIONS = ["itemName"]
ITEM_ECOMMERCE_ID_ONLY_DIMENSIONS = ["itemId"]

ITEM_ECOMMERCE_BASE_METRICS = [
    "itemsViewed",
    "itemsAddedToCart",
    "itemsPurchased",
    "itemRevenue",
]

ITEM_ECOMMERCE_CHECKOUT_METRICS = ["itemsCheckedOut"]

ITEM_ECOMMERCE_OPTIONAL_METRICS = [
    "grossItemRevenue",
    "itemRefundAmount",
]

ITEM_ECOMMERCE_STANDARD_ROW_FIELDS = [
    "itemId",
    "itemName",
    "itemVariant",
    "itemsViewed",
    "itemsAddedToCart",
    "itemsCheckedOut",
    "itemsPurchased",
    "itemRevenue",
]

ITEM_FLOAT_METRICS = {"itemRevenue", "grossItemRevenue", "itemRefundAmount"}

ITEM_ECOMMERCE_INCOMPATIBLE_MESSAGE = (
    "GA4 ha rifiutato le metriche ecommerce item-level per questa proprietà. "
    "Verifica che gli eventi ecommerce Shopify siano presenti in GA4 e che la proprietà "
    "supporti le metriche itemsViewed/itemsAddedToCart/itemsPurchased/itemRevenue."
)


def _auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def _map_http_error(status_code: int, *, property_id: str | None = None) -> Exception:
    if status_code in (401, 403):
        return GoogleIntegrationPermissionError(
            "Permessi insufficienti per Google Analytics 4.",
            status_code=status_code,
            integration="ga4",
        )
    if status_code == 404:
        return GoogleAnalyticsPropertyError(
            "Proprietà GA4 non trovata o non accessibile.",
            property_id=property_id,
        )
    return GoogleApiRequestError(
        "Google Analytics 4 ha rifiutato la richiesta.",
        status_code=status_code,
        error_code="google_analytics_http_error",
    )


def _is_metric_incompatible_error(status_code: int, payload: dict[str, Any] | None) -> bool:
    if status_code != 400 or not payload:
        return False
    message = str(payload.get("error", {}).get("message", "")).lower()
    return "metric" in message or "incompatible" in message or "invalid" in message


def _extract_property_id(property_name: str) -> str:
    if property_name.startswith("properties/"):
        return property_name.split("/", 1)[1]
    return property_name


async def fetch_ga4_account_summaries(access_token: str) -> list[dict[str, Any]]:
    url = f"{ANALYTICS_ADMIN_API_BASE}/accountSummaries"
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.get(url, headers=_auth_headers(access_token))
    except httpx.TimeoutException as exc:
        raise GoogleApiRequestError(
            "Timeout durante la chiamata a Google Analytics Admin API.",
            error_code="google_analytics_timeout",
        ) from exc
    except httpx.HTTPError as exc:
        raise GoogleApiRequestError(
            "Impossibile contattare Google Analytics Admin API.",
            error_code="google_analytics_network_error",
        ) from exc

    if response.status_code >= 400:
        raise _map_http_error(response.status_code)

    try:
        payload = response.json()
    except ValueError as exc:
        raise GoogleApiRequestError(
            "Risposta Google Analytics Admin API non valida.",
            error_code="google_analytics_invalid_json",
        ) from exc

    summaries = payload.get("accountSummaries") or []
    if not isinstance(summaries, list):
        return []

    properties: list[dict[str, Any]] = []
    for account_summary in summaries:
        if not isinstance(account_summary, dict):
            continue
        account = account_summary.get("account") or ""
        account_display_name = account_summary.get("displayName") or ""
        property_summaries = account_summary.get("propertySummaries") or []
        if not isinstance(property_summaries, list):
            continue
        for property_summary in property_summaries:
            if not isinstance(property_summary, dict):
                continue
            property_name = property_summary.get("property") or ""
            if not property_name:
                continue
            properties.append(
                {
                    "account": account,
                    "accountDisplayName": account_display_name,
                    "property": property_name,
                    "propertyId": _extract_property_id(property_name),
                    "propertyDisplayName": property_summary.get("displayName") or property_name,
                }
            )
    return properties


async def _run_ga4_report(
    access_token: str,
    *,
    property_id: str,
    start_date: date,
    end_date: date,
    metrics: list[str],
    limit: int,
) -> dict[str, Any]:
    url = f"{ANALYTICS_DATA_API_BASE}/properties/{property_id}:runReport"
    body = {
        "dateRanges": [
            {
                "startDate": start_date.isoformat(),
                "endDate": end_date.isoformat(),
            }
        ],
        "dimensions": [{"name": "landingPagePlusQueryString"}],
        "metrics": [{"name": metric} for metric in metrics],
        "limit": str(limit),
    }
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.post(
                url,
                headers={**_auth_headers(access_token), "Content-Type": "application/json"},
                json=body,
            )
    except httpx.TimeoutException as exc:
        raise GoogleApiRequestError(
            "Timeout durante la chiamata a Google Analytics Data API.",
            error_code="google_analytics_timeout",
        ) from exc
    except httpx.HTTPError as exc:
        raise GoogleApiRequestError(
            "Impossibile contattare Google Analytics Data API.",
            error_code="google_analytics_network_error",
        ) from exc

    error_payload: dict[str, Any] | None = None
    if response.status_code >= 400:
        try:
            error_payload = response.json()
        except ValueError:
            error_payload = None
        if _is_metric_incompatible_error(response.status_code, error_payload):
            return {"_metric_incompatible": True, "error": error_payload}
        raise _map_http_error(response.status_code, property_id=property_id)

    try:
        return response.json()
    except ValueError as exc:
        raise GoogleApiRequestError(
            "Risposta Google Analytics Data API non valida.",
            error_code="google_analytics_invalid_json",
        ) from exc


def _parse_report_rows(payload: dict[str, Any], metrics: list[str]) -> list[dict[str, Any]]:
    rows = payload.get("rows") or []
    if not isinstance(rows, list):
        return []

    parsed_rows: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        dimension_values = row.get("dimensionValues") or []
        metric_values = row.get("metricValues") or []
        landing_path = ""
        if dimension_values and isinstance(dimension_values[0], dict):
            landing_path = str(dimension_values[0].get("value") or "")

        metrics_map: dict[str, Any] = {}
        for index, metric_name in enumerate(metrics):
            if index >= len(metric_values):
                break
            metric_entry = metric_values[index]
            if not isinstance(metric_entry, dict):
                continue
            raw_value = metric_entry.get("value")
            if metric_name in ("engagementRate",):
                try:
                    metrics_map[metric_name] = float(raw_value or 0)
                except (TypeError, ValueError):
                    metrics_map[metric_name] = 0.0
            elif metric_name == "averageSessionDuration":
                try:
                    metrics_map[metric_name] = float(raw_value or 0)
                except (TypeError, ValueError):
                    metrics_map[metric_name] = 0.0
            elif metric_name == "totalRevenue":
                try:
                    metrics_map[metric_name] = float(raw_value or 0)
                except (TypeError, ValueError):
                    metrics_map[metric_name] = 0.0
            else:
                try:
                    metrics_map[metric_name] = int(float(raw_value or 0))
                except (TypeError, ValueError):
                    metrics_map[metric_name] = 0

        parsed_rows.append(
            {
                "landingPagePlusQueryString": landing_path,
                **metrics_map,
            }
        )
    return parsed_rows


async def fetch_ga4_landing_pages_report(
    access_token: str,
    *,
    property_id: str,
    start_date: date,
    end_date: date,
    limit: int = 10000,
) -> dict[str, Any]:
    normalized_property_id = _extract_property_id(property_id)
    extended_metrics = [*PRIMARY_METRICS, *EXTENDED_METRICS]

    extended_payload = await _run_ga4_report(
        access_token,
        property_id=normalized_property_id,
        start_date=start_date,
        end_date=end_date,
        metrics=extended_metrics,
        limit=limit,
    )

    if extended_payload.get("_metric_incompatible"):
        primary_payload = await _run_ga4_report(
            access_token,
            property_id=normalized_property_id,
            start_date=start_date,
            end_date=end_date,
            metrics=PRIMARY_METRICS,
            limit=limit,
        )
        rows = _parse_report_rows(primary_payload, PRIMARY_METRICS)
        return {
            "propertyId": normalized_property_id,
            "metricsUsed": PRIMARY_METRICS,
            "rows": rows,
        }

    rows = _parse_report_rows(extended_payload, extended_metrics)
    return {
        "propertyId": normalized_property_id,
        "metricsUsed": extended_metrics,
        "rows": rows,
    }


async def _run_ga4_item_report(
    access_token: str,
    *,
    property_id: str,
    start_date: date,
    end_date: date,
    dimensions: list[str],
    metrics: list[str],
    limit: int,
) -> dict[str, Any]:
    url = f"{ANALYTICS_DATA_API_BASE}/properties/{property_id}:runReport"
    body = {
        "dateRanges": [
            {
                "startDate": start_date.isoformat(),
                "endDate": end_date.isoformat(),
            }
        ],
        "dimensions": [{"name": dimension} for dimension in dimensions],
        "metrics": [{"name": metric} for metric in metrics],
        "limit": str(limit),
    }
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.post(
                url,
                headers={**_auth_headers(access_token), "Content-Type": "application/json"},
                json=body,
            )
    except httpx.TimeoutException as exc:
        raise GoogleApiRequestError(
            "Timeout durante la chiamata a Google Analytics Data API.",
            error_code="google_analytics_timeout",
        ) from exc
    except httpx.HTTPError as exc:
        raise GoogleApiRequestError(
            "Impossibile contattare Google Analytics Data API.",
            error_code="google_analytics_network_error",
        ) from exc

    error_payload: dict[str, Any] | None = None
    if response.status_code >= 400:
        try:
            error_payload = response.json()
        except ValueError:
            error_payload = None
        if _is_metric_incompatible_error(response.status_code, error_payload):
            logger.warning(
                "GA4 item ecommerce report incompatible property=%s dimensions=%s metrics=%s message=%s",
                property_id,
                dimensions,
                metrics,
                _extract_google_error_message(error_payload),
            )
            return {"_metric_incompatible": True, "error": error_payload}
        raise _map_http_error(response.status_code, property_id=property_id)

    try:
        return response.json()
    except ValueError as exc:
        raise GoogleApiRequestError(
            "Risposta Google Analytics Data API non valida.",
            error_code="google_analytics_invalid_json",
        ) from exc


def _extract_google_error_message(payload: dict[str, Any] | None) -> str:
    if not payload:
        return ""
    message = str(payload.get("error", {}).get("message", "")).strip()
    if not message:
        return ""
    message = re.sub(r"\s+", " ", message)
    return message[:300]


def _normalize_item_match_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    without_accents = "".join(char for char in normalized if not unicodedata.combining(char))
    collapsed = re.sub(r"\s+", " ", without_accents.strip().lower())
    return collapsed


def _item_row_merge_key(row: dict[str, Any]) -> str:
    item_id = str(row.get("itemId") or "").strip()
    if item_id:
        return f"id:{item_id}"
    item_name = str(row.get("itemName") or "").strip()
    normalized_name = _normalize_item_match_text(item_name)
    if normalized_name:
        return f"name:{normalized_name}"
    return f"raw:{item_name}"


def _merge_item_rows(target: dict[str, Any], source: dict[str, Any]) -> None:
    for field in ("itemId", "itemName", "itemVariant"):
        if not target.get(field) and source.get(field):
            target[field] = source[field]

    for metric in (
        "itemsViewed",
        "itemsAddedToCart",
        "itemsCheckedOut",
        "itemsPurchased",
        "itemRevenue",
    ):
        if metric not in source:
            continue
        source_value = source.get(metric)
        if source_value in (None, "", 0, 0.0):
            continue
        if metric == "itemRevenue":
            target[metric] = round(_safe_item_float(target.get(metric)) + _safe_item_float(source_value), 2)
        else:
            target[metric] = int(target.get(metric) or 0) + int(source_value or 0)


def _safe_item_float(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _normalize_item_rows(
    rows: list[dict[str, Any]],
    *,
    missing_metrics: list[str] | None = None,
) -> list[dict[str, Any]]:
    missing = set(missing_metrics or [])
    normalized_rows: list[dict[str, Any]] = []
    for row in rows:
        normalized_rows.append(
            {
                "itemId": str(row.get("itemId") or ""),
                "itemName": str(row.get("itemName") or ""),
                "itemVariant": str(row.get("itemVariant") or ""),
                "itemsViewed": int(row.get("itemsViewed") or 0),
                "itemsAddedToCart": int(row.get("itemsAddedToCart") or 0),
                "itemsCheckedOut": 0 if "itemsCheckedOut" in missing else int(row.get("itemsCheckedOut") or 0),
                "itemsPurchased": int(row.get("itemsPurchased") or 0),
                "itemRevenue": round(_safe_item_float(row.get("itemRevenue")), 2),
            }
        )
    return normalized_rows


def _merge_item_report_rows(
    base_rows: list[dict[str, Any]],
    extra_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    merged_by_key: dict[str, dict[str, Any]] = {}
    for row in base_rows:
        key = _item_row_merge_key(row)
        merged_by_key[key] = dict(row)

    for row in extra_rows:
        key = _item_row_merge_key(row)
        if key not in merged_by_key:
            merged_by_key[key] = {
                "itemId": str(row.get("itemId") or ""),
                "itemName": str(row.get("itemName") or ""),
                "itemVariant": str(row.get("itemVariant") or ""),
                "itemsViewed": 0,
                "itemsAddedToCart": 0,
                "itemsCheckedOut": 0,
                "itemsPurchased": 0,
                "itemRevenue": 0.0,
            }
        _merge_item_rows(merged_by_key[key], row)

    return list(merged_by_key.values())


def _parse_item_metric_value(metric_name: str, raw_value: Any) -> int | float:
    if metric_name in ITEM_FLOAT_METRICS:
        try:
            return float(raw_value or 0)
        except (TypeError, ValueError):
            return 0.0
    try:
        return int(float(raw_value or 0))
    except (TypeError, ValueError):
        return 0


def _parse_item_report_rows(
    payload: dict[str, Any],
    *,
    dimensions: list[str],
    metrics: list[str],
) -> list[dict[str, Any]]:
    rows = payload.get("rows") or []
    if not isinstance(rows, list):
        return []

    parsed_rows: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        dimension_values = row.get("dimensionValues") or []
        metric_values = row.get("metricValues") or []

        dimension_map: dict[str, str] = {}
        for index, dimension_name in enumerate(dimensions):
            if index >= len(dimension_values):
                break
            dimension_entry = dimension_values[index]
            if not isinstance(dimension_entry, dict):
                continue
            dimension_map[dimension_name] = str(dimension_entry.get("value") or "")

        metrics_map: dict[str, Any] = {}
        for index, metric_name in enumerate(metrics):
            if index >= len(metric_values):
                break
            metric_entry = metric_values[index]
            if not isinstance(metric_entry, dict):
                continue
            metrics_map[metric_name] = _parse_item_metric_value(
                metric_name,
                metric_entry.get("value"),
            )

        parsed_rows.append(
            {
                "itemId": dimension_map.get("itemId", ""),
                "itemName": dimension_map.get("itemName", ""),
                "itemVariant": dimension_map.get("itemVariant", ""),
                **metrics_map,
            }
        )
    return parsed_rows


async def _try_ga4_item_report(
    access_token: str,
    *,
    property_id: str,
    start_date: date,
    end_date: date,
    dimensions: list[str],
    metrics: list[str],
    limit: int,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    payload = await _run_ga4_item_report(
        access_token,
        property_id=property_id,
        start_date=start_date,
        end_date=end_date,
        dimensions=dimensions,
        metrics=metrics,
        limit=limit,
    )
    if payload.get("_metric_incompatible"):
        return None, []
    rows = _parse_item_report_rows(payload, dimensions=dimensions, metrics=metrics)
    return payload, rows


async def fetch_ga4_item_ecommerce_report(
    access_token: str,
    *,
    property_id: str,
    start_date: date,
    end_date: date,
    limit: int = 10000,
) -> dict[str, Any]:
    """Fetch GA4 item-level ecommerce funnel metrics with progressive compatibility fallback."""
    normalized_property_id = _extract_property_id(property_id)
    missing_metrics: list[str] = []

    base_attempts = [
        ITEM_ECOMMERCE_BASE_DIMENSIONS,
        ITEM_ECOMMERCE_NAME_ONLY_DIMENSIONS,
        ITEM_ECOMMERCE_ID_ONLY_DIMENSIONS,
    ]

    base_dimensions: list[str] | None = None
    base_rows: list[dict[str, Any]] = []

    for dimensions in base_attempts:
        payload, rows = await _try_ga4_item_report(
            access_token,
            property_id=normalized_property_id,
            start_date=start_date,
            end_date=end_date,
            dimensions=dimensions,
            metrics=ITEM_ECOMMERCE_BASE_METRICS,
            limit=limit,
        )
        if payload is not None:
            base_dimensions = dimensions
            base_rows = rows
            break

    if base_dimensions is None:
        raise GoogleApiRequestError(
            ITEM_ECOMMERCE_INCOMPATIBLE_MESSAGE,
            status_code=502,
            error_code="google_analytics_item_report_incompatible",
        )

    merged_rows = list(base_rows)
    metrics_used = list(ITEM_ECOMMERCE_BASE_METRICS)

    checkout_payload, checkout_rows = await _try_ga4_item_report(
        access_token,
        property_id=normalized_property_id,
        start_date=start_date,
        end_date=end_date,
        dimensions=base_dimensions,
        metrics=ITEM_ECOMMERCE_CHECKOUT_METRICS,
        limit=limit,
    )
    if checkout_payload is not None:
        merged_rows = _merge_item_report_rows(merged_rows, checkout_rows)
        metrics_used.extend(ITEM_ECOMMERCE_CHECKOUT_METRICS)
    else:
        missing_metrics.extend(ITEM_ECOMMERCE_CHECKOUT_METRICS)

    if base_dimensions != ITEM_ECOMMERCE_EXTENDED_DIMENSIONS:
        variant_payload, variant_rows = await _try_ga4_item_report(
            access_token,
            property_id=normalized_property_id,
            start_date=start_date,
            end_date=end_date,
            dimensions=ITEM_ECOMMERCE_EXTENDED_DIMENSIONS,
            metrics=ITEM_ECOMMERCE_BASE_METRICS,
            limit=limit,
        )
        if variant_payload is not None and variant_rows:
            merged_rows = _merge_item_report_rows(merged_rows, variant_rows)
            if "itemVariant" not in base_dimensions:
                base_dimensions = ITEM_ECOMMERCE_EXTENDED_DIMENSIONS

    normalized_rows = _normalize_item_rows(merged_rows, missing_metrics=missing_metrics)

    return {
        "propertyId": normalized_property_id,
        "dimensionsUsed": base_dimensions,
        "metricsUsed": metrics_used,
        "missingMetrics": missing_metrics,
        "rows": normalized_rows,
    }
