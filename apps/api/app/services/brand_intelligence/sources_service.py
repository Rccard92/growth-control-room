"""Source document upload and extracted fact review services."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brand_intelligence import BrandExtractedFact, BrandSourceDocument
from app.schemas.brand_intelligence import (
    BrandApplyFactsCounts,
    BrandApplyFactsResponse,
    BrandApplyFactsResultItem,
    BrandExtractedFactUpdate,
    BrandSourceDocumentRead,
)
from app.services.brand_intelligence.batch_service import update_batch_after_apply, upload_files_to_batch
from app.services.brand_intelligence.document_extraction import run_ai_extraction_batch
from app.services.brand_intelligence.fact_apply import apply_approved_facts
from app.services.brand_intelligence.text_extraction import MAX_BATCH_FILES  # noqa: F401 — re-export for tests


async def list_source_documents(
    session: AsyncSession, project_id: UUID
) -> list[BrandSourceDocument]:
    return list(
        (
            await session.execute(
                select(BrandSourceDocument)
                .where(BrandSourceDocument.project_id == project_id)
                .order_by(BrandSourceDocument.uploaded_at.desc())
            )
        ).scalars().all()
    )


async def upload_source_documents(
    session: AsyncSession,
    project_id: UUID,
    files: list[UploadFile],
    *,
    batch_name: str | None = None,
    source_type: str = "file_upload",
    notes: str | None = None,
    brand_name: str | None = None,
    website_url: str | None = None,
    sources: list | None = None,
    batch_id: UUID | None = None,
):
    return await upload_files_to_batch(
        session,
        project_id,
        files,
        batch_name=batch_name,
        source_type=source_type,
        notes=notes,
        brand_name=brand_name,
        website_url=website_url,
        sources=sources,
        batch_id=batch_id,
    )


async def list_extracted_facts(
    session: AsyncSession,
    project_id: UUID,
    *,
    status_filter: str | None = None,
    target_section: str | None = None,
    source_document_id: UUID | None = None,
    batch_id: UUID | None = None,
) -> list[BrandExtractedFact]:
    query = select(BrandExtractedFact).where(BrandExtractedFact.project_id == project_id)
    if status_filter:
        query = query.where(BrandExtractedFact.status == status_filter)
    if target_section:
        query = query.where(BrandExtractedFact.target_section == target_section)
    if source_document_id:
        query = query.where(BrandExtractedFact.source_document_id == source_document_id)
    if batch_id:
        query = query.where(BrandExtractedFact.batch_id == batch_id)
    query = query.order_by(BrandExtractedFact.created_at.desc())
    return list((await session.execute(query)).scalars().all())


async def patch_extracted_fact(
    session: AsyncSession,
    project_id: UUID,
    fact_id: UUID,
    payload: BrandExtractedFactUpdate,
) -> BrandExtractedFact:
    row = (
        await session.execute(
            select(BrandExtractedFact).where(
                BrandExtractedFact.id == fact_id,
                BrandExtractedFact.project_id == project_id,
            )
        )
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fact non trovato.")

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(row, key, value)
    if payload.status in ("approved", "rejected", "needs_review"):
        row.reviewed_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(row)
    return row


async def apply_facts(
    session: AsyncSession,
    project_id: UUID,
    fact_ids: list[UUID],
    batch_id: UUID | None = None,
) -> BrandApplyFactsResponse:
    result = await apply_approved_facts(session, project_id, fact_ids)
    if batch_id:
        await update_batch_after_apply(session, project_id, batch_id)
    return BrandApplyFactsResponse(
        saved=[
            BrandApplyFactsResultItem(
                fact_id=item.fact_id,
                target_section=item.target_section,
                field_name=item.field_name,
                message=item.message,
            )
            for item in result.saved
        ],
        skipped=[
            BrandApplyFactsResultItem(
                fact_id=item.fact_id,
                target_section=item.target_section,
                field_name=item.field_name,
                message=item.message,
            )
            for item in result.skipped
        ],
        counts=BrandApplyFactsCounts(
            saved=len(result.saved),
            skipped=len(result.skipped),
            needs_review=result.needs_review,
            rejected=result.rejected,
        ),
    )


async def count_pending_facts(session: AsyncSession, project_id: UUID) -> int:
    return int(
        (
            await session.execute(
                select(func.count())
                .select_from(BrandExtractedFact)
                .where(
                    BrandExtractedFact.project_id == project_id,
                    BrandExtractedFact.status.in_(("suggested", "needs_review")),
                )
            )
        ).scalar_one()
    )


async def count_source_documents(session: AsyncSession, project_id: UUID) -> int:
    return int(
        (
            await session.execute(
                select(func.count())
                .select_from(BrandSourceDocument)
                .where(BrandSourceDocument.project_id == project_id)
            )
        ).scalar_one()
    )


async def extract_document_batch(
    session: AsyncSession,
    project_id: UUID,
    document_ids: list[UUID],
) -> dict:
    if not document_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nessun documento selezionato.")
    return await run_ai_extraction_batch(session, project_id, document_ids)
