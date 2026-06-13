"""CRUD and orchestration for BrandSectionDraft."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brand_intelligence import BrandImportBatch, BrandSectionDraft
from app.schemas.brand_intelligence import BrandSectionDraftUpdate
from app.schemas.section_drafts import validate_draft_payload
from app.services.brand_intelligence.synthesis import synthesize_section

PENDING_DRAFT_STATUSES = frozenset({"draft", "needs_review", "approved"})


async def list_section_drafts(
    session: AsyncSession,
    project_id: UUID,
    *,
    batch_id: UUID | None = None,
    status_filter: str | None = None,
    section_key: str | None = None,
    latest_only: bool = True,
) -> list[BrandSectionDraft]:
    query = select(BrandSectionDraft).where(BrandSectionDraft.project_id == project_id)
    if batch_id:
        query = query.where(BrandSectionDraft.batch_id == batch_id)
    if status_filter:
        query = query.where(BrandSectionDraft.status == status_filter)
    if section_key:
        query = query.where(BrandSectionDraft.section_key == section_key)
    query = query.order_by(BrandSectionDraft.created_at.desc())
    rows = list((await session.execute(query)).scalars().all())

    if not latest_only or status_filter:
        return rows

    latest: dict[str, BrandSectionDraft] = {}
    for row in rows:
        if row.status in ("rejected", "applied"):
            continue
        if row.status not in PENDING_DRAFT_STATUSES:
            continue
        if row.section_key not in latest:
            latest[row.section_key] = row
    return list(latest.values())


async def get_section_draft(
    session: AsyncSession, project_id: UUID, draft_id: UUID
) -> BrandSectionDraft:
    draft = (
        await session.execute(
            select(BrandSectionDraft).where(
                BrandSectionDraft.id == draft_id,
                BrandSectionDraft.project_id == project_id,
            )
        )
    ).scalar_one_or_none()
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft non trovato.")
    return draft


async def patch_section_draft(
    session: AsyncSession,
    project_id: UUID,
    draft_id: UUID,
    payload: BrandSectionDraftUpdate,
) -> BrandSectionDraft:
    draft = await get_section_draft(session, project_id, draft_id)
    data = payload.model_dump(exclude_unset=True)

    if "draft_payload" in data and data["draft_payload"] is not None:
        draft.draft_payload = validate_draft_payload(draft.section_key, data["draft_payload"])
    if payload.status is not None:
        draft.status = payload.status
        if payload.status == "approved":
            draft.approved_at = datetime.now(timezone.utc)
        if payload.status == "rejected":
            draft.approved_at = None
    if "warnings" in data:
        draft.warnings = data["warnings"]

    await session.commit()
    await session.refresh(draft)
    return draft


async def regenerate_section_draft(
    session: AsyncSession,
    project_id: UUID,
    draft_id: UUID,
    *,
    instructions: str | None = None,
    include_fact_ids: list[UUID] | None = None,
) -> BrandSectionDraft:
    draft = await get_section_draft(session, project_id, draft_id)
    if not draft.batch_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Draft senza batch.")
    result = await synthesize_section(
        session,
        project_id,
        draft.batch_id,
        draft.section_key,
        extra_instructions=instructions,
        include_fact_ids=include_fact_ids,
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dati insufficienti per rigenerare la sezione.",
        )
    return result


async def count_pending_section_drafts(session: AsyncSession, project_id: UUID) -> int:
    return int(
        (
            await session.execute(
                select(func.count())
                .select_from(BrandSectionDraft)
                .where(
                    BrandSectionDraft.project_id == project_id,
                    BrandSectionDraft.status.in_(tuple(PENDING_DRAFT_STATUSES)),
                )
            )
        ).scalar_one()
    )


async def get_latest_batch_id(session: AsyncSession, project_id: UUID) -> UUID | None:
    row = (
        await session.execute(
            select(BrandImportBatch.id)
            .where(BrandImportBatch.project_id == project_id)
            .order_by(BrandImportBatch.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    return row
