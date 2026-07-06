"""DataForSEO HTTP client."""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

import httpx

from app.core.config import settings
from app.services.dataforseo.constants import (
    DATAFORSEO_BASE_URL,
    DEFAULT_LANGUAGE_CODE,
    DEFAULT_LOCATION_CODE,
    ENDPOINT_KEYWORDS_FOR_KEYWORDS_LIVE,
    ENDPOINT_SEARCH_VOLUME_LIVE,
    ENDPOINT_SERP_ORGANIC_LIVE_ADVANCED,
    ENDPOINT_USER_DATA,
    RAW_PREVIEW_MAX_BYTES,
)
from app.services.dataforseo.exceptions import (
    DataForSeoApiError,
    DataForSeoNotConfiguredError,
    DataForSeoRealCallsDisabledError,
)
from app.services.dataforseo.search_volume_normalizer import (
    normalize_search_volume_batch_response,
)

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT_SECONDS = 90.0


def _ensure_dataforseo_configured() -> None:
    if settings.dataforseo_configured:
        return
    raise DataForSeoNotConfiguredError(
        "DataForSEO non configurato. Imposta DATAFORSEO_LOGIN e DATAFORSEO_PASSWORD.",
    )


def _ensure_real_calls_enabled() -> None:
    if settings.dataforseo_enable_real_calls:
        return
    raise DataForSeoRealCallsDisabledError("DataForSEO real calls disabled.")


def _basic_auth() -> httpx.BasicAuth:
    return httpx.BasicAuth(
        settings.dataforseo_login or "",
        settings.dataforseo_password or "",
    )


def truncate_json_preview(data: Any, *, max_bytes: int = RAW_PREVIEW_MAX_BYTES) -> Any:
    try:
        encoded = json.dumps(data, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        encoded = str(data)
    if len(encoded.encode("utf-8")) <= max_bytes:
        return data
    return {"truncated": True, "preview": encoded[: max_bytes - 32] + "…"}


def _extract_cost_usd(payload: dict[str, Any]) -> float | None:
    tasks = payload.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        return None
    total = 0.0
    found = False
    for task in tasks:
        if not isinstance(task, dict):
            continue
        cost = task.get("cost")
        if cost is not None:
            total += float(cost)
            found = True
    return total if found else None


def _normalize_post_response(
    *,
    endpoint: str,
    status_code: int,
    payload: dict[str, Any],
) -> dict[str, Any]:
    tasks = payload.get("tasks")
    task_count = len(tasks) if isinstance(tasks, list) else 0
    cost_usd = _extract_cost_usd(payload)
    logger.info(
        "DataForSEO call endpoint=%s status=%s cost=%s task_count=%s",
        endpoint,
        status_code,
        cost_usd,
        task_count,
    )
    return {
        "endpoint": endpoint,
        "status_code": status_code,
        "cost_usd": cost_usd,
        "task_count": task_count,
        "tasks": tasks if isinstance(tasks, list) else [],
        "raw": payload,
    }


async def get_dataforseo(endpoint: str) -> dict[str, Any]:
    _ensure_dataforseo_configured()
    url = f"{DATAFORSEO_BASE_URL}{endpoint}"
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.get(url, auth=_basic_auth())
    except httpx.TimeoutException as exc:
        raise DataForSeoApiError(
            "Timeout durante la chiamata a DataForSEO.",
            error_code="dataforseo_timeout",
        ) from exc
    except httpx.HTTPError as exc:
        raise DataForSeoApiError(
            "Impossibile contattare DataForSEO.",
            error_code="dataforseo_network_error",
        ) from exc

    try:
        payload: dict[str, Any] = response.json()
    except ValueError as exc:
        raise DataForSeoApiError(
            "Risposta DataForSEO non valida.",
            status_code=response.status_code,
            error_code="dataforseo_invalid_json",
        ) from exc

    if response.status_code >= 400:
        raise DataForSeoApiError(
            "DataForSEO ha rifiutato la richiesta.",
            status_code=response.status_code,
            error_code="dataforseo_http_error",
        )

    return _normalize_post_response(
        endpoint=endpoint,
        status_code=response.status_code,
        payload=payload,
    )


async def post_dataforseo(endpoint: str, payload: list[dict[str, Any]]) -> dict[str, Any]:
    _ensure_dataforseo_configured()
    _ensure_real_calls_enabled()
    url = f"{DATAFORSEO_BASE_URL}{endpoint}"
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.post(
                url,
                auth=_basic_auth(),
                json=payload,
                headers={"Content-Type": "application/json"},
            )
    except httpx.TimeoutException as exc:
        raise DataForSeoApiError(
            "Timeout durante la chiamata a DataForSEO.",
            error_code="dataforseo_timeout",
        ) from exc
    except httpx.HTTPError as exc:
        raise DataForSeoApiError(
            "Impossibile contattare DataForSEO.",
            error_code="dataforseo_network_error",
        ) from exc

    try:
        body: dict[str, Any] = response.json()
    except ValueError as exc:
        raise DataForSeoApiError(
            "Risposta DataForSEO non valida.",
            status_code=response.status_code,
            error_code="dataforseo_invalid_json",
        ) from exc

    if response.status_code >= 400:
        raise DataForSeoApiError(
            "DataForSEO ha rifiutato la richiesta.",
            status_code=response.status_code,
            error_code="dataforseo_http_error",
        )

    return _normalize_post_response(
        endpoint=endpoint,
        status_code=response.status_code,
        payload=body,
    )


async def get_dataforseo_account_status() -> dict[str, Any]:
    result = await get_dataforseo(ENDPOINT_USER_DATA)
    raw = result.get("raw") or {}
    tasks = raw.get("tasks") if isinstance(raw.get("tasks"), list) else []
    account: dict[str, Any] = {}
    if tasks and isinstance(tasks[0], dict):
        task_result = tasks[0].get("result")
        if isinstance(task_result, list) and task_result and isinstance(task_result[0], dict):
            money = task_result[0].get("money")
            if isinstance(money, dict):
                account["balanceUsd"] = money.get("balance")
                account["totalDepositedUsd"] = money.get("total")
    return {
        "verified": True,
        "account": account,
        "rawPreview": truncate_json_preview(raw),
    }


def build_request_hash(endpoint: str, payload: list[dict[str, Any]]) -> str:
    digest_input = json.dumps(
        {"endpoint": endpoint, "payload": payload},
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(digest_input.encode("utf-8")).hexdigest()


def summarize_search_volume_response(result: dict[str, Any], keyword: str) -> dict[str, Any]:
    summary = normalize_search_volume_batch_response(result, [keyword])
    return {
        "keyword": keyword,
        "keywordCount": summary.get("keywordCount", 1),
        "totalCostUsd": summary.get("totalCostUsd"),
        "averageCostPerKeywordUsd": summary.get("averageCostPerKeywordUsd"),
        "itemsCount": summary.get("itemsCount", 1),
        "items": summary.get("results", [])[:5],
        "results": summary.get("results", []),
    }


def summarize_keyword_ideas_response(result: dict[str, Any], keyword: str) -> dict[str, Any]:
    ideas: list[str] = []
    tasks = result.get("tasks") or []
    for task in tasks:
        if not isinstance(task, dict):
            continue
        task_results = task.get("result")
        if not isinstance(task_results, list):
            continue
        for row in task_results:
            if not isinstance(row, dict):
                continue
            for item in row.get("items") or []:
                if isinstance(item, dict) and item.get("keyword"):
                    ideas.append(str(item["keyword"]))
                elif isinstance(item, str):
                    ideas.append(item)
            if row.get("keyword") and not row.get("items"):
                ideas.append(str(row["keyword"]))
    unique_ideas = list(dict.fromkeys(ideas))
    return {
        "seedKeyword": keyword,
        "ideasCount": len(unique_ideas),
        "topIdeas": unique_ideas[:5],
    }


def summarize_serp_response(result: dict[str, Any], keyword: str) -> dict[str, Any]:
    organic: list[dict[str, Any]] = []
    tasks = result.get("tasks") or []
    for task in tasks:
        if not isinstance(task, dict):
            continue
        task_results = task.get("result")
        if not isinstance(task_results, list):
            continue
        for row in task_results:
            if not isinstance(row, dict):
                continue
            for item in row.get("items") or []:
                if not isinstance(item, dict):
                    continue
                if item.get("type") == "organic" or item.get("url"):
                    organic.append(
                        {
                            "title": item.get("title"),
                            "url": item.get("url"),
                            "position": item.get("rank_group") or item.get("rank_absolute"),
                        }
                    )
    return {
        "keyword": keyword,
        "resultCount": len(organic),
        "topResults": organic[:3],
    }


async def safe_test_keyword_search_volume_batch(
    keywords: list[str],
    *,
    location_code: int = DEFAULT_LOCATION_CODE,
    language_code: str = DEFAULT_LANGUAGE_CODE,
) -> dict[str, Any]:
    payload = [
        {
            "location_code": location_code,
            "language_code": language_code,
            "keywords": keywords,
        }
    ]
    result = await post_dataforseo(ENDPOINT_SEARCH_VOLUME_LIVE, payload)
    result["summary"] = normalize_search_volume_batch_response(result, keywords)
    result["rawPreview"] = truncate_json_preview(result.get("raw"))
    return result


async def safe_test_keyword_search_volume(
    keyword: str,
    *,
    location_code: int = DEFAULT_LOCATION_CODE,
    language_code: str = DEFAULT_LANGUAGE_CODE,
) -> dict[str, Any]:
    payload = [
        {
            "location_code": location_code,
            "language_code": language_code,
            "keywords": [keyword],
        }
    ]
    result = await post_dataforseo(ENDPOINT_SEARCH_VOLUME_LIVE, payload)
    result["summary"] = summarize_search_volume_response(result, keyword)
    result["rawPreview"] = truncate_json_preview(result.get("raw"))
    return result


async def safe_test_keyword_ideas(
    keyword: str,
    *,
    location_code: int = DEFAULT_LOCATION_CODE,
    language_code: str = DEFAULT_LANGUAGE_CODE,
    limit: int = 10,
) -> dict[str, Any]:
    payload = [
        {
            "location_code": location_code,
            "language_code": language_code,
            "keywords": [keyword],
        }
    ]
    result = await post_dataforseo(ENDPOINT_KEYWORDS_FOR_KEYWORDS_LIVE, payload)
    summary = summarize_keyword_ideas_response(result, keyword)
    if limit > 0 and summary.get("topIdeas"):
        summary["topIdeas"] = summary["topIdeas"][:limit]
    result["summary"] = summary
    result["rawPreview"] = truncate_json_preview(result.get("raw"))
    return result


async def safe_test_serp(
    keyword: str,
    *,
    location_code: int = DEFAULT_LOCATION_CODE,
    language_code: str = DEFAULT_LANGUAGE_CODE,
    depth: int = 10,
) -> dict[str, Any]:
    payload = [
        {
            "keyword": keyword,
            "location_code": location_code,
            "language_code": language_code,
            "depth": depth,
        }
    ]
    result = await post_dataforseo(ENDPOINT_SERP_ORGANIC_LIVE_ADVANCED, payload)
    result["summary"] = summarize_serp_response(result, keyword)
    result["rawPreview"] = truncate_json_preview(result.get("raw"))
    return result
