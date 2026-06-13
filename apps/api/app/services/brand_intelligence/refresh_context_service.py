"""Async refresh of batch context: fetch external sources + archive drafts + synthesize."""

from __future__ import annotations

import asyncio
import logging
from uuid import UUID

from sqlalchemy import select

from app.db.session import get_session_factory
from app.models.brand_intelligence import BrandImportBatch, BrandSectionDraft
from app.services.brand_intelligence.batch_service import update_batch_progress
from app.services.brand_intelligence.external_sources_service import fetch_batch_external_sources

logger = logging.getLogger(__name__)

ARCHIVE_DRAFT_STATUSES = frozenset({"draft", "needs_review", "approved"})


def schedule_refresh_context(
    batch_id: UUID,
    *,
    refetch_external_sources: bool = True,
    regenerate_section_drafts: bool = True,
    archive_previous_drafts: bool = True,
) -> None:
    asyncio.create_task(
        refresh_batch_context(
            batch_id,
            refetch_external_sources=refetch_external_sources,
            regenerate_section_drafts=regenerate_section_drafts,
            archive_previous_drafts=archive_previous_drafts,
        )
    )


async def refresh_batch_context(
    batch_id: UUID,
    *,
    refetch_external_sources: bool = True,
    regenerate_section_drafts: bool = True,
    archive_previous_drafts: bool = True,
) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        batch = (
            await session.execute(
                select(BrandImportBatch).where(BrandImportBatch.id == batch_id)
            )
        ).scalar_one_or_none()
        if not batch:
            logger.error("Batch %s non trovato per refresh context", batch_id)
            return

        project_id = batch.project_id

        try:
            await update_batch_progress(
                session,
                batch,
                status="ai_processing",
                progress_percent=5,
                current_step="Salvataggio fonti brand",
                commit=True,
            )

            if refetch_external_sources:
                await update_batch_progress(
                    session,
                    batch,
                    progress_percent=20,
                    current_step="Recupero sito web",
                    commit=True,
                )
                await fetch_batch_external_sources(
                    session, batch_id, refetch_failed=True
                )
                batch = (
                    await session.execute(
                        select(BrandImportBatch).where(BrandImportBatch.id == batch_id)
                    )
                ).scalar_one()
                await update_batch_progress(
                    session,
                    batch,
                    progress_percent=35,
                    current_step="Recupero fonti social e recensioni",
                    commit=True,
                )
                await update_batch_progress(
                    session,
                    batch,
                    progress_percent=55,
                    current_step="Integrazione fonti esterne con i documenti",
                    commit=True,
                )

            if archive_previous_drafts:
                drafts = list(
                    (
                        await session.execute(
                            select(BrandSectionDraft).where(
                                BrandSectionDraft.batch_id == batch_id,
                                BrandSectionDraft.status.in_(tuple(ARCHIVE_DRAFT_STATUSES)),
                            )
                        )
                    ).scalars().all()
                )
                for draft in drafts:
                    draft.status = "rejected"
                await session.commit()

            if regenerate_section_drafts:
                await update_batch_progress(
                    session,
                    batch,
                    progress_percent=75,
                    current_step="Rigenerazione bozze Brand Intelligence",
                    commit=True,
                )
                from app.services.brand_intelligence.synthesis import synthesize_batch

                await synthesize_batch(
                    session, project_id, batch_id, update_progress=False
                )

            batch = (
                await session.execute(
                    select(BrandImportBatch).where(BrandImportBatch.id == batch_id)
                )
            ).scalar_one()
            await update_batch_progress(
                session,
                batch,
                status="review_ready",
                progress_percent=100,
                current_step="Bozze pronte per revisione",
                commit=True,
            )

        except Exception as exc:
            logger.exception("Refresh context failed for batch %s", batch_id)
            batch = (
                await session.execute(
                    select(BrandImportBatch).where(BrandImportBatch.id == batch_id)
                )
            ).scalar_one_or_none()
            if batch:
                batch.status = "partially_failed"
                batch.error_message = str(exc)
                batch.current_step = "Aggiornamento contesto fallito"
                await session.commit()
