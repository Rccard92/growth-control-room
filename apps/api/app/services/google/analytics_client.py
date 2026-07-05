"""Google Analytics 4 Admin + Data API client."""

from __future__ import annotations

from datetime import date
from typing import Any

import httpx

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
