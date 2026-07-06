"""Growth Audit page-level Keyword Intelligence analysis via DataForSEO."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.growth_audit import (
    GrowthAuditFinding,
    GrowthAuditPage,
    GrowthAuditPageResult,
    GrowthAuditRun,
    GrowthAuditTask,
)
from app.services.dataforseo.constants import (
    ENDPOINT_KEYWORDS_FOR_KEYWORDS_LIVE,
    ENDPOINT_SEARCH_VOLUME_LIVE,
    ENDPOINT_SERP_ORGANIC_LIVE_ADVANCED,
    OBSERVED_SEARCH_VOLUME_SINGLE_COST_USD,
)
from app.services.dataforseo.dataforseo_budget import assert_dataforseo_budget_allows
from app.services.dataforseo.dataforseo_call_logging import record_dataforseo_call
from app.services.dataforseo.dataforseo_client import (
    build_request_hash,
    safe_test_keyword_ideas,
    safe_test_keyword_search_volume_batch,
    safe_test_serp,
)
from app.services.dataforseo.dataforseo_cost_estimator import (
    estimate_keyword_intelligence_page_cost,
)
from app.services.dataforseo.exceptions import DataForSeoApiError
from app.services.dataforseo.keyword_utils import resolve_search_volume_keywords
from app.services.growth_audit.exceptions import (
    GrowthAuditRunNotFoundError,
    GrowthAuditValidationError,
)
from app.services.growth_audit.keyword_intelligence_competitors import build_competitor_summary
from app.services.growth_audit.keyword_intelligence_findings import (
    build_keyword_intelligence_findings,
)
from app.services.growth_audit.keyword_intelligence_selection import (
    select_keyword_intelligence_seed_queries,
)
from app.services.growth_audit.run_service import (
    _ACTIVE_RUN_STATUSES,
    _count_open_findings_and_tasks,
    _get_growth_audit_page,
    create_growth_audit_event,
    get_growth_audit_run,
)

logger = logging.getLogger(__name__)

KEYWORD_INTELLIGENCE_RESULT_TYPE = "keyword_intelligence"
KEYWORD_INTELLIGENCE_SKILL_KEY = "growth_audit_keyword_intelligence"
CACHE_DAYS = 7


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _stringify_finding_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False)
    except Exception:
        return str(value)


def _is_product_page(page: GrowthAuditPage) -> bool:
    return page.page_type == "product" or page.source_entity_type == "shopify_product"


def _parse_synced_at(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed
    except ValueError:
        return None


def _is_fresh(metadata: dict[str, Any] | None, *, days: int = CACHE_DAYS) -> bool:
    if not metadata:
        return False
    synced_at = _parse_synced_at(metadata.get("syncedAt"))
    if synced_at is None:
        return False
    return synced_at >= _utcnow() - timedelta(days=days)


async def estimate_keyword_intelligence_cost(
    session: AsyncSession,
    project_id: UUID,
    *,
    seed_count: int,
    keyword_ideas_seeds: int,
    serp_keywords: int,
) -> float:
    estimate = await estimate_keyword_intelligence_page_cost(
        session,
        project_id,
        seed_queries=seed_count,
        keyword_ideas_seeds=keyword_ideas_seeds,
        serp_keywords=serp_keywords,
    )
    return float(estimate["totalUsd"])


def _update_run_keyword_intelligence_summary(
    run: GrowthAuditRun,
    *,
    page: GrowthAuditPage,
    payload: dict[str, Any],
    competitors: list[dict[str, Any]],
) -> None:
    existing_summary = dict(run.summary or {})
    prev_ki = existing_summary.get("keywordIntelligence")
    if not isinstance(prev_ki, dict):
        prev_ki = {}

    cost = payload.get("cost") or {}
    total_cost = float(cost.get("totalUsd") or 0)
    prev_pages = int(prev_ki.get("pagesAnalyzed") or 0)
    prev_total_cost = float(prev_ki.get("totalCostUsd") or 0)
    prev_keywords = int(prev_ki.get("keywordsEnriched") or 0)
    prev_serp = int(prev_ki.get("serpQueriesAnalyzed") or 0)

    pages_analyzed = prev_pages + 1
    combined_total_cost = round(prev_total_cost + total_cost, 4)
    keywords_enriched = prev_keywords + len(payload.get("searchVolume") or [])
    serp_queries = prev_serp + len(payload.get("serp") or [])

    top_competitors = sorted(
        competitors,
        key=lambda item: (
            -(item.get("appearancesCount") or 0),
            item.get("bestPosition") if item.get("bestPosition") is not None else 999,
        ),
    )[:5]

    existing_summary["keywordIntelligence"] = {
        "pagesAnalyzed": pages_analyzed,
        "lastAnalyzedAt": payload.get("syncedAt"),
        "lastAnalyzedPageUrl": page.url,
        "totalCostUsd": combined_total_cost,
        "averageCostPerPageUsd": round(combined_total_cost / pages_analyzed, 4)
        if pages_analyzed
        else combined_total_cost,
        "keywordsEnriched": keywords_enriched,
        "serpQueriesAnalyzed": serp_queries,
        "competitorsFound": len(competitors),
        "topCompetitors": [
            {
                "domain": item.get("domain"),
                "appearancesCount": item.get("appearancesCount"),
                "bestPosition": item.get("bestPosition"),
            }
            for item in top_competitors
        ],
    }
    run.summary = existing_summary


async def analyze_growth_audit_page_keyword_intelligence(
    session: AsyncSession,
    *,
    project_id: UUID,
    run_id: UUID,
    page_id: UUID,
    max_seed_queries: int = 10,
    keyword_ideas_seeds: int = 1,
    serp_keywords: int = 3,
    location_code: int = 2380,
    language_code: str = "it",
    force: bool = False,
) -> tuple[GrowthAuditRun, GrowthAuditPage, dict[str, Any], bool, int, int]:
    run = await get_growth_audit_run(session, project_id, run_id)
    if run is None:
        raise GrowthAuditRunNotFoundError(f"Growth Audit run {run_id} not found")

    if run.status in _ACTIVE_RUN_STATUSES:
        raise GrowthAuditValidationError(
            "Impossibile avviare Keyword Intelligence mentre il run è ancora in corso."
        )

    page = await _get_growth_audit_page(
        session,
        project_id=project_id,
        run_id=run_id,
        page_id=page_id,
    )
    if page is None:
        raise GrowthAuditValidationError(f"Pagina {page_id} non trovata nel run.")

    if not _is_product_page(page):
        raise GrowthAuditValidationError(
            "Keyword Intelligence è disponibile solo per pagine prodotto."
        )

    metadata = page.page_metadata or {}
    existing_ki = metadata.get("keywordIntelligence")
    if (
        not force
        and isinstance(existing_ki, dict)
        and _is_fresh(existing_ki)
    ):
        _update_run_keyword_intelligence_summary(
            run,
            page=page,
            payload=existing_ki,
            competitors=existing_ki.get("competitors") or [],
        )
        await session.commit()
        await session.refresh(run)
        await session.refresh(page)
        findings_count, tasks_count = await _count_open_findings_and_tasks(
            session,
            run_id=run.id,
            project_id=project_id,
        )
        return run, page, existing_ki, True, findings_count, tasks_count

    if not settings.dataforseo_configured:
        from app.services.dataforseo.exceptions import DataForSeoNotConfiguredError

        raise DataForSeoNotConfiguredError(
            "DataForSEO non configurato. Imposta DATAFORSEO_LOGIN e DATAFORSEO_PASSWORD.",
        )

    search_console_meta = metadata.get("searchConsole")
    seed_queries = select_keyword_intelligence_seed_queries(
        search_console_meta if isinstance(search_console_meta, dict) else None,
        page,
        max_seed_queries=max_seed_queries,
    )
    if not seed_queries:
        raise GrowthAuditValidationError(
            "Nessuna keyword seed disponibile. Sincronizza Search Console o verifica il titolo pagina."
        )

    keyword_strings = resolve_search_volume_keywords(
        keyword="",
        keywords=[item["query"] for item in seed_queries],
    )
    estimated_cost = await estimate_keyword_intelligence_cost(
        session,
        project_id,
        seed_count=len(keyword_strings),
        keyword_ideas_seeds=keyword_ideas_seeds,
        serp_keywords=serp_keywords,
    )
    await assert_dataforseo_budget_allows(session, project_id, estimated_cost)

    started_at = _utcnow()
    await create_growth_audit_event(
        session,
        run_id=run.id,
        project_id=project_id,
        event_type="keyword_intelligence_started",
        phase="keyword_intelligence",
        message=f"Keyword Intelligence avviata: {page.url}",
        progress_percent=run.progress_percent,
        payload={
            "pageId": str(page.id),
            "url": page.url,
            "maxSeedQueries": max_seed_queries,
            "keywordIdeasSeeds": keyword_ideas_seeds,
            "serpKeywords": serp_keywords,
        },
    )
    await session.flush()

    warnings: list[str] = []
    cost_breakdown = {
        "totalUsd": 0.0,
        "searchVolumeUsd": 0.0,
        "keywordIdeasUsd": 0.0,
        "serpUsd": 0.0,
    }
    search_volume_results: list[dict[str, Any]] = []
    keyword_ideas_payload: dict[str, Any] | None = None
    serp_results: list[dict[str, Any]] = []

    call_metadata_base = {
        "runId": str(run_id),
        "pageId": str(page_id),
        "url": page.url,
        "source": "keyword_intelligence",
    }

    sv_payload = [
        {
            "location_code": location_code,
            "language_code": language_code,
            "keywords": keyword_strings,
        }
    ]
    try:
        sv_result = await safe_test_keyword_search_volume_batch(
            keyword_strings,
            location_code=location_code,
            language_code=language_code,
        )
        sv_cost = await record_dataforseo_call(
            session,
            project_id=project_id,
            endpoint=ENDPOINT_SEARCH_VOLUME_LIVE,
            operation="keyword_intelligence_search_volume",
            request_hash=build_request_hash(ENDPOINT_SEARCH_VOLUME_LIVE, sv_payload),
            result=sv_result,
            metadata={**call_metadata_base, "keywords": keyword_strings},
            items_count=len(keyword_strings),
        )
        cost_breakdown["searchVolumeUsd"] = float(sv_cost)
        summary = sv_result.get("summary") or {}
        search_volume_results = summary.get("results") or []
    except DataForSeoApiError as exc:
        warnings.append(f"Search volume fallito: {exc.message}")
        await record_dataforseo_call(
            session,
            project_id=project_id,
            endpoint=ENDPOINT_SEARCH_VOLUME_LIVE,
            operation="keyword_intelligence_search_volume",
            request_hash=build_request_hash(ENDPOINT_SEARCH_VOLUME_LIVE, sv_payload),
            result={"cost_usd": None, "summary": {}},
            metadata={**call_metadata_base, "keywords": keyword_strings},
            items_count=len(keyword_strings),
            status="error",
            error_message=exc.message,
        )
        raise

    primary_keyword = keyword_strings[0]
    if keyword_ideas_seeds > 0 and primary_keyword:
        ideas_payload = [
            {
                "location_code": location_code,
                "language_code": language_code,
                "keywords": [primary_keyword],
            }
        ]
        try:
            ideas_result = await safe_test_keyword_ideas(
                primary_keyword,
                location_code=location_code,
                language_code=language_code,
                limit=20,
            )
            ideas_cost = await record_dataforseo_call(
                session,
                project_id=project_id,
                endpoint=ENDPOINT_KEYWORDS_FOR_KEYWORDS_LIVE,
                operation="keyword_intelligence_keyword_ideas",
                request_hash=build_request_hash(
                    ENDPOINT_KEYWORDS_FOR_KEYWORDS_LIVE,
                    ideas_payload,
                ),
                result=ideas_result,
                metadata={**call_metadata_base, "seedKeyword": primary_keyword},
                items_count=1,
            )
            cost_breakdown["keywordIdeasUsd"] = float(ideas_cost)
            ideas_summary = ideas_result.get("summary") or {}
            keyword_ideas_payload = {
                "seedKeyword": ideas_summary.get("seedKeyword", primary_keyword),
                "ideasCount": ideas_summary.get("ideasCount", 0),
                "items": ideas_summary.get("items", []),
            }
        except DataForSeoApiError as exc:
            warnings.append(f"Keyword ideas fallite: {exc.message}")
            await record_dataforseo_call(
                session,
                project_id=project_id,
                endpoint=ENDPOINT_KEYWORDS_FOR_KEYWORDS_LIVE,
                operation="keyword_intelligence_keyword_ideas",
                request_hash=build_request_hash(
                    ENDPOINT_KEYWORDS_FOR_KEYWORDS_LIVE,
                    ideas_payload,
                ),
                result={"cost_usd": None, "summary": {}},
                metadata={**call_metadata_base, "seedKeyword": primary_keyword},
                items_count=1,
                status="error",
                error_message=exc.message,
            )

    serp_targets = sorted(
        seed_queries,
        key=lambda item: item.get("score", 0),
        reverse=True,
    )[:serp_keywords]

    for seed in serp_targets:
        serp_keyword = str(seed.get("query") or "").strip()
        if not serp_keyword:
            continue
        serp_payload = [
            {
                "keyword": serp_keyword,
                "location_code": location_code,
                "language_code": language_code,
                "depth": 10,
            }
        ]
        try:
            serp_result = await safe_test_serp(
                serp_keyword,
                location_code=location_code,
                language_code=language_code,
                depth=10,
            )
            serp_cost = await record_dataforseo_call(
                session,
                project_id=project_id,
                endpoint=ENDPOINT_SERP_ORGANIC_LIVE_ADVANCED,
                operation="keyword_intelligence_serp",
                request_hash=build_request_hash(
                    ENDPOINT_SERP_ORGANIC_LIVE_ADVANCED,
                    serp_payload,
                ),
                result=serp_result,
                metadata={**call_metadata_base, "keyword": serp_keyword},
                items_count=1,
            )
            cost_breakdown["serpUsd"] += float(serp_cost)
            serp_summary = serp_result.get("summary") or {}
            serp_results.append(serp_summary)
        except DataForSeoApiError as exc:
            warnings.append(f'SERP fallita per "{serp_keyword}": {exc.message}')
            await record_dataforseo_call(
                session,
                project_id=project_id,
                endpoint=ENDPOINT_SERP_ORGANIC_LIVE_ADVANCED,
                operation="keyword_intelligence_serp",
                request_hash=build_request_hash(
                    ENDPOINT_SERP_ORGANIC_LIVE_ADVANCED,
                    serp_payload,
                ),
                result={"cost_usd": None, "summary": {}},
                metadata={**call_metadata_base, "keyword": serp_keyword},
                items_count=1,
                status="error",
                error_message=exc.message,
            )

    cost_breakdown["totalUsd"] = round(
        cost_breakdown["searchVolumeUsd"]
        + cost_breakdown["keywordIdeasUsd"]
        + cost_breakdown["serpUsd"],
        4,
    )
    if cost_breakdown["totalUsd"] <= 0:
        cost_breakdown["totalUsd"] = OBSERVED_SEARCH_VOLUME_SINGLE_COST_USD

    competitors = build_competitor_summary(serp_results)
    synced_at = _utcnow().isoformat()

    payload: dict[str, Any] = {
        "period": "latest",
        "source": "search_console_dataforseo",
        "locationCode": location_code,
        "languageCode": language_code,
        "seedQueries": seed_queries,
        "searchVolume": search_volume_results,
        "keywordIdeas": keyword_ideas_payload,
        "serp": serp_results,
        "competitors": competitors,
        "cost": cost_breakdown,
        "limits": {
            "maxSeedQueries": max_seed_queries,
            "keywordIdeasSeeds": keyword_ideas_seeds,
            "serpKeywords": serp_keywords,
        },
        "dataQuality": {
            "hasGscQueries": bool(
                isinstance(search_console_meta, dict)
                and search_console_meta.get("topQueries")
            ),
            "hasSearchVolume": bool(search_volume_results),
            "hasKeywordIdeas": bool(keyword_ideas_payload and keyword_ideas_payload.get("items")),
            "hasSerp": bool(serp_results),
            "warnings": warnings,
        },
        "syncedAt": synced_at,
    }

    findings, tasks = build_keyword_intelligence_findings(
        seed_queries=seed_queries,
        search_volume=search_volume_results,
        serp_results=serp_results,
        competitors=competitors,
    )

    now = _utcnow()
    page_result = GrowthAuditPageResult(
        run_id=run.id,
        page_id=page.id,
        project_id=project_id,
        result_type=KEYWORD_INTELLIGENCE_RESULT_TYPE,
        skill_key=KEYWORD_INTELLIGENCE_SKILL_KEY,
        status="completed",
        summary=(
            f"Keyword Intelligence: {len(search_volume_results)} volumi, "
            f"{len(serp_results)} SERP, costo ${cost_breakdown['totalUsd']:.4f}."
        ),
        findings=findings,
        recommendations=[
            {
                "title": finding.get("title"),
                "description": finding.get("recommendation"),
                "priority": finding.get("priority"),
            }
            for finding in findings
        ],
        tasks=tasks,
        artifacts={
            "keywordsEnriched": len(search_volume_results),
            "serpQueriesAnalyzed": len(serp_results),
            "competitorsFound": len(competitors),
            "costUsd": cost_breakdown["totalUsd"],
        },
        started_at=started_at,
        completed_at=now,
    )
    session.add(page_result)
    await session.flush()

    for finding_data in findings:
        existing_meta = finding_data.get("finding_metadata") or {}
        finding_metadata = {
            **existing_meta,
            "source": "keyword_intelligence",
            "structuredEvidence": finding_data.get("structuredEvidence"),
        }
        session.add(
            GrowthAuditFinding(
                run_id=run.id,
                page_id=page.id,
                project_id=project_id,
                source_result_id=page_result.id,
                category=finding_data.get("category", "seo"),
                severity=finding_data.get("severity", "medium"),
                priority=finding_data.get("priority", "medium"),
                title=_stringify_finding_text(finding_data.get("title"))
                or "Opportunità keyword",
                description=_stringify_finding_text(finding_data.get("description")),
                evidence=_stringify_finding_text(finding_data.get("evidence")),
                recommendation=_stringify_finding_text(finding_data.get("recommendation")),
                status="open",
                finding_metadata=finding_metadata,
            )
        )

    for task_data in tasks:
        session.add(
            GrowthAuditTask(
                run_id=run.id,
                page_id=page.id,
                project_id=project_id,
                title=_stringify_finding_text(task_data.get("title")) or "Task keyword",
                description=_stringify_finding_text(task_data.get("description")),
                owner_type=task_data.get("ownerType", "seo"),
                priority=task_data.get("priority", "medium"),
                estimated_effort=task_data.get("estimatedEffort", "medium"),
                status="open",
            )
        )

    page.page_metadata = {
        **metadata,
        "keywordIntelligence": payload,
    }

    _update_run_keyword_intelligence_summary(
        run,
        page=page,
        payload=payload,
        competitors=competitors,
    )

    await create_growth_audit_event(
        session,
        run_id=run.id,
        project_id=project_id,
        event_type="keyword_intelligence_completed",
        phase="keyword_intelligence",
        message=f"Keyword Intelligence completata: {page.url}",
        progress_percent=run.progress_percent,
        payload={
            "pageId": str(page.id),
            "url": page.url,
            "resultId": str(page_result.id),
            "costUsd": cost_breakdown["totalUsd"],
            "keywordsEnriched": len(search_volume_results),
            "findingsCount": len(findings),
            "tasksCount": len(tasks),
        },
    )

    await session.commit()
    await session.refresh(run)
    await session.refresh(page)

    findings_count, tasks_count = await _count_open_findings_and_tasks(
        session,
        run_id=run.id,
        project_id=project_id,
    )
    return run, page, payload, False, findings_count, tasks_count
