"""PageSpeed Insights API client."""

from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings
from app.services.google.exceptions import GoogleApiRequestError, GoogleIntegrationNotConfiguredError

PAGESPEED_API_URL = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
DEFAULT_CATEGORIES = ("performance", "accessibility", "best-practices", "seo")
REQUEST_TIMEOUT_SECONDS = 90.0


def _ensure_pagespeed_configured() -> None:
    if settings.google_pagespeed_api_key and settings.google_pagespeed_api_key.strip():
        return
    raise GoogleIntegrationNotConfiguredError(
        "PageSpeed Insights non configurato. Imposta GOOGLE_PAGESPEED_API_KEY.",
        integration="google_pagespeed",
    )


async def fetch_pagespeed_insights(
    url: str,
    *,
    strategy: str = "mobile",
    categories: list[str] | None = None,
) -> dict[str, Any]:
    _ensure_pagespeed_configured()
    resolved_categories = categories or list(DEFAULT_CATEGORIES)
    params: list[tuple[str, str]] = [
        ("url", url),
        ("key", settings.google_pagespeed_api_key or ""),
        ("strategy", strategy),
    ]
    for category in resolved_categories:
        params.append(("category", category))

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.get(PAGESPEED_API_URL, params=params)
    except httpx.TimeoutException as exc:
        raise GoogleApiRequestError(
            "Timeout durante la chiamata a PageSpeed Insights.",
            error_code="google_pagespeed_timeout",
        ) from exc
    except httpx.HTTPError as exc:
        raise GoogleApiRequestError(
            "Impossibile contattare PageSpeed Insights.",
            error_code="google_pagespeed_network_error",
        ) from exc

    if response.status_code >= 400:
        raise GoogleApiRequestError(
            "PageSpeed Insights ha rifiutato la richiesta.",
            status_code=response.status_code,
            error_code="google_pagespeed_http_error",
        )

    try:
        data: dict[str, Any] = response.json()
    except ValueError as exc:
        raise GoogleApiRequestError(
            "Risposta PageSpeed Insights non valida.",
            error_code="google_pagespeed_invalid_json",
        ) from exc

    if not data.get("lighthouseResult"):
        raise GoogleApiRequestError(
            "Risposta PageSpeed Insights incompleta.",
            error_code="google_pagespeed_invalid_payload",
        )

    return data
