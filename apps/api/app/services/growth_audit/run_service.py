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
from app.services.growth_audit.page_inventory import merge_discovered_urls
from app.services.growth_audit.shopify_url_discovery import discover_shopify_urls
from app.services.growth_audit.sitemap_discovery import discover_sitemap_urls
from app.services.growth_audit.url_utils import (
    extract_domain,
    get_url_path,
    normalize_root_url,
    normalize_url,
)

logger = logging.getLogger(__name__)

MAX_LIST_LIMIT = 100
MAX_DISCOVERY_PAGES = 300
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


def _resolve_max_pages(config: dict | None) -> int:
    raw = (config or {}).get("maxPages", 50)
    try:
        max_pages = int(raw)
    except (TypeError, ValueError):
        max_pages = 50
    return max(1, min(max_pages, MAX_DISCOVERY_PAGES))


def _count_inventory_sources(items: list[dict]) -> dict[str, int]:
    counts = {"seed": 0, "sitemap": 0, "shopify": 0}
    for item in items:
        source = item.get("source", "")
        if source == "seed":
            counts["seed"] += 1
        elif source == "sitemap":
            counts["sitemap"] += 1
        elif source.startswith("shopify_"):
            counts["shopify"] += 1
    return counts


def _count_inventory_page_types(items: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        page_type = item.get("pageType") or "unknown"
        counts[page_type] = counts.get(page_type, 0) + 1
    return counts


async def _persist_discovery_events(
    session: AsyncSession,
    *,
    run: GrowthAuditRun,
    events: list[dict],
    phase: str = "discovery",
    progress_percent: int = 10,
) -> None:
    for event in events:
        event_type = event.get("type", "discovery_info")
        message = event.get("message", "Discovery event")
        payload = {
            key: value
            for key, value in event.items()
            if key not in {"type", "message"}
        }
        await create_growth_audit_event(
            session,
            run_id=run.id,
            project_id=run.project_id,
            event_type=event_type,
            phase=phase,
            message=message,
            progress_percent=progress_percent,
            payload=payload or None,
        )


async def _upsert_inventory_pages(
    session: AsyncSession,
    *,
    run: GrowthAuditRun,
    inventory_items: list[dict],
    now: datetime,
) -> int:
    existing_by_url = {
        page.normalized_url: page for page in run.pages
    }
    classified_count = 0

    for item in inventory_items:
        normalized_url = item["normalizedUrl"]
        page_type = item.get("pageType") or classify_page_type(
            normalized_url,
            title=item.get("title"),
            metadata=item.get("metadata"),
        )
        skill_bundle = get_default_skill_bundle_for_page_type(page_type)
        metadata = {
            **(item.get("metadata") or {}),
            "skillBundle": skill_bundle,
        }

        page = existing_by_url.get(normalized_url)
        if page is None:
            page = GrowthAuditPage(
                run_id=run.id,
                project_id=run.project_id,
                url=item["url"],
                normalized_url=normalized_url,
                path=item.get("path") or get_url_path(normalized_url),
                page_type=page_type,
                source=item.get("source", "seed"),
                status="classified",
                priority="high" if item.get("source") == "seed" else "normal",
                title=item.get("title"),
                discovered_at=now,
                classified_at=now,
                page_metadata=metadata,
            )
            session.add(page)
            existing_by_url[normalized_url] = page
        else:
            page.url = item["url"]
            page.path = item.get("path") or get_url_path(normalized_url)
            page.page_type = page_type
            page.source = item.get("source", page.source)
            page.status = "classified"
            page.title = item.get("title") or page.title
            page.discovered_at = page.discovered_at or now
            page.classified_at = now
            page.page_metadata = {
                **(page.page_metadata or {}),
                **metadata,
            }

        classified_count += 1

    return classified_count


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
        max_pages = _resolve_max_pages(run.config)
        root_domain = run.normalized_domain

        run.status = "discovering"
        run.phase = "discovery"
        run.started_at = run.started_at or now
        run.progress_percent = 10
        run.current_url = run.root_url
        await create_growth_audit_event(
            session,
            run_id=run.id,
            project_id=run.project_id,
            event_type="discovery_started",
            phase="discovery",
            message="Discovery avviata: sitemap e dati Shopify.",
            progress_percent=10,
        )
        await session.commit()

        sitemap_urls: list[str] = []
        shopify_items: list[dict] = []
        discovery_events: list[dict] = []

        try:
            sitemap_urls, sitemap_events = await discover_sitemap_urls(
                run.root_url,
                max_urls=max_pages,
            )
            discovery_events.extend(sitemap_events)
        except Exception as exc:
            logger.warning("Sitemap discovery failed for run %s: %s", run_id, exc)
            discovery_events.append(
                {
                    "type": "sitemap_error",
                    "message": "Errore durante la discovery sitemap.",
                    "count": 0,
                }
            )

        try:
            shopify_items, shopify_events = await discover_shopify_urls(
                session,
                run.project_id,
                run.root_url,
                max_urls=max_pages,
            )
            discovery_events.extend(shopify_events)
        except Exception as exc:
            logger.warning("Shopify discovery failed for run %s: %s", run_id, exc)
            discovery_events.append(
                {
                    "type": "shopify_urls_missing",
                    "message": "Errore durante la discovery Shopify.",
                    "count": 0,
                }
            )

        await _persist_discovery_events(
            session,
            run=run,
            events=discovery_events,
            phase="discovery",
            progress_percent=25,
        )
        await session.commit()

        inventory_items = merge_discovered_urls(
            seed_url=run.root_url,
            sitemap_urls=sitemap_urls,
            shopify_items=shopify_items,
            max_pages=max_pages,
            root_domain=root_domain,
        )

        classified_count = await _upsert_inventory_pages(
            session,
            run=run,
            inventory_items=inventory_items,
            now=now,
        )

        source_counts = _count_inventory_sources(inventory_items)
        page_type_counts = _count_inventory_page_types(inventory_items)

        run.pages_discovered = len(inventory_items)
        run.pages_classified = classified_count
        run.total_pages = len(inventory_items)
        run.current_url = None
        run.progress_percent = 60
        run.status = "ready_for_analysis"
        run.phase = "analysis"

        inventory_message = (
            f"Inventario completato con {len(inventory_items)} pagine."
            if len(inventory_items) > 1
            else "Inventario completato con sola pagina seed."
        )
        await create_growth_audit_event(
            session,
            run_id=run.id,
            project_id=run.project_id,
            event_type="inventory_completed",
            phase="analysis",
            message=inventory_message,
            progress_percent=60,
            payload={
                "pagesDiscovered": len(inventory_items),
                "pagesClassified": classified_count,
                "sources": source_counts,
                "pageTypes": page_type_counts,
            },
        )
        await session.commit()

        include_ai = bool((run.config or {}).get("includeAiAnalysis"))
        await create_growth_audit_event(
            session,
            run_id=run.id,
            project_id=run.project_id,
            event_type="analysis_skipped",
            phase="analysis",
            message="Analisi AI non abilitata in questo step.",
            progress_percent=60,
            payload={"includeAiAnalysis": include_ai},
        )
        await session.commit()

        warning_message = None
        if len(inventory_items) <= 1:
            warning_message = (
                "Solo la pagina seed è stata trovata. Verifica sitemap o sincronizzazione Shopify."
            )

        run.status = "completed"
        run.phase = "finalization"
        run.progress_percent = 100
        run.completed_at = _utcnow()
        run.current_url = None
        run.summary = {
            "message": "Page inventory completed. AI page analysis is not enabled yet.",
            "pagesDiscovered": len(inventory_items),
            "pagesClassified": classified_count,
            "pagesAnalyzed": 0,
            "includeAiAnalysis": include_ai,
            "auditMode": run.audit_mode,
            "sources": source_counts,
            "pageTypes": page_type_counts,
            "nextStep": "Enable page-level technical and AI analysis.",
            "warning": warning_message,
        }
        await create_growth_audit_event(
            session,
            run_id=run.id,
            project_id=run.project_id,
            event_type="run_completed",
            phase="finalization",
            message="Growth Audit completato: inventario pagine pronto.",
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
