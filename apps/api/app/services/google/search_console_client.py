"""Google Search Console API client."""

from __future__ import annotations

from datetime import date
from typing import Any
from urllib.parse import quote

import httpx

from app.services.google.exceptions import (
    GoogleApiRequestError,
    GoogleIntegrationPermissionError,
    GoogleSearchConsolePropertyError,
)

SEARCH_CONSOLE_API_BASE = "https://www.googleapis.com/webmasters/v3"
REQUEST_TIMEOUT_SECONDS = 60.0


def _encode_site_url(site_url: str) -> str:
    return quote(site_url, safe="")


def _auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def _map_http_error(status_code: int, *, site_url: str | None = None) -> Exception:
    if status_code in (401, 403):
        return GoogleIntegrationPermissionError(
            "Permessi insufficienti per Google Search Console.",
            status_code=status_code,
            integration="google_search_console",
        )
    if status_code == 404:
        return GoogleSearchConsolePropertyError(
            "Proprietà Search Console non trovata.",
            site_url=site_url,
        )
    return GoogleApiRequestError(
        "Google Search Console ha rifiutato la richiesta.",
        status_code=status_code,
        error_code="google_search_console_http_error",
    )


async def fetch_search_console_sites(access_token: str) -> list[dict[str, Any]]:
    url = f"{SEARCH_CONSOLE_API_BASE}/sites"
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.get(url, headers=_auth_headers(access_token))
    except httpx.TimeoutException as exc:
        raise GoogleApiRequestError(
            "Timeout durante la chiamata a Google Search Console.",
            error_code="google_search_console_timeout",
        ) from exc
    except httpx.HTTPError as exc:
        raise GoogleApiRequestError(
            "Impossibile contattare Google Search Console.",
            error_code="google_search_console_network_error",
        ) from exc

    if response.status_code >= 400:
        raise _map_http_error(response.status_code)

    try:
        payload = response.json()
    except ValueError as exc:
        raise GoogleApiRequestError(
            "Risposta Search Console non valida.",
            error_code="google_search_console_invalid_json",
        ) from exc

    site_entries = payload.get("siteEntry", [])
    if not isinstance(site_entries, list):
        return []

    sites: list[dict[str, Any]] = []
    for entry in site_entries:
        if not isinstance(entry, dict):
            continue
        site_url = entry.get("siteUrl")
        if not isinstance(site_url, str) or not site_url.strip():
            continue
        sites.append(
            {
                "siteUrl": site_url,
                "permissionLevel": entry.get("permissionLevel"),
            }
        )
    return sites


async def fetch_search_console_search_analytics(
    access_token: str,
    *,
    site_url: str,
    start_date: date,
    end_date: date,
    dimensions: list[str],
    row_limit: int = 25000,
    start_row: int = 0,
    dimension_filter_groups: list[dict] | None = None,
) -> dict[str, Any]:
    encoded_site = _encode_site_url(site_url)
    url = f"{SEARCH_CONSOLE_API_BASE}/sites/{encoded_site}/searchAnalytics/query"
    body: dict[str, Any] = {
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "dimensions": dimensions,
        "rowLimit": row_limit,
        "startRow": start_row,
    }
    if dimension_filter_groups:
        body["dimensionFilterGroups"] = dimension_filter_groups

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.post(
                url,
                headers={**_auth_headers(access_token), "Content-Type": "application/json"},
                json=body,
            )
    except httpx.TimeoutException as exc:
        raise GoogleApiRequestError(
            "Timeout durante la query Search Console.",
            error_code="google_search_console_timeout",
        ) from exc
    except httpx.HTTPError as exc:
        raise GoogleApiRequestError(
            "Impossibile contattare Google Search Console.",
            error_code="google_search_console_network_error",
        ) from exc

    if response.status_code >= 400:
        raise _map_http_error(response.status_code, site_url=site_url)

    try:
        payload = response.json()
    except ValueError as exc:
        raise GoogleApiRequestError(
            "Risposta Search Console non valida.",
            error_code="google_search_console_invalid_json",
        ) from exc

    return payload if isinstance(payload, dict) else {"rows": []}
