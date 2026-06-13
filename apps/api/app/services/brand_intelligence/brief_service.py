"""CRUD and lifecycle for BrandIntelligenceBrief."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brand_intelligence import BrandIntelligenceBrief
from app.schemas.brand_brief import (
    BrandIntelligenceBriefUpdate,
    build_markdown_summary,
    sanitize_brief_payload,
)

PENDING_BRIEF_STATUSES = frozenset({"draft"})


async def list_briefs(
    session: AsyncSession,
    project_id: UUID,
) -> list[BrandIntelligenceBrief]:
    rows = list(
        (
            await session.execute(
                select(BrandIntelligenceBrief)
                .where(BrandIntelligenceBrief.project_id == project_id)
                .order_by(BrandIntelligenceBrief.created_at.desc())
            )
        ).scalars().all()
    )
    return rows


async def get_brief(
    session: AsyncSession,
    project_id: UUID,
    brief_id: UUID,
) -> BrandIntelligenceBrief:
    brief = (
        await session.execute(
            select(BrandIntelligenceBrief).where(
                BrandIntelligenceBrief.id == brief_id,
                BrandIntelligenceBrief.project_id == project_id,
            )
        )
    ).scalar_one_or_none()
    if not brief:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brief non trovato.")
    return brief


async def get_approved_brief(
    session: AsyncSession,
    project_id: UUID,
) -> BrandIntelligenceBrief | None:
    return (
        await session.execute(
            select(BrandIntelligenceBrief)
            .where(
                BrandIntelligenceBrief.project_id == project_id,
                BrandIntelligenceBrief.status == "approved",
            )
            .order_by(BrandIntelligenceBrief.approved_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()


async def count_pending_briefs(session: AsyncSession, project_id: UUID) -> int:
    return int(
        (
            await session.execute(
                select(func.count())
                .select_from(BrandIntelligenceBrief)
                .where(
                    BrandIntelligenceBrief.project_id == project_id,
                    BrandIntelligenceBrief.status.in_(tuple(PENDING_BRIEF_STATUSES)),
                )
            )
        ).scalar_one()
    )


async def patch_brief(
    session: AsyncSession,
    project_id: UUID,
    brief_id: UUID,
    payload: BrandIntelligenceBriefUpdate,
) -> BrandIntelligenceBrief:
    brief = await get_brief(session, project_id, brief_id)
    data = payload.model_dump(exclude_unset=True)

    if payload.title is not None:
        brief.title = payload.title.strip() or brief.title

    if "brief_payload" in data and data["brief_payload"] is not None:
        sanitized, warnings = sanitize_brief_payload(data["brief_payload"])
        brief.brief_payload = sanitized
        if warnings:
            existing = (brief.warnings or {}).get("messages", []) if isinstance(brief.warnings, dict) else []
            brief.warnings = {"messages": list(existing) + warnings}
        if payload.markdown_summary is None:
            brief.markdown_summary = build_markdown_summary(sanitized)

    if payload.markdown_summary is not None:
        brief.markdown_summary = payload.markdown_summary

    if "warnings" in data:
        brief.warnings = data["warnings"]

    if payload.status is not None:
        brief.status = payload.status

    await session.commit()
    await session.refresh(brief)
    return brief


async def approve_brief(
    session: AsyncSession,
    project_id: UUID,
    brief_id: UUID,
) -> BrandIntelligenceBrief:
    brief = await get_brief(session, project_id, brief_id)
    if brief.status == "approved":
        return brief

    now = datetime.now(timezone.utc)
    previous = list(
        (
            await session.execute(
                select(BrandIntelligenceBrief).where(
                    BrandIntelligenceBrief.project_id == project_id,
                    BrandIntelligenceBrief.status == "approved",
                    BrandIntelligenceBrief.id != brief_id,
                )
            )
        ).scalars().all()
    )
    for old in previous:
        old.status = "archived"
        old.archived_at = now

    brief.status = "approved"
    brief.approved_at = now
    brief.archived_at = None
    await session.commit()
    await session.refresh(brief)
    return brief


async def archive_brief(
    session: AsyncSession,
    project_id: UUID,
    brief_id: UUID,
) -> BrandIntelligenceBrief:
    brief = await get_brief(session, project_id, brief_id)
    now = datetime.now(timezone.utc)
    brief.status = "archived"
    brief.archived_at = now
    await session.commit()
    await session.refresh(brief)
    return brief
