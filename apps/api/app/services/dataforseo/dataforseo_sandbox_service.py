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
    TEST_COST_ESTIMATES,
)
from app.services.dataforseo.dataforseo_budget import assert_dataforseo_budget_allows
from app.services.dataforseo.dataforseo_client import (
    build_request_hash,
    safe_test_keyword_ideas,
    safe_test_keyword_search_volume,
    safe_test_serp,
)
from app.services.dataforseo.dataforseo_usage_service import (
    DataForSeoUsageLogInput,
    record_dataforseo_usage,
)
from app.services.dataforseo.exceptions import DataForSeoApiError


async def _record_call(
    session: AsyncSession,
    *,
    project_id: UUID,
    endpoint: str,
    operation: str,
    request_hash: str,
    result: dict[str, Any],
    metadata: dict[str, Any],
) -> Decimal:
    cost = result.get("cost_usd")
    cost_decimal = Decimal(str(cost)) if cost is not None else None
    await record_dataforseo_usage(
        session,
        DataForSeoUsageLogInput(
            project_id=project_id,
            endpoint=endpoint,
            operation=operation,
            status="success",
            request_hash=request_hash,
            cost_usd=cost_decimal,
            items_count=(result.get("summary") or {}).get("itemsCount")
            or (result.get("summary") or {}).get("ideasCount")
            or (result.get("summary") or {}).get("resultCount"),
            metadata_json=metadata,
            response_summary=result.get("summary"),
        ),
    )
    return cost_decimal or Decimal("0")


async def run_dataforseo_sandbox_test(
    session: AsyncSession,
    *,
    project_id: UUID,
    test_type: str,
    keyword: str,
    location_code: int,
    language_code: str,
) -> dict[str, Any]:
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
        )
        return {
            "testType": test_type,
            "keyword": keyword,
            "costUsd": float(cost),
            "endpoints": [ENDPOINT_SEARCH_VOLUME_LIVE],
            "responseSummary": result.get("summary"),
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
        )
        return {
            "testType": test_type,
            "keyword": keyword,
            "costUsd": float(cost),
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
        )
        return {
            "testType": test_type,
            "keyword": keyword,
            "costUsd": float(cost),
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
            )
            total_cost += step_cost
            endpoints.append(endpoint)
            summaries[step] = result.get("summary")
            raw_previews[step] = result.get("rawPreview")

        return {
            "testType": test_type,
            "keyword": keyword,
            "costUsd": float(total_cost),
            "endpoints": endpoints,
            "responseSummary": summaries,
            "rawPreview": raw_previews,
        }

    raise ValueError(f"Tipo test non supportato: {test_type}")
