"""Chrome UX Report API client."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import httpx

from app.core.config import settings
from app.services.google.exceptions import GoogleApiRequestError, GoogleIntegrationNotConfiguredError

CRUX_API_URL = "https://chromeuxreport.googleapis.com/v1/records:queryRecord"
REQUEST_TIMEOUT_SECONDS = 60.0


def _ensure_crux_configured() -> None:
    if settings.google_crux_api_key and settings.google_crux_api_key.strip():
        return
    raise GoogleIntegrationNotConfiguredError(
        "Chrome UX Report non configurato. Imposta GOOGLE_CRUX_API_KEY.",
        integration="google_crux",
    )


def _extract_origin(url: str) -> str | None:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return None
    return f"{parsed.scheme}://{parsed.netloc}"


async def _query_crux_record(body: dict[str, str]) -> dict[str, Any] | None:
    params = {"key": settings.google_crux_api_key or ""}
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.post(CRUX_API_URL, params=params, json=body)
    except httpx.TimeoutException as exc:
        raise GoogleApiRequestError(
            "Timeout durante la chiamata a Chrome UX Report.",
            error_code="google_crux_timeout",
        ) from exc
    except httpx.HTTPError as exc:
        raise GoogleApiRequestError(
            "Impossibile contattare Chrome UX Report.",
            error_code="google_crux_network_error",
        ) from exc

    if response.status_code == 404:
        return None
    if response.status_code >= 400:
        raise GoogleApiRequestError(
            "Chrome UX Report ha rifiutato la richiesta.",
            status_code=response.status_code,
            error_code="google_crux_http_error",
        )

    try:
        data: dict[str, Any] = response.json()
    except ValueError as exc:
        raise GoogleApiRequestError(
            "Risposta Chrome UX Report non valida.",
            error_code="google_crux_invalid_json",
        ) from exc

    record = data.get("record")
    if not record:
        return None
    return data


async def fetch_crux_record(
    url: str,
    *,
    form_factor: str = "PHONE",
) -> dict[str, Any] | None:
    _ensure_crux_configured()

    url_result = await _query_crux_record({"url": url, "formFactor": form_factor})
    if url_result is not None:
        return {**url_result, "_cruxSource": "url"}

    origin = _extract_origin(url)
    if origin is None:
        return None

    origin_result = await _query_crux_record({"origin": origin, "formFactor": form_factor})
    if origin_result is not None:
        return {**origin_result, "_cruxSource": "origin"}
    return None
