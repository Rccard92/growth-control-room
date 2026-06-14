"""Batch brief generation job for Content SEO editorial calendar."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session_factory
from app.models.content_seo_brief_job import ContentSeoBriefGenerationJob
from app.models.content_seo_editorial import ContentSeoEditorialItem
from app.schemas.content_seo_editorial import (
    EditorialBriefBatchJobResponse,
    EditorialBriefBatchStartRequest,
)
from app.services.ai.openai_client import is_openai_configured
from app.services.content.editorial_brief_service import (
    BriefGenerationError,
    generate_editorial_brief_core,
)
from app.services.content.editorial_item_service import list_editorial_items

logger = logging.getLogger(__name__)


def has_editorial_brief_payload(payload: dict[str, Any] | None) -> bool:
    if not payload:
        return False
    proposed = str(payload.get("proposedTitle") or "").strip()
    primary = str(payload.get("primaryKeyword") or "").strip()
    meta = str(payload.get("metaTitle") or "").strip()
    h2 = payload.get("h2H3Structure") or []
    if proposed or primary or meta:
        return True
    if isinstance(h2, list) and len(h2) > 0:
        return True
    return False


async def find_batch_candidates(
    session: AsyncSession,
    project_id: UUID,
    month: str,
    only_status: str,
) -> list[ContentSeoEditorialItem]:
    rows = await list_editorial_items(
        session,
        project_id,
        month=month,
        status=only_status,
    )
    return [r for r in rows if not has_editorial_brief_payload(r.brief_payload)]


def _progress_percent(job: ContentSeoBriefGenerationJob) -> int:
    if job.total_items <= 0:
        return 0
    done = job.completed_items + job.failed_items
    return min(100, round(done / job.total_items * 100))


def job_to_response(job: ContentSeoBriefGenerationJob) -> EditorialBriefBatchJobResponse:
    raw_errors = job.errors or []
    return EditorialBriefBatchJobResponse(
        job_id=job.id,
        status=job.status,
        total_items=job.total_items,
        completed_items=job.completed_items,
        failed_items=job.failed_items,
        current_item_title=job.current_item_title,
        progress_percent=_progress_percent(job),
        errors=raw_errors,
    )


async def get_brief_batch_job(
    session: AsyncSession,
    project_id: UUID,
    job_id: UUID,
) -> ContentSeoBriefGenerationJob:
    row = (
        await session.execute(
            select(ContentSeoBriefGenerationJob).where(
                ContentSeoBriefGenerationJob.id == job_id,
                ContentSeoBriefGenerationJob.project_id == project_id,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Job di generazione brief non trovato.")
    return row


async def create_brief_batch_job(
    session: AsyncSession,
    project_id: UUID,
    request: EditorialBriefBatchStartRequest,
) -> ContentSeoBriefGenerationJob:
    if not is_openai_configured():
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI non configurata. Inserisci OPENAI_API_KEY per generare i brief.",
        )

    candidates = await find_batch_candidates(
        session,
        project_id,
        request.month,
        request.only_status,
    )
    if not candidates:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Nessun contenuto in stato Idea da elaborare.",
        )

    job = ContentSeoBriefGenerationJob(
        id=uuid4(),
        project_id=project_id,
        status="pending",
        month=request.month,
        only_status=request.only_status,
        total_items=len(candidates),
        completed_items=0,
        failed_items=0,
        errors=[],
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job


def schedule_brief_batch_job(job_id: UUID) -> None:
    asyncio.create_task(process_brief_batch_job(job_id))


async def process_brief_batch_job(job_id: UUID) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        job = (
            await session.execute(
                select(ContentSeoBriefGenerationJob).where(
                    ContentSeoBriefGenerationJob.id == job_id
                )
            )
        ).scalar_one_or_none()
        if not job:
            logger.error("Brief batch job %s non trovato", job_id)
            return

        project_id = job.project_id
        job.status = "running"
        await session.commit()

        if not job.month:
            job.status = "failed"
            job.completed_at = datetime.now(timezone.utc)
            await session.commit()
            return

        candidates = await find_batch_candidates(
            session,
            project_id,
            job.month,
            job.only_status,
        )
        item_ids = [c.id for c in candidates]
        job.total_items = len(item_ids)
        await session.commit()

        errors: list[dict[str, Any]] = list(job.errors or [])

        for item_id in item_ids:
            item = (
                await session.execute(
                    select(ContentSeoEditorialItem).where(
                        ContentSeoEditorialItem.id == item_id,
                        ContentSeoEditorialItem.project_id == project_id,
                    )
                )
            ).scalar_one_or_none()
            if not item:
                job.failed_items += 1
                errors.append(
                    {
                        "itemId": str(item_id),
                        "title": "—",
                        "message": "Brief non generato per questo contenuto.",
                    }
                )
                job.errors = errors
                await session.commit()
                continue

            job.current_item_id = item.id
            job.current_item_title = item.title
            await session.commit()

            try:
                await generate_editorial_brief_core(
                    session, project_id, item.id, job_id=str(job_id)
                )
                job.completed_items += 1
            except BriefGenerationError as exc:
                job.failed_items += 1
                errors.append(
                    {
                        "itemId": str(item.id),
                        "title": item.title,
                        "message": str(exc),
                    }
                )
                job.errors = errors
                await session.commit()
            except Exception as exc:
                logger.exception("Unexpected batch brief error for %s", item.id)
                job.failed_items += 1
                errors.append(
                    {
                        "itemId": str(item.id),
                        "title": item.title,
                        "message": "Brief non generato per questo contenuto.",
                    }
                )
                job.errors = errors
                await session.commit()

        job.current_item_id = None
        job.current_item_title = None
        job.completed_at = datetime.now(timezone.utc)

        if job.failed_items == 0:
            job.status = "completed"
        elif job.completed_items == 0:
            job.status = "failed"
        else:
            job.status = "partial_failed"

        await session.commit()


async def start_brief_batch_job(
    session: AsyncSession,
    project_id: UUID,
    request: EditorialBriefBatchStartRequest,
) -> EditorialBriefBatchJobResponse:
    job = await create_brief_batch_job(session, project_id, request)
    schedule_brief_batch_job(job.id)
    return job_to_response(job)
