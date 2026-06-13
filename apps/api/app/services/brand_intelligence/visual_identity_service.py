"""Brand Visual Identity CRUD, completion and apply-proposal."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brand_intelligence import BrandVisualIdentity
from app.schemas.brand_identity_visual import (
    BrandVisualIdentityUpdate,
    VisualExtractProposal,
)

CompletionStatus = Literal["complete", "partial", "empty"]


def _has_text(value: str | None) -> bool:
    return bool(value and value.strip())


def _has_list(value: list | None) -> bool:
    return bool(value and len(value) > 0)


def visual_has_minimum(visual: BrandVisualIdentity | None) -> bool:
    if not visual:
        return False
    return bool(
        _has_text(visual.primary_logo_url)
        or _has_text(visual.primary_color)
        or _has_list(visual.color_palette)
    )


def visual_missing_fields(visual: BrandVisualIdentity | None) -> list[str]:
    if not visual:
        return ["primary_logo_url", "primary_color"]
    missing: list[str] = []
    if not _has_text(visual.primary_logo_url):
        missing.append("primary_logo_url")
    if not _has_text(visual.primary_color):
        missing.append("primary_color")
    if not _has_text(visual.secondary_color):
        missing.append("secondary_color")
    if not _has_list(visual.color_palette) and not _has_text(visual.accent_color):
        missing.append("color_palette")
    return missing


def visual_completion(visual: BrandVisualIdentity | None) -> CompletionStatus:
    if not visual or not visual_has_minimum(visual):
        return "empty"
    missing = visual_missing_fields(visual)
    if not missing:
        return "complete"
    return "partial"


async def _get_or_create_visual(session: AsyncSession, project_id: UUID) -> BrandVisualIdentity:
    row = (
        await session.execute(
            select(BrandVisualIdentity).where(BrandVisualIdentity.project_id == project_id)
        )
    ).scalar_one_or_none()
    if row is None:
        row = BrandVisualIdentity(project_id=project_id)
        session.add(row)
        await session.commit()
        await session.refresh(row)
    return row


async def get_visual_identity(session: AsyncSession, project_id: UUID) -> BrandVisualIdentity:
    return await _get_or_create_visual(session, project_id)


async def upsert_visual_identity(
    session: AsyncSession,
    project_id: UUID,
    payload: BrandVisualIdentityUpdate,
) -> BrandVisualIdentity:
    row = await _get_or_create_visual(session, project_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    await session.commit()
    await session.refresh(row)
    return row


def _palette_to_dicts(palette: list) -> list[dict]:
    out: list[dict] = []
    for item in palette:
        if hasattr(item, "model_dump"):
            out.append(item.model_dump(by_alias=True))
        elif isinstance(item, dict):
            out.append(item)
    return out


async def apply_visual_proposal(
    session: AsyncSession,
    project_id: UUID,
    proposal: VisualExtractProposal,
) -> BrandVisualIdentity:
    row = await _get_or_create_visual(session, project_id)

    if proposal.primary_logo_url:
        row.primary_logo_url = proposal.primary_logo_url
    if proposal.favicon_url:
        row.favicon_url = proposal.favicon_url
    if proposal.visual_style_notes:
        row.visual_style_notes = proposal.visual_style_notes

    palette = _palette_to_dicts(proposal.color_palette or [])
    if palette:
        row.color_palette = palette
        row.website_extracted_palette = palette
        for swatch in palette:
            role = (swatch.get("role") or "").lower()
            hex_val = swatch.get("hex")
            if not hex_val:
                continue
            if role == "primary" and not row.primary_color:
                row.primary_color = hex_val
            elif role == "secondary" and not row.secondary_color:
                row.secondary_color = hex_val
            elif role == "accent" and not row.accent_color:
                row.accent_color = hex_val
            elif role == "background" and not row.background_color:
                row.background_color = hex_val
            elif role == "text" and not row.text_color:
                row.text_color = hex_val
        if not row.primary_color and palette:
            row.primary_color = palette[0].get("hex")

    if proposal.fonts:
        row.fonts = [
            f.model_dump(by_alias=True) if hasattr(f, "model_dump") else f for f in proposal.fonts
        ]

    await session.commit()
    await session.refresh(row)
    return row
