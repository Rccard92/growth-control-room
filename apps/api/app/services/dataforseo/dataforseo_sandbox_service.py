"""DataForSEO Cost Sandbox orchestration."""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.dataforseo.constants import (
    ENDPOINT_KEYWORDS_FOR_KEYWORDS_LIVE,
    ENDPOINT_SEARCH_VOLUME_LIVE,
    ENDPOINT_SERP_ORGANIC_LIVE_ADVANCED,
    OBSERVED_SEARCH_VOLUME_SINGLE_COST_USD,
    TEST_COST_ESTIMATES,
    UNIT_COST_ESTIMATES,
)
from app.services.dataforseo.dataforseo_budget import assert_dataforseo_budget_allows
from app.services.dataforseo.dataforseo_client import (
    build_request_hash,
    safe_test_keyword_ideas,
    safe_test_keyword_search_volume,
    safe_test_keyword_search_volume_batch,
    safe_test_serp,
)
from app.services.dataforseo.dataforseo_usage_service import (
    DataForSeoUsageLogInput,
    observed_unit_costs,
    record_dataforseo_usage,
)
from app.services.dataforseo.exceptions import DataForSeoApiError
from app.services.dataforseo.keyword_utils import resolve_search_volume_keywords


async def estimate_search_volume_batch_cost(
    session: AsyncSession,
    project_id: UUID,
    keyword_count: int,
) -> float:
    observed = await observed_unit_costs(session, project_id)
    per_keyword = (
        observed.get("search_volume_batch")
        or observed.get("search_volume")
        or UNIT_COST_ESTIMATES["search_volume"]
    )
    estimated = max(float(per_keyword) * keyword_count, OBSERVED_SEARCH_VOLUME_SINGLE_COST_USD)
    return round(estimated, 4)


async def _record_call(
    session: AsyncSession,
    *,
    project_id: UUID,
    endpoint: str,
    operation: str,
    request_hash: str,
    result: dict[str, Any],
    metadata: dict[str, Any],
    items_count: int | None = None,
) -> Decimal:
    cost = result.get("cost_usd")
    cost_decimal = Decimal(str(cost)) if cost is not None else None
    summary = result.get("summary") or {}
    resolved_items_count = (
        items_count
        if items_count is not None
        else summary.get("keywordCount")
        or summary.get("itemsCount")
        or summary.get("ideasCount")
        or summary.get("resultCount")
    )
    await record_dataforseo_usage(
        session,
        DataForSeoUsageLogInput(
            project_id=project_id,
            endpoint=endpoint,
            operation=operation,
            status="success",
            request_hash=request_hash,
            cost_usd=cost_decimal,
            items_count=resolved_items_count,
            metadata_json=metadata,
            response_summary=summary,
        ),
    )
    return cost_decimal or Decimal("0")


async def run_dataforseo_sandbox_test(
    session: AsyncSession,
    *,
    project_id: UUID,
    test_type: str,
    keyword: str,
    keywords: list[str] | None = None,
    location_code: int,
    language_code: str,
) -> dict[str, Any]:
    if test_type == "search_volume_batch":
        resolved_keywords = resolve_search_volume_keywords(keyword=keyword, keywords=keywords)
        estimated_cost = await estimate_search_volume_batch_cost(
            session,
            project_id,
            len(resolved_keywords),
        )
        await assert_dataforseo_budget_allows(session, project_id, estimated_cost)

        payload = [
            {
                "location_code": location_code,
                "language_code": language_code,
                "keywords": resolved_keywords,
            }
        ]
        result = await safe_test_keyword_search_volume_batch(
            resolved_keywords,
            location_code=location_code,
            language_code=language_code,
        )
        summary = result.get("summary") or {}
        cost = await _record_call(
            session,
            project_id=project_id,
            endpoint=ENDPOINT_SEARCH_VOLUME_LIVE,
            operation=test_type,
            request_hash=build_request_hash(ENDPOINT_SEARCH_VOLUME_LIVE, payload),
            result=result,
            metadata={
                "testType": test_type,
                "keywords": resolved_keywords,
                "locationCode": location_code,
                "languageCode": language_code,
            },
            items_count=len(resolved_keywords),
        )
        average_cost = summary.get("averageCostPerKeywordUsd")
        if average_cost is None and resolved_keywords:
            average_cost = float(cost) / len(resolved_keywords)
        return {
            "testType": test_type,
            "keyword": resolved_keywords[0],
            "keywords": resolved_keywords,
            "costUsd": float(cost),
            "averageCostPerKeywordUsd": average_cost,
            "endpoints": [ENDPOINT_SEARCH_VOLUME_LIVE],
            "responseSummary": summary,
            "rawPreview": result.get("rawPreview"),
        }

    estimated_cost = TEST_COST_ESTIMATES.get(test_type)
    if estimated_cost is None:
        raise ValueError(f"Tipo test non supportato: {test_type}")

    await assert_dataforseo_budget_allows(session, project_id, estimated_cost)

    metadata = {
        "testType": test_type,
        "keyword": keyword,
        "locationCode": location_code,
        "languageCode": language_code,
    }

    if test_type == "search_volume":
        payload = [
            {
                "location_code": location_code,
                "language_code": language_code,
                "keywords": [keyword],
            }
        ]
        result = await safe_test_keyword_search_volume(
            keyword,
            location_code=location_code,
            language_code=language_code,
        )
        cost = await _record_call(
            session,
            project_id=project_id,
            endpoint=ENDPOINT_SEARCH_VOLUME_LIVE,
            operation=test_type,
            request_hash=build_request_hash(ENDPOINT_SEARCH_VOLUME_LIVE, payload),
            result=result,
            metadata=metadata,
            items_count=1,
        )
        summary = result.get("summary") or {}
        return {
            "testType": test_type,
            "keyword": keyword,
            "keywords": [keyword],
            "costUsd": float(cost),
            "averageCostPerKeywordUsd": summary.get("averageCostPerKeywordUsd") or float(cost),
            "endpoints": [ENDPOINT_SEARCH_VOLUME_LIVE],
            "responseSummary": summary,
            "rawPreview": result.get("rawPreview"),
        }

    if test_type == "keyword_ideas":
        payload = [
            {
                "location_code": location_code,
                "language_code": language_code,
                "keywords": [keyword],
            }
        ]
        result = await safe_test_keyword_ideas(
            keyword,
            location_code=location_code,
            language_code=language_code,
            limit=10,
        )
        cost = await _record_call(
            session,
            project_id=project_id,
            endpoint=ENDPOINT_KEYWORDS_FOR_KEYWORDS_LIVE,
            operation=test_type,
            request_hash=build_request_hash(ENDPOINT_KEYWORDS_FOR_KEYWORDS_LIVE, payload),
            result=result,
            metadata=metadata,
            items_count=1,
        )
        return {
            "testType": test_type,
            "keyword": keyword,
            "keywords": [keyword],
            "costUsd": float(cost),
            "averageCostPerKeywordUsd": float(cost),
            "endpoints": [ENDPOINT_KEYWORDS_FOR_KEYWORDS_LIVE],
            "responseSummary": result.get("summary"),
            "rawPreview": result.get("rawPreview"),
        }

    if test_type == "serp":
        payload = [
            {
                "keyword": keyword,
                "location_code": location_code,
                "language_code": language_code,
                "depth": 10,
            }
        ]
        result = await safe_test_serp(
            keyword,
            location_code=location_code,
            language_code=language_code,
            depth=10,
        )
        cost = await _record_call(
            session,
            project_id=project_id,
            endpoint=ENDPOINT_SERP_ORGANIC_LIVE_ADVANCED,
            operation=test_type,
            request_hash=build_request_hash(ENDPOINT_SERP_ORGANIC_LIVE_ADVANCED, payload),
            result=result,
            metadata=metadata,
            items_count=1,
        )
        return {
            "testType": test_type,
            "keyword": keyword,
            "keywords": [keyword],
            "costUsd": float(cost),
            "averageCostPerKeywordUsd": float(cost),
            "endpoints": [ENDPOINT_SERP_ORGANIC_LIVE_ADVANCED],
            "responseSummary": result.get("summary"),
            "rawPreview": result.get("rawPreview"),
        }

    if test_type == "micro_bundle":
        total_cost = Decimal("0")
        endpoints: list[str] = []
        summaries: dict[str, Any] = {}
        raw_previews: dict[str, Any] = {}

        for step, runner, endpoint in (
            (
                "search_volume",
                lambda: safe_test_keyword_search_volume(
                    keyword,
                    location_code=location_code,
                    language_code=language_code,
                ),
                ENDPOINT_SEARCH_VOLUME_LIVE,
            ),
            (
                "keyword_ideas",
                lambda: safe_test_keyword_ideas(
                    keyword,
                    location_code=location_code,
                    language_code=language_code,
                    limit=10,
                ),
                ENDPOINT_KEYWORDS_FOR_KEYWORDS_LIVE,
            ),
            (
                "serp",
                lambda: safe_test_serp(
                    keyword,
                    location_code=location_code,
                    language_code=language_code,
                    depth=10,
                ),
                ENDPOINT_SERP_ORGANIC_LIVE_ADVANCED,
            ),
        ):
            try:
                result = await runner()
            except DataForSeoApiError as exc:
                await record_dataforseo_usage(
                    session,
                    DataForSeoUsageLogInput(
                        project_id=project_id,
                        endpoint=endpoint,
                        operation=step,
                        status="error",
                        metadata_json={**metadata, "bundleStep": step},
                        error_message=exc.message,
                    ),
                )
                raise
            step_cost = await _record_call(
                session,
                project_id=project_id,
                endpoint=endpoint,
                operation=step,
                request_hash=build_request_hash(endpoint, [{"keyword": keyword}]),
                result=result,
                metadata={**metadata, "bundleStep": step},
                items_count=1,
            )
            total_cost += step_cost
            endpoints.append(endpoint)
            summaries[step] = result.get("summary")
            raw_previews[step] = result.get("rawPreview")

        return {
            "testType": test_type,
            "keyword": keyword,
            "keywords": [keyword],
            "costUsd": float(total_cost),
            "averageCostPerKeywordUsd": float(total_cost),
            "endpoints": endpoints,
            "responseSummary": summaries,
            "rawPreview": raw_previews,
        }

    raise ValueError(f"Tipo test non supportato: {test_type}")
