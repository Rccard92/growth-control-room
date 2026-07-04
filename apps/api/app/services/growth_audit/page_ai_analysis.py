"""Growth Audit page-level AI/GEO/CRO analysis service."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_seo import ShopifyCollection
from app.models.growth_audit import (
    GrowthAuditFinding,
    GrowthAuditPage,
    GrowthAuditPageResult,
    GrowthAuditRun,
    GrowthAuditTask,
)
from app.models.shopify import ShopifyProduct
from app.services.ai.ai_client import AiRequestMetadata
from app.services.ai.provider_router import generate_structured_json_with_provider
from app.services.growth_audit.exceptions import (
    GrowthAuditRunNotFoundError,
    GrowthAuditValidationError,
)
from app.services.growth_audit.page_ai_output_schema import (
    get_growth_audit_page_ai_output_json_schema,
    normalize_growth_audit_page_ai_output,
)
from app.services.growth_audit.page_ai_prompts import build_system_prompt, build_user_prompt
from app.services.growth_audit.run_service import (
    _ACTIVE_RUN_STATUSES,
    _count_open_findings_and_tasks,
    _get_growth_audit_page,
    create_growth_audit_event,
    get_growth_audit_run,
)

logger = logging.getLogger(__name__)

SUPPORTED_PROVIDERS = {"openai", "claude"}
AI_RESULT_TYPE = "ai_deep_analysis"
AI_SKILL_KEY = "growth_audit_page_ai"


def _utcnow() -> datetime:
    return datetime.now(UTC)


async def _load_latest_technical_result(
    session: AsyncSession,
    *,
    page_id: UUID,
    project_id: UUID,
    run_id: UUID,
) -> GrowthAuditPageResult | None:
    result = await session.execute(
        select(GrowthAuditPageResult)
        .where(
            GrowthAuditPageResult.page_id == page_id,
            GrowthAuditPageResult.project_id == project_id,
            GrowthAuditPageResult.run_id == run_id,
            GrowthAuditPageResult.result_type == "technical",
            GrowthAuditPageResult.status == "completed",
        )
        .order_by(GrowthAuditPageResult.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _load_shopify_entity(
    session: AsyncSession,
    page: GrowthAuditPage,
) -> dict[str, Any] | None:
    if not page.source_entity_type or not page.source_entity_id:
        return None

    if page.source_entity_type == "shopify_product":
        product = await session.get(ShopifyProduct, page.source_entity_id)
        if product is None:
            return None
        images = product.media_images or []
        return {
            "entityType": "product",
            "title": product.title,
            "handle": product.handle,
            "seoTitle": product.seo_title,
            "seoDescription": product.seo_description,
            "descriptionText": product.description_text,
            "featuredImageUrl": product.featured_image_url,
            "imagesCount": len(images) if isinstance(images, list) else 0,
            "missingAltCount": sum(
                1
                for img in images
                if isinstance(img, dict) and not str(img.get("altText") or img.get("alt") or "").strip()
            )
            if isinstance(images, list)
            else 0,
        }

    if page.source_entity_type == "shopify_collection":
        collection = await session.get(ShopifyCollection, page.source_entity_id)
        if collection is None:
            return None
        return {
            "entityType": "collection",
            "title": collection.title,
            "handle": collection.handle,
            "seoTitle": collection.seo_title,
            "seoDescription": collection.seo_description,
            "descriptionText": collection.description_text,
            "productsCount": collection.products_count,
            "imageUrl": collection.image_url,
            "imageAlt": collection.image_alt,
        }

    return None


async def _build_page_analysis_context(
    session: AsyncSession,
    *,
    run: GrowthAuditRun,
    page: GrowthAuditPage,
    technical_result: GrowthAuditPageResult,
    note: str | None,
) -> dict[str, Any]:
    metadata = page.page_metadata or {}
    technical_meta = metadata.get("technical") if isinstance(metadata.get("technical"), dict) else {}

    open_findings = (
        await session.execute(
            select(GrowthAuditFinding)
            .where(
                GrowthAuditFinding.page_id == page.id,
                GrowthAuditFinding.project_id == page.project_id,
                GrowthAuditFinding.run_id == run.id,
                GrowthAuditFinding.status == "open",
            )
            .order_by(GrowthAuditFinding.created_at.desc())
            .limit(12)
        )
    ).scalars().all()

    open_tasks = (
        await session.execute(
            select(GrowthAuditTask)
            .where(
                GrowthAuditTask.page_id == page.id,
                GrowthAuditTask.project_id == page.project_id,
                GrowthAuditTask.run_id == run.id,
                GrowthAuditTask.status == "open",
            )
            .order_by(GrowthAuditTask.created_at.desc())
            .limit(12)
        )
    ).scalars().all()

    shopify_entity = await _load_shopify_entity(session, page)

    return {
        "url": page.url,
        "pageType": page.page_type,
        "technicalScore": page.score,
        "httpStatus": page.http_status,
        "title": page.title,
        "metaDescription": page.meta_description,
        "h1": page.h1,
        "canonicalUrl": page.canonical_url,
        "sourceEntityType": page.source_entity_type,
        "sourceEntityTitle": page.source_entity_title,
        "sourceEntityHandle": page.source_entity_handle,
        "technicalMetadata": technical_meta,
        "technicalFindings": technical_result.findings or [],
        "technicalTasks": technical_result.tasks or [],
        "existingOpenFindings": [
            {
                "category": f.category,
                "severity": f.severity,
                "title": f.title,
                "recommendation": f.recommendation,
            }
            for f in open_findings
        ],
        "existingOpenTasks": [
            {
                "title": t.title,
                "ownerType": t.owner_type,
                "priority": t.priority,
            }
            for t in open_tasks
        ],
        "shopifyEntity": shopify_entity,
        "analysisNote": note,
        "runDomain": run.normalized_domain,
    }


async def _update_run_summary_after_ai_analysis(
    session: AsyncSession,
    run: GrowthAuditRun,
    *,
    page: GrowthAuditPage,
    analyzed_at: datetime,
) -> None:
    ai_pages_analyzed = (
        await session.execute(
            select(func.count(func.distinct(GrowthAuditPageResult.page_id)))
            .select_from(GrowthAuditPageResult)
            .where(
                GrowthAuditPageResult.run_id == run.id,
                GrowthAuditPageResult.project_id == run.project_id,
                GrowthAuditPageResult.result_type == AI_RESULT_TYPE,
                GrowthAuditPageResult.status == "completed",
            )
        )
    ).scalar_one()

    geo_findings = (
        await session.execute(
            select(func.count())
            .select_from(GrowthAuditFinding)
            .where(
                GrowthAuditFinding.run_id == run.id,
                GrowthAuditFinding.project_id == run.project_id,
                GrowthAuditFinding.status == "open",
                GrowthAuditFinding.category == "geo",
            )
        )
    ).scalar_one()

    cro_findings = (
        await session.execute(
            select(func.count())
            .select_from(GrowthAuditFinding)
            .where(
                GrowthAuditFinding.run_id == run.id,
                GrowthAuditFinding.project_id == run.project_id,
                GrowthAuditFinding.status == "open",
                GrowthAuditFinding.category == "cro",
            )
        )
    ).scalar_one()

    ads_findings = (
        await session.execute(
            select(func.count())
            .select_from(GrowthAuditFinding)
            .where(
                GrowthAuditFinding.run_id == run.id,
                GrowthAuditFinding.project_id == run.project_id,
                GrowthAuditFinding.status == "open",
                GrowthAuditFinding.category == "ads",
            )
        )
    ).scalar_one()

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

    existing_summary = dict(run.summary or {})
    run.summary = {
        **existing_summary,
        "criticalFindings": critical_count,
        "highFindings": high_count,
        "tasksOpen": tasks_open,
        "aiPagesAnalyzed": ai_pages_analyzed,
        "geoFindings": geo_findings,
        "croFindings": cro_findings,
        "adsFindings": ads_findings,
        "lastAiAnalysisAt": analyzed_at.isoformat(),
        "lastAiAnalysisUrl": page.url,
    }


def _readable_ai_failure_message(exc: Exception, *, provider: str) -> str:
    msg = str(exc)
    lowered = msg.lower()
    if "not configured" in lowered or "non configurato" in lowered:
        return (
            f"Provider {provider} non configurato. "
            "Verifica le credenziali AI del progetto."
        )
    if "invalid schema for response_format" in lowered:
        return (
            "Analisi AI non riuscita: configurazione output non valida. "
            "Riprova dopo l'aggiornamento del sistema."
        )
    return f"Analisi AI non riuscita: {msg}"


async def _persist_failed_ai_result(
    session: AsyncSession,
    *,
    run: GrowthAuditRun,
    page: GrowthAuditPage,
    started_at: datetime,
    error_message: str,
    raw_output: dict[str, Any] | None = None,
) -> GrowthAuditPageResult:
    now = _utcnow()
    page_result = GrowthAuditPageResult(
        run_id=run.id,
        page_id=page.id,
        project_id=run.project_id,
        result_type=AI_RESULT_TYPE,
        skill_key=AI_SKILL_KEY,
        status="failed",
        summary="Analisi AI non riuscita.",
        error_message=error_message,
        raw_output=raw_output,
        started_at=started_at,
        completed_at=now,
    )
    session.add(page_result)
    await session.flush()

    await create_growth_audit_event(
        session,
        run_id=run.id,
        project_id=run.project_id,
        event_type="page_ai_analysis_failed",
        phase="analysis",
        message=f"Analisi AI fallita: {page.url}",
        progress_percent=run.progress_percent,
        payload={
            "pageId": str(page.id),
            "url": page.url,
            "error": error_message,
            "resultId": str(page_result.id),
        },
    )
    await session.commit()
    return page_result


async def analyze_growth_audit_page_with_ai(
    session: AsyncSession,
    *,
    project_id: UUID,
    run_id: UUID,
    page_id: UUID,
    provider: str = "openai",
    depth: str = "standard",
    include_seo: bool = True,
    include_geo: bool = True,
    include_cro: bool = True,
    include_ads_readiness: bool = True,
    note: str | None = None,
) -> tuple[GrowthAuditRun, GrowthAuditPage, GrowthAuditPageResult, int, int]:
    run = await get_growth_audit_run(session, project_id, run_id)
    if run is None:
        raise GrowthAuditRunNotFoundError(f"Growth Audit run {run_id} not found")

    if run.status in _ACTIVE_RUN_STATUSES:
        raise GrowthAuditValidationError(
            "Impossibile avviare l'analisi AI mentre il run è ancora in corso."
        )

    normalized_provider = (provider or "openai").strip().lower()
    if normalized_provider not in SUPPORTED_PROVIDERS:
        raise GrowthAuditValidationError(f"Provider AI non supportato: {provider}")

    page = await _get_growth_audit_page(
        session,
        project_id=project_id,
        run_id=run_id,
        page_id=page_id,
    )
    if page is None:
        raise GrowthAuditValidationError(f"Pagina {page_id} non trovata nel run.")

    if page.status != "analyzed":
        raise GrowthAuditValidationError(
            "L'analisi AI richiede una pagina con scansione tecnica completata."
        )

    technical_result = await _load_latest_technical_result(
        session,
        page_id=page.id,
        project_id=project_id,
        run_id=run_id,
    )
    if technical_result is None:
        raise GrowthAuditValidationError(
            "Nessun risultato tecnico disponibile per questa pagina. Esegui prima la scansione."
        )

    started_at = _utcnow()
    await create_growth_audit_event(
        session,
        run_id=run.id,
        project_id=project_id,
        event_type="page_ai_analysis_started",
        phase="analysis",
        message=f"Analisi AI avviata: {page.url}",
        progress_percent=run.progress_percent,
        payload={
            "pageId": str(page.id),
            "url": page.url,
            "provider": normalized_provider,
            "depth": depth,
        },
    )
    await session.flush()

    context = await _build_page_analysis_context(
        session,
        run=run,
        page=page,
        technical_result=technical_result,
        note=note,
    )
    system_prompt = build_system_prompt(
        page.page_type,
        include_seo=include_seo,
        include_geo=include_geo,
        include_cro=include_cro,
        include_ads_readiness=include_ads_readiness,
        depth=depth,
    )
    user_prompt = build_user_prompt(context)

    metadata = AiRequestMetadata(
        project_id=project_id,
        module="growth_audit",
        operation="page_ai_analysis",
        operation_key="growth_audit_page_ai_analysis",
        entity_type="growth_audit_page",
        entity_id=str(page.id),
        job_id=str(run.id),
        context_profile="growth_audit_page_ai",
    )

    json_schema = (
        get_growth_audit_page_ai_output_json_schema()
        if normalized_provider == "openai"
        else None
    )

    try:
        raw_output = await generate_structured_json_with_provider(
            provider=normalized_provider,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            metadata=metadata,
            timeout=90.0,
            json_schema=json_schema,
            json_schema_name="growth_audit_page_ai_output" if json_schema else None,
        )
    except Exception as exc:
        readable = _readable_ai_failure_message(exc, provider=normalized_provider)
        await _persist_failed_ai_result(
            session,
            run=run,
            page=page,
            started_at=started_at,
            error_message=readable,
        )
        raise GrowthAuditValidationError(readable) from exc

    if not isinstance(raw_output, dict):
        readable = "L'AI ha restituito un output non valido."
        await _persist_failed_ai_result(
            session,
            run=run,
            page=page,
            started_at=started_at,
            error_message=readable,
            raw_output={"raw": raw_output},
        )
        raise GrowthAuditValidationError(readable)

    normalized = normalize_growth_audit_page_ai_output(raw_output, page_type=page.page_type)
    if not normalized.get("summary"):
        readable = "L'AI non ha prodotto un riepilogo valido."
        await _persist_failed_ai_result(
            session,
            run=run,
            page=page,
            started_at=started_at,
            error_message=readable,
            raw_output=raw_output,
        )
        raise GrowthAuditValidationError(readable)

    now = _utcnow()
    page_result = GrowthAuditPageResult(
        run_id=run.id,
        page_id=page.id,
        project_id=project_id,
        result_type=AI_RESULT_TYPE,
        skill_key=AI_SKILL_KEY,
        status="completed",
        score=normalized.get("score"),
        summary=normalized.get("summary"),
        findings=normalized.get("findings"),
        recommendations=normalized.get("recommendations"),
        tasks=normalized.get("tasks"),
        artifacts=normalized.get("artifacts"),
        raw_output=raw_output,
        started_at=started_at,
        completed_at=now,
    )
    session.add(page_result)
    await session.flush()

    for finding_data in normalized.get("findings") or []:
        session.add(
            GrowthAuditFinding(
                run_id=run.id,
                page_id=page.id,
                project_id=project_id,
                source_result_id=page_result.id,
                category=finding_data.get("category", "seo"),
                severity=finding_data.get("severity", "medium"),
                priority=finding_data.get("priority", "medium"),
                title=finding_data.get("title", "Finding AI"),
                description=finding_data.get("description"),
                evidence=finding_data.get("evidence"),
                recommendation=finding_data.get("recommendation"),
                how_to_validate=finding_data.get("howToValidate"),
                impact=finding_data.get("impact"),
                effort=finding_data.get("effort"),
                status="open",
            )
        )

    for task_data in normalized.get("tasks") or []:
        session.add(
            GrowthAuditTask(
                run_id=run.id,
                page_id=page.id,
                project_id=project_id,
                title=task_data.get("title", "Task AI"),
                description=task_data.get("description"),
                owner_type=task_data.get("ownerType", "seo"),
                priority=task_data.get("priority", "medium"),
                estimated_effort=task_data.get("estimatedEffort", "medium"),
                status="open",
            )
        )

    if normalized.get("geoScore") is not None:
        page.geo_score = normalized["geoScore"]
    if normalized.get("croScore") is not None:
        page.cro_score = normalized["croScore"]
    if normalized.get("seoScore") is not None:
        page.seo_score = normalized["seoScore"]

    page.page_metadata = {
        **(page.page_metadata or {}),
        "ai": {
            "latestResultId": str(page_result.id),
            "latestScore": normalized.get("score"),
            "seoScore": normalized.get("seoScore"),
            "geoScore": normalized.get("geoScore"),
            "croScore": normalized.get("croScore"),
            "adsReadinessScore": normalized.get("adsReadinessScore"),
            "analyzedAt": now.isoformat(),
        },
    }

    await _update_run_summary_after_ai_analysis(session, run, page=page, analyzed_at=now)

    await create_growth_audit_event(
        session,
        run_id=run.id,
        project_id=project_id,
        event_type="page_ai_analysis_completed",
        phase="analysis",
        message=f"Analisi AI completata: {page.url}",
        progress_percent=run.progress_percent,
        payload={
            "pageId": str(page.id),
            "url": page.url,
            "resultId": str(page_result.id),
            "score": normalized.get("score"),
            "findingsCount": len(normalized.get("findings") or []),
            "tasksCount": len(normalized.get("tasks") or []),
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


async def list_growth_audit_page_results(
    session: AsyncSession,
    *,
    project_id: UUID,
    run_id: UUID,
    page_id: UUID,
    result_type: str | None = None,
) -> list[GrowthAuditPageResult]:
    page = await _get_growth_audit_page(
        session,
        project_id=project_id,
        run_id=run_id,
        page_id=page_id,
    )
    if page is None:
        raise GrowthAuditValidationError(f"Pagina {page_id} non trovata nel run.")

    query = (
        select(GrowthAuditPageResult)
        .where(
            GrowthAuditPageResult.page_id == page_id,
            GrowthAuditPageResult.run_id == run_id,
            GrowthAuditPageResult.project_id == project_id,
        )
        .order_by(GrowthAuditPageResult.created_at.desc())
    )
    if result_type:
        query = query.where(GrowthAuditPageResult.result_type == result_type)

    result = await session.execute(query)
    return list(result.scalars().all())
