"""Brand import batch lifecycle and progress tracking."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brand_intelligence import (
    BrandExtractedFact,
    BrandImportBatch,
    BrandSourceDocument,
)
from app.schemas.brand_intelligence import (
    BrandImportBatchDocumentStatus,
    BrandImportBatchListItem,
    BrandImportBatchStatusResponse,
    BrandSourceDocumentUploadItem,
    BrandSourceDocumentsUploadResponse,
)
from app.services.brand_intelligence.text_extraction import (
    MAX_BATCH_FILES,
    TextExtractionError,
    extract_text_from_bytes,
)

ACTIVE_BATCH_STATUSES = frozenset({"pending", "uploading", "extracting", "ai_processing"})
TERMINAL_BATCH_STATUSES = frozenset({"review_ready", "partially_failed", "completed", "failed"})


async def create_batch(
    session: AsyncSession,
    project_id: UUID,
    *,
    name: str | None = None,
    source_type: str = "file_upload",
    notes: str | None = None,
) -> BrandImportBatch:
    batch = BrandImportBatch(
        project_id=project_id,
        name=name,
        source_type=source_type,
        notes=notes,
        status="pending",
        progress_percent=0,
        current_step="In attesa di avvio",
    )
    session.add(batch)
    await session.flush()
    return batch


async def update_batch_progress(
    session: AsyncSession,
    batch: BrandImportBatch,
    *,
    progress_percent: int | None = None,
    current_step: str | None = None,
    status: str | None = None,
    error_message: str | None = None,
    warnings: list[str] | None = None,
    commit: bool = True,
) -> None:
    if progress_percent is not None:
        batch.progress_percent = max(0, min(100, progress_percent))
    if current_step is not None:
        batch.current_step = current_step
    if status is not None:
        batch.status = status
        if status in TERMINAL_BATCH_STATUSES and batch.completed_at is None:
            batch.completed_at = datetime.now(timezone.utc)
    if error_message is not None:
        batch.error_message = error_message
    if warnings is not None:
        batch.warnings = warnings
    if commit:
        await session.commit()


async def finalize_batch_counts(session: AsyncSession, batch_id: UUID) -> BrandImportBatch:
    batch = await _get_batch(session, batch_id)
    docs = list(
        (
            await session.execute(
                select(BrandSourceDocument).where(BrandSourceDocument.batch_id == batch_id)
            )
        ).scalars().all()
    )
    facts = list(
        (
            await session.execute(
                select(BrandExtractedFact).where(BrandExtractedFact.batch_id == batch_id)
            )
        ).scalars().all()
    )

    batch.total_files = len(docs)
    batch.processed_files = sum(
        1 for d in docs if d.extraction_status in ("extracted", "failed")
    )
    batch.total_facts = len(facts)
    batch.approved_facts = sum(1 for f in facts if f.status == "approved")
    batch.rejected_facts = sum(1 for f in facts if f.status == "rejected")
    batch.needs_review_facts = sum(
        1 for f in facts if f.status in ("suggested", "needs_review")
    )

    for doc in docs:
        doc_facts = [f for f in facts if f.source_document_id == doc.id]
        doc.extracted_facts_count = len(doc_facts)
        doc.needs_review_count = sum(
            1 for f in doc_facts if f.status in ("suggested", "needs_review")
        )
        doc.approved_count = sum(1 for f in doc_facts if f.status == "approved")
        doc.rejected_count = sum(1 for f in doc_facts if f.status == "rejected")

    await session.commit()
    await session.refresh(batch)
    return batch


async def upload_files_to_batch(
    session: AsyncSession,
    project_id: UUID,
    files: list[UploadFile],
    *,
    batch_name: str | None = None,
    source_type: str = "file_upload",
    notes: str | None = None,
) -> BrandSourceDocumentsUploadResponse:
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nessun file caricato.")
    if len(files) > MAX_BATCH_FILES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Massimo {MAX_BATCH_FILES} file per batch.",
        )

    batch = await create_batch(
        session,
        project_id,
        name=batch_name or f"Import {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}",
        source_type=source_type,
        notes=notes,
    )
    batch.status = "uploading"
    batch.current_step = "Caricamento file"
    batch.total_files = len(files)
    batch.started_at = datetime.now(timezone.utc)

    now = datetime.now(timezone.utc)
    uploaded: list[BrandSourceDocumentUploadItem] = []

    for order, upload in enumerate(files, start=1):
        filename = upload.filename or "document"
        data = await upload.read()
        doc = BrandSourceDocument(
            project_id=project_id,
            batch_id=batch.id,
            filename=filename,
            content_type=upload.content_type or "application/octet-stream",
            file_size=len(data),
            storage_mode="text_only",
            extraction_status="uploaded",
            processing_order=order,
            progress_percent=0,
            current_step="In coda",
            uploaded_at=now,
        )
        try:
            doc.extracted_text = extract_text_from_bytes(
                content_type=doc.content_type,
                filename=filename,
                data=data,
            )
            doc.extraction_error = None
        except TextExtractionError as exc:
            doc.extraction_status = "failed"
            doc.extraction_error = exc.message
            doc.extracted_text = None

        session.add(doc)
        await session.flush()
        uploaded.append(
            BrandSourceDocumentUploadItem(
                id=doc.id,
                filename=doc.filename,
                status=doc.extraction_status,
            )
        )

    batch.status = "extracting"
    batch.progress_percent = 5
    batch.current_step = "Upload completato"
    await session.commit()

    return BrandSourceDocumentsUploadResponse(
        batch_id=batch.id,
        status=batch.status,
        documents=uploaded,
    )


async def get_batch_status(
    session: AsyncSession,
    project_id: UUID,
    batch_id: UUID,
) -> BrandImportBatchStatusResponse:
    batch = await _get_batch_for_project(session, project_id, batch_id)
    docs = list(
        (
            await session.execute(
                select(BrandSourceDocument)
                .where(BrandSourceDocument.batch_id == batch_id)
                .order_by(BrandSourceDocument.processing_order.asc())
            )
        ).scalars().all()
    )
    warnings = batch.warnings or []
    return BrandImportBatchStatusResponse(
        id=batch.id,
        project_id=batch.project_id,
        name=batch.name,
        source_type=batch.source_type,
        notes=batch.notes,
        status=batch.status,
        progress_percent=batch.progress_percent,
        current_step=batch.current_step,
        total_files=batch.total_files,
        processed_files=batch.processed_files,
        total_facts=batch.total_facts,
        approved_facts=batch.approved_facts,
        rejected_facts=batch.rejected_facts,
        needs_review_facts=batch.needs_review_facts,
        error_message=batch.error_message,
        warnings=warnings,
        started_at=batch.started_at,
        completed_at=batch.completed_at,
        created_at=batch.created_at,
        updated_at=batch.updated_at,
        documents=[
            BrandImportBatchDocumentStatus(
                id=d.id,
                filename=d.filename,
                extraction_status=d.extraction_status,
                progress_percent=d.progress_percent,
                current_step=d.current_step,
                extracted_facts_count=d.extracted_facts_count,
                extraction_error=d.extraction_error,
            )
            for d in docs
        ],
    )


async def list_batches(
    session: AsyncSession,
    project_id: UUID,
) -> list[BrandImportBatchListItem]:
    rows = list(
        (
            await session.execute(
                select(BrandImportBatch)
                .where(BrandImportBatch.project_id == project_id)
                .order_by(BrandImportBatch.created_at.desc())
            )
        ).scalars().all()
    )
    return [BrandImportBatchListItem.model_validate(r) for r in rows]


async def mark_batch_started(
    session: AsyncSession, project_id: UUID, batch_id: UUID
) -> BrandImportBatch:
    batch = await _get_batch_for_project(session, project_id, batch_id)
    if batch.status in TERMINAL_BATCH_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Batch già terminato con status {batch.status}.",
        )
    batch.status = "extracting"
    batch.started_at = batch.started_at or datetime.now(timezone.utc)
    batch.current_step = "Avvio elaborazione"
    await session.commit()
    await session.refresh(batch)
    return batch


async def update_batch_after_apply(
    session: AsyncSession,
    project_id: UUID,
    batch_id: UUID,
) -> None:
    batch = await _get_batch_for_project(session, project_id, batch_id)
    await finalize_batch_counts(session, batch.id)
    pending = int(
        (
            await session.execute(
                select(func.count())
                .select_from(BrandExtractedFact)
                .where(
                    BrandExtractedFact.batch_id == batch_id,
                    BrandExtractedFact.status.in_(("suggested", "needs_review")),
                )
            )
        ).scalar_one()
    )
    if pending == 0 and batch.status in ("review_ready", "partially_failed"):
        batch.status = "completed"
        batch.progress_percent = 100
        batch.current_step = "Import completato"
        batch.completed_at = datetime.now(timezone.utc)
        await session.commit()


async def _get_batch(session: AsyncSession, batch_id: UUID) -> BrandImportBatch:
    batch = (
        await session.execute(select(BrandImportBatch).where(BrandImportBatch.id == batch_id))
    ).scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch non trovato.")
    return batch


async def _get_batch_for_project(
    session: AsyncSession, project_id: UUID, batch_id: UUID
) -> BrandImportBatch:
    batch = (
        await session.execute(
            select(BrandImportBatch).where(
                BrandImportBatch.id == batch_id,
                BrandImportBatch.project_id == project_id,
            )
        )
    ).scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch non trovato.")
    return batch
