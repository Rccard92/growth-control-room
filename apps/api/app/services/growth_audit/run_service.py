"""Growth Audit run orchestration and background processing."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import case, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_session_factory
from app.models.growth_audit import (
    GrowthAuditEvent,
    GrowthAuditFinding,
    GrowthAuditPage,
    GrowthAuditPageResult,
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
from app.services.growth_audit.page_technical_scanner import scan_page_technical
from app.services.growth_audit.shopify_url_discovery import discover_shopify_urls
from app.services.growth_audit.sitemap_discovery import discover_sitemap_urls
from app.services.growth_audit.technical_scoring import score_technical_scan
from app.services.growth_audit.url_utils import (
    extract_domain,
    get_url_path,
    normalize_root_url,
    normalize_url,
)

logger = logging.getLogger(__name__)

MAX_LIST_LIMIT = 100
MAX_DISCOVERY_PAGES = 300
MAX_TECHNICAL_SCAN_PAGES = 300
TECHNICAL_SCAN_CONCURRENCY = 4
TECHNICAL_SCAN_TIMEOUT_SECONDS = 12.0
SUPPORTED_PROVIDERS = {"openai", "claude"}

_SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
_PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
_ACTIVE_RUN_STATUSES = {
    "pending",
    "queued",
    "discovering",
    "classifying",
    "analyzing",
    "ready_for_analysis",
}
_RESCAN_ALLOWED_RUN_STATUSES = {"completed", "partial_failed", "failed"}


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


async def _load_pages_to_scan(
    session: AsyncSession,
    *,
    run: GrowthAuditRun,
    max_pages: int,
) -> list[GrowthAuditPage]:
    scan_limit = min(max_pages, run.total_pages or max_pages, MAX_TECHNICAL_SCAN_PAGES)
    priority_rank = case(
        (GrowthAuditPage.priority == "high", 0),
        else_=1,
    )
    stmt = (
        select(GrowthAuditPage)
        .where(
            GrowthAuditPage.run_id == run.id,
            GrowthAuditPage.project_id == run.project_id,
            GrowthAuditPage.status.in_(("classified", "discovered", "pending")),
        )
        .order_by(
            priority_rank.asc(),
            GrowthAuditPage.depth.asc().nulls_last(),
            GrowthAuditPage.url.asc(),
        )
        .limit(scan_limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def _fetch_page_scan(
    page: GrowthAuditPage,
    *,
    root_domain: str,
    semaphore: asyncio.Semaphore,
) -> tuple[GrowthAuditPage, dict | None, str | None]:
    async with semaphore:
        try:
            scan = await scan_page_technical(
                page.url,
                page_type=page.page_type,
                root_domain=root_domain,
                timeout_seconds=TECHNICAL_SCAN_TIMEOUT_SECONDS,
            )
            score_technical_scan(scan, page.page_type)
            return page, scan, None
        except Exception as exc:
            logger.warning("Technical scan failed for page %s: %s", page.url, exc)
            return page, None, str(exc)


async def _persist_technical_scan_result(
    session: AsyncSession,
    *,
    run: GrowthAuditRun,
    page: GrowthAuditPage,
    scan: dict | None,
    error_message: str | None,
    now: datetime,
    count_as_new_analysis: bool = True,
    create_page_event: bool = True,
    event_phase: str = "technical_scan",
) -> tuple[bool, int, list[dict], list[dict]]:
    page_started = now
    result_status = "completed"
    page_status = "analyzed"
    score = 0
    findings: list[dict] = []
    tasks: list[dict] = []
    summary = "Technical scan completed."

    if scan is None or error_message:
        result_status = "failed"
        page_status = "failed"
        page.error_message = error_message or scan.get("fetchError") if scan else "Scan failed"
        summary = page.error_message or "Technical scan failed."
        if create_page_event:
            await create_growth_audit_event(
                session,
                run_id=run.id,
                project_id=run.project_id,
                event_type="page_scan_failed",
                phase=event_phase,
                message=f"Scansione fallita: {page.url}",
                progress_percent=run.progress_percent,
                payload={"pageId": str(page.id), "url": page.url, "error": page.error_message},
            )
        if count_as_new_analysis:
            run.pages_failed += 1
    else:
        score = scan.get("score", 0)
        findings = scan.get("findings") or []
        tasks = scan.get("tasks") or []
        page.http_status = scan.get("httpStatus")
        page.title = scan.get("title") or page.title
        page.meta_description = scan.get("metaDescription")
        page.canonical_url = scan.get("canonicalUrl")
        page.h1 = scan.get("h1")
        page.score = score
        page.seo_score = score
        page.analyzed_at = now
        page.error_message = scan.get("fetchError")
        page.page_metadata = {
            **(page.page_metadata or {}),
            "technical": {
                "schemaTypes": (scan.get("schema") or {}).get("types", []),
                "imagesTotal": (scan.get("images") or {}).get("total", 0),
                "imagesMissingAlt": (scan.get("images") or {}).get("missingAlt", 0),
                "linksInternal": (scan.get("links") or {}).get("internal", 0),
                "linksExternal": (scan.get("links") or {}).get("external", 0),
                "robots": scan.get("robots") or {},
            },
        }
        if scan.get("fetchError"):
            result_status = "failed"
            page_status = "failed"
            if count_as_new_analysis:
                run.pages_failed += 1
        elif count_as_new_analysis:
            run.pages_analyzed += 1
        summary = f"Technical score {score}. {len(findings)} findings."

        if create_page_event:
            await create_growth_audit_event(
                session,
                run_id=run.id,
                project_id=run.project_id,
                event_type="page_scanned",
                phase=event_phase,
                message=f"Pagina scansionata: {page.url}",
                progress_percent=run.progress_percent,
                payload={
                    "pageId": str(page.id),
                    "url": page.url,
                    "score": score,
                    "httpStatus": scan.get("httpStatus"),
                },
            )

    page.status = page_status
    page_result = GrowthAuditPageResult(
        run_id=run.id,
        page_id=page.id,
        project_id=run.project_id,
        result_type="technical",
        status=result_status,
        score=score if scan else None,
        summary=summary,
        findings=findings if scan else None,
        tasks=tasks if scan else None,
        raw_output=scan,
        started_at=page_started,
        completed_at=now,
        error_message=error_message if not scan else scan.get("fetchError"),
    )
    session.add(page_result)
    await session.flush()

    if scan and findings:
        for finding_data in findings:
            finding = GrowthAuditFinding(
                run_id=run.id,
                page_id=page.id,
                project_id=run.project_id,
                source_result_id=page_result.id,
                category=finding_data.get("category", "technical"),
                severity=finding_data.get("severity", "medium"),
                priority=finding_data.get("priority", "medium"),
                title=finding_data.get("title", "Finding"),
                description=finding_data.get("description"),
                evidence=finding_data.get("evidence"),
                recommendation=finding_data.get("recommendation"),
                how_to_validate=finding_data.get("howToValidate"),
                impact=finding_data.get("impact"),
                effort=finding_data.get("effort"),
                status="open",
            )
            session.add(finding)

    if scan and tasks:
        for task_data in tasks:
            task = GrowthAuditTask(
                run_id=run.id,
                page_id=page.id,
                project_id=run.project_id,
                title=task_data.get("title", "Task"),
                description=task_data.get("description"),
                owner_type=task_data.get("ownerType", "seo"),
                priority=task_data.get("priority", "medium"),
                estimated_effort=task_data.get("estimatedEffort", "medium"),
                status="open",
            )
            session.add(task)

    success = page_status == "analyzed"
    return success, score, findings, tasks


async def _run_technical_scan_phase(
    session: AsyncSession,
    *,
    run: GrowthAuditRun,
    max_pages: int,
    source_counts: dict[str, int],
    page_type_counts: dict[str, int],
    classified_count: int,
    inventory_count: int,
    now: datetime,
) -> None:
    pages = await _load_pages_to_scan(session, run=run, max_pages=max_pages)
    total_to_scan = len(pages)

    run.pages_analyzed = run.pages_analyzed or 0
    run.pages_failed = run.pages_failed or 0

    if total_to_scan == 1 and inventory_count > 1:
        await create_growth_audit_event(
            session,
            run_id=run.id,
            project_id=run.project_id,
            event_type="technical_scan_page_mismatch",
            phase="technical_scan",
            message=(
                "Inventario contiene più pagine, ma la scansione tecnica ne ha caricate solo una. "
                "Verifica query/status."
            ),
            progress_percent=65,
            payload={
                "pagesDiscovered": inventory_count,
                "pagesToScan": total_to_scan,
            },
        )

    run.status = "analyzing"
    run.phase = "technical_scan"
    run.progress_percent = 65
    await create_growth_audit_event(
        session,
        run_id=run.id,
        project_id=run.project_id,
        event_type="technical_scan_started",
        phase="technical_scan",
        message=f"Scansione tecnica avviata su {total_to_scan} pagine.",
        progress_percent=65,
        payload={"pagesToScan": total_to_scan},
    )
    await session.commit()

    if total_to_scan == 0:
        run.pages_analyzed = 0
        run.pages_failed = 0
        run.site_score = None
        run.seo_score = None
        run.status = "completed"
        run.phase = "finalization"
        run.progress_percent = 100
        run.completed_at = _utcnow()
        run.summary = {
            "message": "Technical page scan completed. No pages to analyze.",
            "pagesDiscovered": inventory_count,
            "pagesClassified": classified_count,
            "pagesAnalyzed": 0,
            "pagesFailed": 0,
            "includeAiAnalysis": bool((run.config or {}).get("includeAiAnalysis")),
            "auditMode": run.audit_mode,
            "sources": source_counts,
            "pageTypes": page_type_counts,
            "nextStep": "Enable page-level AI, GEO and CRO analysis by page type.",
        }
        await create_growth_audit_event(
            session,
            run_id=run.id,
            project_id=run.project_id,
            event_type="run_completed",
            phase="finalization",
            message="Growth Audit completato.",
            progress_percent=100,
            payload=run.summary,
        )
        await session.commit()
        return

    semaphore = asyncio.Semaphore(TECHNICAL_SCAN_CONCURRENCY)
    scan_results = await asyncio.gather(
        *[
            _fetch_page_scan(page, root_domain=run.normalized_domain, semaphore=semaphore)
            for page in pages
        ]
    )

    scores: list[int] = []
    all_findings: list[dict] = []
    done = 0

    for page, scan, error_message in scan_results:
        run.current_url = page.url
        page.status = "analyzing"
        done += 1
        run.progress_percent = 65 + int(30 * done / total_to_scan)
        if run.progress_percent > 95:
            run.progress_percent = 95

        success, score, findings, _ = await _persist_technical_scan_result(
            session,
            run=run,
            page=page,
            scan=scan,
            error_message=error_message,
            now=now,
        )
        if success and score is not None:
            scores.append(score)
        all_findings.extend(findings)
        await session.commit()

    run.current_url = None
    include_ai = bool((run.config or {}).get("includeAiAnalysis"))

    critical_count = sum(1 for f in all_findings if f.get("severity") == "critical")
    high_count = sum(1 for f in all_findings if f.get("severity") == "high")
    tasks_open = (
        await session.execute(
            select(func.count())
            .select_from(GrowthAuditTask)
            .where(
                GrowthAuditTask.run_id == run.id,
                GrowthAuditTask.project_id == run.project_id,
                GrowthAuditTask.status == "open",
            )
        )
    ).scalar_one()

    average_score = round(sum(scores) / len(scores)) if scores else None
    run.site_score = average_score
    run.seo_score = average_score
    run.geo_score = None
    run.cro_score = None
    run.performance_score = None

    warning_message = None
    if inventory_count <= 1:
        warning_message = (
            "Solo la pagina seed è stata trovata. Verifica sitemap o sincronizzazione Shopify."
        )

    if run.pages_analyzed == 0 and run.pages_failed > 0:
        final_status = "failed"
    elif run.pages_failed > 0:
        final_status = "partial_failed"
    else:
        final_status = "completed"

    run.status = final_status
    run.phase = "finalization"
    run.progress_percent = 100
    run.completed_at = _utcnow()
    run.summary = {
        "message": "Technical page scan completed. AI/GEO/CRO analysis is not enabled yet.",
        "pagesDiscovered": inventory_count,
        "pagesClassified": classified_count,
        "pagesAnalyzed": run.pages_analyzed,
        "pagesFailed": run.pages_failed,
        "averageTechnicalScore": average_score,
        "criticalFindings": critical_count,
        "highFindings": high_count,
        "tasksOpen": tasks_open,
        "includeAiAnalysis": include_ai,
        "auditMode": run.audit_mode,
        "sources": source_counts,
        "pageTypes": page_type_counts,
        "nextStep": "Enable page-level AI, GEO and CRO analysis by page type.",
        "warning": warning_message,
    }
    await create_growth_audit_event(
        session,
        run_id=run.id,
        project_id=run.project_id,
        event_type="run_completed",
        phase="finalization",
        message="Growth Audit completato: scansione tecnica pagine.",
        progress_percent=100,
        payload=run.summary,
    )
    await session.commit()


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

        await _run_technical_scan_phase(
            session,
            run=run,
            max_pages=max_pages,
            source_counts=source_counts,
            page_type_counts=page_type_counts,
            classified_count=classified_count,
            inventory_count=len(inventory_items),
            now=now,
        )


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


async def list_growth_audit_findings(
    session: AsyncSession,
    project_id: UUID,
    run_id: UUID,
    *,
    page_id: UUID | None = None,
    severity: str | None = None,
    category: str | None = None,
    status: str | None = None,
) -> list[GrowthAuditFinding]:
    run = await get_growth_audit_run(session, project_id, run_id)
    if run is None:
        raise GrowthAuditRunNotFoundError(f"Growth Audit run {run_id} not found")

    query = select(GrowthAuditFinding).where(
        GrowthAuditFinding.run_id == run_id,
        GrowthAuditFinding.project_id == project_id,
    )
    if page_id is not None:
        query = query.where(GrowthAuditFinding.page_id == page_id)
    if severity:
        query = query.where(GrowthAuditFinding.severity == severity)
    if category:
        query = query.where(GrowthAuditFinding.category == category)
    if status:
        query = query.where(GrowthAuditFinding.status == status)

    result = await session.execute(query)
    findings = list(result.scalars().all())
    findings.sort(
        key=lambda f: (
            _SEVERITY_ORDER.get(f.severity, 99),
            f.created_at or _utcnow(),
        )
    )
    return findings


async def list_growth_audit_tasks(
    session: AsyncSession,
    project_id: UUID,
    run_id: UUID,
    *,
    page_id: UUID | None = None,
    priority: str | None = None,
    owner_type: str | None = None,
    status: str | None = None,
) -> list[GrowthAuditTask]:
    run = await get_growth_audit_run(session, project_id, run_id)
    if run is None:
        raise GrowthAuditRunNotFoundError(f"Growth Audit run {run_id} not found")

    query = select(GrowthAuditTask).where(
        GrowthAuditTask.run_id == run_id,
        GrowthAuditTask.project_id == project_id,
    )
    if page_id is not None:
        query = query.where(GrowthAuditTask.page_id == page_id)
    if priority:
        query = query.where(GrowthAuditTask.priority == priority)
    if owner_type:
        query = query.where(GrowthAuditTask.owner_type == owner_type)
    if status:
        query = query.where(GrowthAuditTask.status == status)

    result = await session.execute(query)
    tasks = list(result.scalars().all())
    tasks.sort(
        key=lambda t: (
            _PRIORITY_ORDER.get(t.priority, 99),
            t.created_at or _utcnow(),
        )
    )
    return tasks


async def _get_growth_audit_page(
    session: AsyncSession,
    *,
    project_id: UUID,
    run_id: UUID,
    page_id: UUID,
) -> GrowthAuditPage | None:
    result = await session.execute(
        select(GrowthAuditPage).where(
            GrowthAuditPage.id == page_id,
            GrowthAuditPage.run_id == run_id,
            GrowthAuditPage.project_id == project_id,
        )
    )
    return result.scalar_one_or_none()


async def _supersede_page_open_items(
    session: AsyncSession,
    *,
    run_id: UUID,
    page_id: UUID,
    project_id: UUID,
) -> tuple[int, int]:
    findings_result = await session.execute(
        update(GrowthAuditFinding)
        .where(
            GrowthAuditFinding.run_id == run_id,
            GrowthAuditFinding.page_id == page_id,
            GrowthAuditFinding.project_id == project_id,
            GrowthAuditFinding.status == "open",
        )
        .values(status="superseded")
    )
    tasks_result = await session.execute(
        update(GrowthAuditTask)
        .where(
            GrowthAuditTask.run_id == run_id,
            GrowthAuditTask.page_id == page_id,
            GrowthAuditTask.project_id == project_id,
            GrowthAuditTask.status == "open",
        )
        .values(status="superseded")
    )
    return findings_result.rowcount or 0, tasks_result.rowcount or 0


async def _count_open_findings_and_tasks(
    session: AsyncSession,
    *,
    run_id: UUID,
    project_id: UUID,
) -> tuple[int, int]:
    findings_count = (
        await session.execute(
            select(func.count())
            .select_from(GrowthAuditFinding)
            .where(
                GrowthAuditFinding.run_id == run_id,
                GrowthAuditFinding.project_id == project_id,
                GrowthAuditFinding.status == "open",
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
                GrowthAuditTask.status == "open",
            )
        )
    ).scalar_one()
    return findings_count, tasks_count


async def recompute_growth_audit_run_summary(
    session: AsyncSession,
    run: GrowthAuditRun,
    *,
    last_page_rescan_at: datetime | None = None,
) -> None:
    pages_analyzed = (
        await session.execute(
            select(func.count())
            .select_from(GrowthAuditPage)
            .where(
                GrowthAuditPage.run_id == run.id,
                GrowthAuditPage.project_id == run.project_id,
                GrowthAuditPage.status == "analyzed",
            )
        )
    ).scalar_one()
    pages_failed = (
        await session.execute(
            select(func.count())
            .select_from(GrowthAuditPage)
            .where(
                GrowthAuditPage.run_id == run.id,
                GrowthAuditPage.project_id == run.project_id,
                GrowthAuditPage.status == "failed",
            )
        )
    ).scalar_one()

    scores = (
        await session.execute(
            select(GrowthAuditPage.score).where(
                GrowthAuditPage.run_id == run.id,
                GrowthAuditPage.project_id == run.project_id,
                GrowthAuditPage.status == "analyzed",
                GrowthAuditPage.score.is_not(None),
            )
        )
    ).scalars().all()
    average_score = round(sum(scores) / len(scores)) if scores else None

    critical_count = (
        await session.execute(
            select(func.count())
            .select_from(GrowthAuditFinding)
            .where(
                GrowthAuditFinding.run_id == run.id,
                GrowthAuditFinding.project_id == run.project_id,
                GrowthAuditFinding.status == "open",
                GrowthAuditFinding.severity == "critical",
            )
        )
    ).scalar_one()
    high_count = (
        await session.execute(
            select(func.count())
            .select_from(GrowthAuditFinding)
            .where(
                GrowthAuditFinding.run_id == run.id,
                GrowthAuditFinding.project_id == run.project_id,
                GrowthAuditFinding.status == "open",
                GrowthAuditFinding.severity == "high",
            )
        )
    ).scalar_one()
    tasks_open = (
        await session.execute(
            select(func.count())
            .select_from(GrowthAuditTask)
            .where(
                GrowthAuditTask.run_id == run.id,
                GrowthAuditTask.project_id == run.project_id,
                GrowthAuditTask.status == "open",
            )
        )
    ).scalar_one()

    run.pages_analyzed = pages_analyzed
    run.pages_failed = pages_failed
    run.site_score = average_score
    run.seo_score = average_score

    if pages_analyzed == 0 and pages_failed > 0:
        run.status = "failed"
    elif pages_failed > 0:
        run.status = "partial_failed"
    else:
        run.status = "completed"

    existing_summary = dict(run.summary or {})
    include_ai = (run.config or {}).get("includeAiAnalysis", False)
    run.summary = {
        **existing_summary,
        "message": existing_summary.get(
            "message",
            "Technical page scan completed. AI/GEO/CRO analysis is not enabled yet.",
        ),
        "pagesDiscovered": existing_summary.get("pagesDiscovered", run.pages_discovered),
        "pagesClassified": existing_summary.get("pagesClassified", run.pages_classified),
        "pagesAnalyzed": pages_analyzed,
        "pagesFailed": pages_failed,
        "averageTechnicalScore": average_score,
        "criticalFindings": critical_count,
        "highFindings": high_count,
        "tasksOpen": tasks_open,
        "includeAiAnalysis": existing_summary.get("includeAiAnalysis", include_ai),
        "auditMode": existing_summary.get("auditMode", run.audit_mode),
        "sources": existing_summary.get("sources", {}),
        "pageTypes": existing_summary.get("pageTypes", {}),
        "nextStep": existing_summary.get(
            "nextStep",
            "Enable page-level AI, GEO and CRO analysis by page type.",
        ),
        "warning": existing_summary.get("warning"),
        "lastPageRescanAt": (
            last_page_rescan_at.isoformat()
            if last_page_rescan_at
            else existing_summary.get("lastPageRescanAt")
        ),
    }


async def rescan_growth_audit_page(
    session: AsyncSession,
    *,
    project_id: UUID,
    run_id: UUID,
    page_id: UUID,
    clear_previous_open_items: bool = True,
    note: str | None = None,
) -> tuple[GrowthAuditRun, GrowthAuditPage, int, int]:
    run = await get_growth_audit_run(session, project_id, run_id)
    if run is None:
        raise GrowthAuditRunNotFoundError(f"Growth Audit run {run_id} not found")

    if run.status in _ACTIVE_RUN_STATUSES:
        raise GrowthAuditValidationError(
            "Cannot rescan page while audit run is still active."
        )
    if run.status not in _RESCAN_ALLOWED_RUN_STATUSES:
        raise GrowthAuditValidationError(
            f"Cannot rescan page for run status: {run.status}"
        )

    page = await _get_growth_audit_page(
        session,
        project_id=project_id,
        run_id=run_id,
        page_id=page_id,
    )
    if page is None:
        raise GrowthAuditRunNotFoundError(f"Growth Audit page {page_id} not found")

    if not (page.url and page.url.strip()):
        raise GrowthAuditValidationError("Page URL is required for rescan.")

    now = _utcnow()

    await create_growth_audit_event(
        session,
        run_id=run.id,
        project_id=project_id,
        event_type="page_rescan_started",
        phase="page_rescan",
        message=f"Riscansione pagina avviata: {page.url}",
        progress_percent=run.progress_percent,
        payload={
            "pageId": str(page.id),
            "url": page.url,
            "note": note,
        },
    )

    if clear_previous_open_items:
        findings_superseded, tasks_superseded = await _supersede_page_open_items(
            session,
            run_id=run.id,
            page_id=page.id,
            project_id=project_id,
        )
        if findings_superseded > 0 or tasks_superseded > 0:
            await create_growth_audit_event(
                session,
                run_id=run.id,
                project_id=project_id,
                event_type="page_previous_items_superseded",
                phase="page_rescan",
                message=(
                    f"Archiviati {findings_superseded} problemi e "
                    f"{tasks_superseded} task aperti precedenti."
                ),
                progress_percent=run.progress_percent,
                payload={
                    "pageId": str(page.id),
                    "findingsSuperseded": findings_superseded,
                    "tasksSuperseded": tasks_superseded,
                },
            )

    page.status = "analyzing"
    page.error_message = None
    await session.flush()

    scan: dict | None = None
    error_message: str | None = None
    try:
        scan = await scan_page_technical(
            page.url,
            page_type=page.page_type,
            root_domain=run.normalized_domain,
            timeout_seconds=TECHNICAL_SCAN_TIMEOUT_SECONDS,
        )
        score_technical_scan(scan, page.page_type)
    except Exception as exc:
        logger.warning("Page rescan failed for %s: %s", page.url, exc)
        error_message = str(exc)

    success, score, findings_data, tasks_data = await _persist_technical_scan_result(
        session,
        run=run,
        page=page,
        scan=scan,
        error_message=error_message,
        now=now,
        count_as_new_analysis=False,
        create_page_event=False,
        event_phase="page_rescan",
    )

    await recompute_growth_audit_run_summary(
        session,
        run,
        last_page_rescan_at=now,
    )

    findings_count, tasks_count = await _count_open_findings_and_tasks(
        session,
        run_id=run.id,
        project_id=project_id,
    )

    event_type = "page_rescan_completed" if success else "page_rescan_failed"
    event_message = (
        f"Riscansione completata: {page.url}"
        if success
        else f"Riscansione fallita: {page.url}"
    )
    await create_growth_audit_event(
        session,
        run_id=run.id,
        project_id=project_id,
        event_type=event_type,
        phase="page_rescan",
        message=event_message,
        progress_percent=run.progress_percent or 100,
        payload={
            "pageId": str(page.id),
            "url": page.url,
            "score": page.score,
            "status": page.status,
            "findingsCreated": len(findings_data),
            "tasksCreated": len(tasks_data),
        },
    )

    await session.commit()
    await session.refresh(run)
    await session.refresh(page)

    return run, page, findings_count, tasks_count
