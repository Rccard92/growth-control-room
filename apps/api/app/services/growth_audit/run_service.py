"""Growth Audit run orchestration and background processing."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_session_factory
from app.models.growth_audit import (
    GrowthAuditEvent,
    GrowthAuditFinding,
    GrowthAuditPage,
    GrowthAuditRun,
    GrowthAuditTask,
)
from app.schemas.growth_audit import GrowthAuditRunCreateRequest
from app.services.growth_audit.exceptions import (
    GrowthAuditRunNotFoundError,
    GrowthAuditValidationError,
)
from app.services.growth_audit.page_classifier import (
    classify_page_type,
    get_default_skill_bundle_for_page_type,
)
from app.services.growth_audit.url_utils import (
    extract_domain,
    get_url_path,
    normalize_root_url,
    normalize_url,
)

logger = logging.getLogger(__name__)

MAX_LIST_LIMIT = 100
SUPPORTED_PROVIDERS = {"openai", "claude"}


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _validate_create_request(request: GrowthAuditRunCreateRequest) -> tuple[str, str, dict]:
    if not (request.root_url and request.root_url.strip()):
        raise GrowthAuditValidationError("rootUrl is required")

    provider = (request.provider or "openai").strip().lower()
    if provider not in SUPPORTED_PROVIDERS:
        raise GrowthAuditValidationError(f"Unsupported AI provider: {request.provider}")

    normalized_root = normalize_root_url(request.root_url)
    domain = extract_domain(normalized_root)

    max_pages = request.max_pages
    if max_pages < 1 or max_pages > 500:
        raise GrowthAuditValidationError("maxPages must be between 1 and 500")

    config = {
        "rootUrl": normalized_root,
        "provider": provider,
        "auditMode": request.audit_mode,
        "maxPages": max_pages,
        "includeAiAnalysis": request.include_ai_analysis,
    }

    return normalized_root, domain, config


async def create_growth_audit_event(
    session: AsyncSession,
    *,
    run_id: UUID,
    project_id: UUID,
    event_type: str,
    message: str,
    phase: str | None = None,
    progress_percent: int | None = None,
    payload: dict | None = None,
) -> GrowthAuditEvent:
    event = GrowthAuditEvent(
        run_id=run_id,
        project_id=project_id,
        event_type=event_type,
        phase=phase,
        message=message,
        progress_percent=progress_percent,
        payload=payload,
    )
    session.add(event)
    await session.flush()
    return event


async def create_growth_audit_run(
    session: AsyncSession,
    project_id: UUID,
    request: GrowthAuditRunCreateRequest,
) -> GrowthAuditRun:
    normalized_root, domain, config = _validate_create_request(request)
    now = _utcnow()

    run = GrowthAuditRun(
        project_id=project_id,
        root_url=normalized_root,
        normalized_domain=domain,
        status="pending",
        phase="queued",
        audit_mode=request.audit_mode,
        provider=config["provider"],
        progress_percent=0,
        pages_discovered=0,
        pages_classified=0,
        pages_analyzed=0,
        pages_failed=0,
        total_pages=1,
        current_url=normalized_root,
        config=config,
    )
    session.add(run)
    await session.flush()

    page_type = classify_page_type(normalized_root)
    skill_bundle = get_default_skill_bundle_for_page_type(page_type)

    seed_page = GrowthAuditPage(
        run_id=run.id,
        project_id=project_id,
        url=normalized_root,
        normalized_url=normalize_url(normalized_root),
        path=get_url_path(normalized_root),
        page_type=page_type,
        source="seed",
        status="discovered",
        priority="high",
        depth=0,
        discovered_at=now,
        page_metadata={"skillBundle": skill_bundle},
    )
    session.add(seed_page)

    run.pages_discovered = 1
    run.status = "queued"

    await create_growth_audit_event(
        session,
        run_id=run.id,
        project_id=project_id,
        event_type="run_created",
        phase="queued",
        message="Growth Audit run creato con pagina seed.",
        progress_percent=0,
        payload={"rootUrl": normalized_root, "pagesDiscovered": 1},
    )

    await session.commit()
    await session.refresh(run)
    return run


def schedule_growth_audit_run(run_id: UUID) -> None:
    logger.info("Scheduling Growth Audit run %s", run_id)
    asyncio.create_task(process_growth_audit_run(run_id))


async def start_growth_audit_run(
    session: AsyncSession,
    project_id: UUID,
    request: GrowthAuditRunCreateRequest,
) -> GrowthAuditRun:
    run = await create_growth_audit_run(session, project_id, request)
    schedule_growth_audit_run(run.id)
    return run


async def process_growth_audit_run(run_id: UUID) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        run = (
            await session.execute(
                select(GrowthAuditRun)
                .where(GrowthAuditRun.id == run_id)
                .options(selectinload(GrowthAuditRun.pages))
            )
        ).scalar_one_or_none()

        if run is None:
            logger.error("Growth Audit run %s not found", run_id)
            return

        if run.status not in ("pending", "queued"):
            logger.info(
                "Skipping Growth Audit run %s because status is %s",
                run_id,
                run.status,
            )
            return

        now = _utcnow()
        run.status = "discovering"
        run.phase = "discovery"
        run.started_at = now
        run.progress_percent = 10
        run.current_url = run.root_url
        await create_growth_audit_event(
            session,
            run_id=run.id,
            project_id=run.project_id,
            event_type="discovery_started",
            phase="discovery",
            message="Discovery avviata (MVP: solo pagina seed).",
            progress_percent=10,
        )
        await session.commit()

        run.status = "classifying"
        run.phase = "classification"
        run.progress_percent = 35
        await create_growth_audit_event(
            session,
            run_id=run.id,
            project_id=run.project_id,
            event_type="classification_started",
            phase="classification",
            message="Classificazione pagine in corso.",
            progress_percent=35,
        )
        await session.commit()

        classified_count = 0
        for page in run.pages:
            page_type = classify_page_type(page.url, title=page.title)
            skill_bundle = get_default_skill_bundle_for_page_type(page_type)
            page.page_type = page_type
            page.status = "classified"
            page.classified_at = _utcnow()
            page.page_metadata = {
                **(page.page_metadata or {}),
                "skillBundle": skill_bundle,
            }
            classified_count += 1

        run.pages_classified = classified_count
        run.status = "ready_for_analysis"
        run.phase = "ready_for_analysis"
        run.progress_percent = 60
        await create_growth_audit_event(
            session,
            run_id=run.id,
            project_id=run.project_id,
            event_type="analysis_ready",
            phase="ready_for_analysis",
            message="Pagine classificate, pronte per analisi.",
            progress_percent=60,
            payload={"pagesClassified": classified_count},
        )
        await session.commit()

        include_ai = bool((run.config or {}).get("includeAiAnalysis"))
        if include_ai:
            await create_growth_audit_event(
                session,
                run_id=run.id,
                project_id=run.project_id,
                event_type="analysis_skipped",
                phase="ready_for_analysis",
                message="Analisi AI disabilitata in questo step.",
                progress_percent=60,
            )
        else:
            await create_growth_audit_event(
                session,
                run_id=run.id,
                project_id=run.project_id,
                event_type="analysis_skipped",
                phase="ready_for_analysis",
                message="Analisi AI non inclusa in questa configurazione.",
                progress_percent=60,
            )
        await session.commit()

        run.status = "completed"
        run.phase = "completed"
        run.progress_percent = 100
        run.completed_at = _utcnow()
        run.current_url = None
        run.summary = {
            "message": "Audit skeleton completato. Discovery sitemap e analisi skill arriveranno nel prossimo step.",
            "pagesDiscovered": run.pages_discovered,
            "pagesClassified": run.pages_classified,
            "pagesAnalyzed": 0,
            "includeAiAnalysis": include_ai,
            "auditMode": run.audit_mode,
        }
        await create_growth_audit_event(
            session,
            run_id=run.id,
            project_id=run.project_id,
            event_type="run_completed",
            phase="completed",
            message="Growth Audit completato (skeleton MVP).",
            progress_percent=100,
            payload=run.summary,
        )
        await session.commit()


async def get_growth_audit_run(
    session: AsyncSession,
    project_id: UUID,
    run_id: UUID,
) -> GrowthAuditRun | None:
    result = await session.execute(
        select(GrowthAuditRun)
        .where(
            GrowthAuditRun.id == run_id,
            GrowthAuditRun.project_id == project_id,
        )
        .options(
            selectinload(GrowthAuditRun.pages),
            selectinload(GrowthAuditRun.events),
        )
    )
    return result.scalar_one_or_none()


async def get_growth_audit_run_detail(
    session: AsyncSession,
    project_id: UUID,
    run_id: UUID,
) -> tuple[GrowthAuditRun, int, int]:
    run = await get_growth_audit_run(session, project_id, run_id)
    if run is None:
        raise GrowthAuditRunNotFoundError(f"Growth Audit run {run_id} not found")

    findings_count = (
        await session.execute(
            select(func.count())
            .select_from(GrowthAuditFinding)
            .where(
                GrowthAuditFinding.run_id == run_id,
                GrowthAuditFinding.project_id == project_id,
            )
        )
    ).scalar_one()

    tasks_count = (
        await session.execute(
            select(func.count())
            .select_from(GrowthAuditTask)
            .where(
                GrowthAuditTask.run_id == run_id,
                GrowthAuditTask.project_id == project_id,
            )
        )
    ).scalar_one()

    return run, findings_count, tasks_count


async def list_growth_audit_runs(
    session: AsyncSession,
    project_id: UUID,
    limit: int = 20,
) -> list[GrowthAuditRun]:
    capped_limit = max(1, min(limit, MAX_LIST_LIMIT))
    result = await session.execute(
        select(GrowthAuditRun)
        .where(GrowthAuditRun.project_id == project_id)
        .order_by(GrowthAuditRun.created_at.desc())
        .limit(capped_limit)
    )
    return list(result.scalars().all())


async def list_growth_audit_pages(
    session: AsyncSession,
    project_id: UUID,
    run_id: UUID,
) -> list[GrowthAuditPage]:
    run = await get_growth_audit_run(session, project_id, run_id)
    if run is None:
        raise GrowthAuditRunNotFoundError(f"Growth Audit run {run_id} not found")
    return list(run.pages)


async def list_growth_audit_events(
    session: AsyncSession,
    project_id: UUID,
    run_id: UUID,
) -> list[GrowthAuditEvent]:
    run = await get_growth_audit_run(session, project_id, run_id)
    if run is None:
        raise GrowthAuditRunNotFoundError(f"Growth Audit run {run_id} not found")
    return sorted(run.events, key=lambda event: event.created_at or _utcnow())
