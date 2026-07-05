"""Growth Audit page-level performance analysis service."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.growth_audit import (
    GrowthAuditFinding,
    GrowthAuditPage,
    GrowthAuditPageResult,
    GrowthAuditRun,
    GrowthAuditTask,
)
from app.services.google.crux_client import fetch_crux_record
from app.services.google.exceptions import GoogleApiRequestError, GoogleIntegrationNotConfiguredError
from app.services.google.google_config import is_crux_configured, is_pagespeed_configured
from app.services.google.pagespeed_client import fetch_pagespeed_insights
from app.services.growth_audit.exceptions import (
    GrowthAuditRunNotFoundError,
    GrowthAuditValidationError,
)
from app.services.growth_audit.performance_analysis import (
    build_performance_findings,
    build_performance_tasks,
    normalize_crux_result,
    normalize_pagespeed_result,
)
from app.services.growth_audit.run_service import (
    _ACTIVE_RUN_STATUSES,
    _count_open_findings_and_tasks,
    _get_growth_audit_page,
    create_growth_audit_event,
    get_growth_audit_run,
)

logger = logging.getLogger(__name__)

PERFORMANCE_RESULT_TYPE = "performance"
PERFORMANCE_SKILL_KEY = "growth_audit_page_performance"
SUPPORTED_STRATEGIES = {"mobile", "desktop"}


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _build_performance_summary(
    normalized_pagespeed: dict[str, Any],
    normalized_crux: dict[str, Any],
) -> str:
    score = normalized_pagespeed.get("performanceScore")
    lcp = normalized_pagespeed.get("lcp")
    cls = normalized_pagespeed.get("cls")
    tbt = normalized_pagespeed.get("tbt")
    parts = [f"Performance score {score if score is not None else 'n/d'}."]
    if lcp is not None:
        parts.append(f"LCP {lcp:.0f}ms.")
    if cls is not None:
        parts.append(f"CLS {cls:.3f}.")
    if tbt is not None:
        parts.append(f"TBT {tbt:.0f}ms.")
    if normalized_crux.get("source") == "missing":
        parts.append("CrUX non disponibile per questa URL.")
    elif normalized_crux.get("source"):
        parts.append(f"CrUX source: {normalized_crux['source']}.")
    return " ".join(parts)


def _compact_raw_output(
    pagespeed_raw: dict[str, Any] | None,
    *,
    strategy: str,
) -> dict[str, Any]:
    if pagespeed_raw is None:
        return {"strategy": strategy}
    lighthouse = pagespeed_raw.get("lighthouseResult") or {}
    categories = lighthouse.get("categories") or {}
    return {
        "strategy": strategy,
        "analysisUTCTimestamp": pagespeed_raw.get("analysisUTCTimestamp"),
        "categoryScores": {
            key: (categories.get(key) or {}).get("score")
            for key in ("performance", "accessibility", "best-practices", "seo")
        },
        "finalUrl": lighthouse.get("finalUrl"),
    }


async def _persist_failed_performance_result(
    session: AsyncSession,
    *,
    run: GrowthAuditRun,
    page: GrowthAuditPage,
    project_id: UUID,
    started_at: datetime,
    error_message: str,
    strategy: str,
    raw_output: dict[str, Any] | None = None,
) -> GrowthAuditPageResult:
    now = _utcnow()
    page_result = GrowthAuditPageResult(
        run_id=run.id,
        page_id=page.id,
        project_id=project_id,
        result_type=PERFORMANCE_RESULT_TYPE,
        skill_key=PERFORMANCE_SKILL_KEY,
        status="failed",
        summary=error_message,
        artifacts={"strategy": strategy},
        raw_output=raw_output,
        error_message=error_message,
        started_at=started_at,
        completed_at=now,
    )
    session.add(page_result)
    await session.flush()

    await create_growth_audit_event(
        session,
        run_id=run.id,
        project_id=project_id,
        event_type="performance_analysis_failed",
        phase="performance",
        message=f"Analisi performance fallita: {page.url}",
        progress_percent=run.progress_percent,
        payload={
            "pageId": str(page.id),
            "url": page.url,
            "resultId": str(page_result.id),
            "error": error_message,
            "strategy": strategy,
        },
    )
    await session.commit()
    await session.refresh(page_result)
    return page_result


async def _update_run_summary_after_performance_analysis(
    session: AsyncSession,
    run: GrowthAuditRun,
    *,
    page: GrowthAuditPage,
    analyzed_at: datetime,
    performance_score: int | None,
) -> None:
    performance_pages_analyzed = (
        await session.execute(
            select(func.count())
            .select_from(GrowthAuditPage)
            .where(
                GrowthAuditPage.run_id == run.id,
                GrowthAuditPage.project_id == run.project_id,
                GrowthAuditPage.performance_score.is_not(None),
            )
        )
    ).scalar_one()

    avg_score = (
        await session.execute(
            select(func.avg(GrowthAuditPage.performance_score)).where(
                GrowthAuditPage.run_id == run.id,
                GrowthAuditPage.project_id == run.project_id,
                GrowthAuditPage.performance_score.is_not(None),
            )
        )
    ).scalar_one()

    performance_issues_open = (
        await session.execute(
            select(func.count())
            .select_from(GrowthAuditFinding)
            .where(
                GrowthAuditFinding.run_id == run.id,
                GrowthAuditFinding.project_id == run.project_id,
                GrowthAuditFinding.status == "open",
                GrowthAuditFinding.category == "performance",
            )
        )
    ).scalar_one()

    existing_summary = dict(run.summary or {})
    average_performance_score = (
        int(round(float(avg_score))) if avg_score is not None else performance_score
    )
    run.summary = {
        **existing_summary,
        "performancePagesAnalyzed": performance_pages_analyzed,
        "averagePerformanceScore": average_performance_score,
        "performanceIssuesOpen": performance_issues_open,
        "lastPerformanceAnalysisAt": analyzed_at.isoformat(),
        "lastPerformanceAnalysisUrl": page.url,
    }
    if average_performance_score is not None:
        run.performance_score = average_performance_score


async def analyze_growth_audit_page_performance(
    session: AsyncSession,
    *,
    project_id: UUID,
    run_id: UUID,
    page_id: UUID,
    strategy: str = "mobile",
) -> tuple[GrowthAuditRun, GrowthAuditPage, GrowthAuditPageResult, int, int]:
    run = await get_growth_audit_run(session, project_id, run_id)
    if run is None:
        raise GrowthAuditRunNotFoundError(f"Growth Audit run {run_id} not found")

    if run.status in _ACTIVE_RUN_STATUSES:
        raise GrowthAuditValidationError(
            "Impossibile avviare l'analisi performance mentre il run è ancora in corso."
        )

    normalized_strategy = (strategy or "mobile").strip().lower()
    if normalized_strategy not in SUPPORTED_STRATEGIES:
        raise GrowthAuditValidationError(f"Strategy non supportata: {strategy}")

    if not is_pagespeed_configured():
        raise GoogleIntegrationNotConfiguredError(
            "PageSpeed Insights non configurato. Imposta GOOGLE_PAGESPEED_API_KEY.",
            integration="google_pagespeed",
        )

    page = await _get_growth_audit_page(
        session,
        project_id=project_id,
        run_id=run_id,
        page_id=page_id,
    )
    if page is None:
        raise GrowthAuditValidationError(f"Pagina {page_id} non trovata nel run.")

    if not page.url or not page.url.strip():
        raise GrowthAuditValidationError("La pagina non ha un URL valido per l'analisi performance.")

    started_at = _utcnow()
    await create_growth_audit_event(
        session,
        run_id=run.id,
        project_id=project_id,
        event_type="performance_analysis_started",
        phase="performance",
        message=f"Analisi performance avviata: {page.url}",
        progress_percent=run.progress_percent,
        payload={
            "pageId": str(page.id),
            "url": page.url,
            "strategy": normalized_strategy,
        },
    )
    await session.flush()

    pagespeed_raw: dict[str, Any] | None = None
    try:
        pagespeed_raw = await fetch_pagespeed_insights(page.url, strategy=normalized_strategy)
    except (GoogleApiRequestError, GoogleIntegrationNotConfiguredError) as exc:
        readable = str(exc)
        await _persist_failed_performance_result(
            session,
            run=run,
            page=page,
            project_id=project_id,
            started_at=started_at,
            error_message=readable,
            strategy=normalized_strategy,
        )
        raise

    crux_raw: dict[str, Any] | None = None
    if is_crux_configured():
        try:
            crux_raw = await fetch_crux_record(page.url)
        except GoogleApiRequestError as exc:
            logger.warning("CrUX lookup failed for %s: %s", page.url, exc)

    normalized_pagespeed = normalize_pagespeed_result(pagespeed_raw)
    normalized_crux = normalize_crux_result(crux_raw)
    findings = build_performance_findings(normalized_pagespeed, normalized_crux)
    tasks = build_performance_tasks(findings)
    recommendations = [
        {
            "title": finding.get("title"),
            "description": finding.get("recommendation"),
            "priority": finding.get("priority"),
        }
        for finding in findings
        if finding.get("recommendation")
    ]

    now = _utcnow()
    summary = _build_performance_summary(normalized_pagespeed, normalized_crux)
    page_result = GrowthAuditPageResult(
        run_id=run.id,
        page_id=page.id,
        project_id=project_id,
        result_type=PERFORMANCE_RESULT_TYPE,
        skill_key=PERFORMANCE_SKILL_KEY,
        status="completed",
        score=normalized_pagespeed.get("performanceScore"),
        summary=summary,
        findings=findings,
        recommendations=recommendations,
        tasks=tasks,
        artifacts={
            "pagespeed": normalized_pagespeed,
            "crux": normalized_crux,
            "strategy": normalized_strategy,
        },
        raw_output=_compact_raw_output(pagespeed_raw, strategy=normalized_strategy),
        started_at=started_at,
        completed_at=now,
    )
    session.add(page_result)
    await session.flush()

    for finding_data in findings:
        session.add(
            GrowthAuditFinding(
                run_id=run.id,
                page_id=page.id,
                project_id=project_id,
                source_result_id=page_result.id,
                category=finding_data.get("category", "performance"),
                severity=finding_data.get("severity", "medium"),
                priority=finding_data.get("priority", "medium"),
                title=finding_data.get("title", "Problema performance"),
                description=finding_data.get("description"),
                evidence=finding_data.get("evidence"),
                recommendation=finding_data.get("recommendation"),
                how_to_validate=finding_data.get("howToValidate"),
                impact=finding_data.get("impact"),
                effort=finding_data.get("effort"),
                status="open",
            )
        )

    for task_data in tasks:
        session.add(
            GrowthAuditTask(
                run_id=run.id,
                page_id=page.id,
                project_id=project_id,
                title=task_data.get("title", "Task performance"),
                description=task_data.get("description"),
                owner_type=task_data.get("ownerType", "dev"),
                priority=task_data.get("priority", "medium"),
                estimated_effort=task_data.get("estimatedEffort", "medium"),
                status="open",
            )
        )

    page.performance_score = normalized_pagespeed.get("performanceScore")
    page.page_metadata = {
        **(page.page_metadata or {}),
        "performance": {
            "latestResultId": str(page_result.id),
            "latestScore": normalized_pagespeed.get("performanceScore"),
            "analyzedAt": now.isoformat(),
            "cruxSource": normalized_crux.get("source"),
            "lcp": normalized_pagespeed.get("lcp"),
            "cls": normalized_pagespeed.get("cls"),
            "inp": normalized_crux.get("inpP75"),
            "strategy": normalized_strategy,
        },
    }

    await _update_run_summary_after_performance_analysis(
        session,
        run,
        page=page,
        analyzed_at=now,
        performance_score=normalized_pagespeed.get("performanceScore"),
    )

    await create_growth_audit_event(
        session,
        run_id=run.id,
        project_id=project_id,
        event_type="performance_analysis_completed",
        phase="performance",
        message=f"Analisi performance completata: {page.url}",
        progress_percent=run.progress_percent,
        payload={
            "pageId": str(page.id),
            "url": page.url,
            "resultId": str(page_result.id),
            "score": normalized_pagespeed.get("performanceScore"),
            "findingsCount": len(findings),
            "tasksCount": len(tasks),
            "cruxSource": normalized_crux.get("source"),
            "strategy": normalized_strategy,
        },
    )

    await session.commit()
    await session.refresh(run)
    await session.refresh(page)
    await session.refresh(page_result)

    findings_count, tasks_count = await _count_open_findings_and_tasks(
        session,
        run_id=run.id,
        project_id=project_id,
    )
    return run, page, page_result, findings_count, tasks_count
