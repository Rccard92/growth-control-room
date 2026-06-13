"""Brand Visual Identity CRUD, completion and apply-proposal."""

from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brand_intelligence import BrandVisualIdentity
from app.schemas.brand_identity_visual import (
    BrandVisualIdentityUpdate,
    VisualExtractProposal,
)

CompletionStatus = Literal["complete", "partial", "empty"]

_ROLE_COLOR_FIELDS = {
    "primary": "primary_color",
    "secondary": "secondary_color",
    "accent": "accent_color",
    "background": "background_color",
    "text": "text_color",
}


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


def _palette_to_dicts(palette: list) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in palette:
        if hasattr(item, "model_dump"):
            out.append(item.model_dump())
        elif isinstance(item, dict):
            out.append(item)
    return out


def _fonts_to_dicts(fonts: list) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in fonts:
        if hasattr(item, "model_dump"):
            out.append(item.model_dump())
        elif isinstance(item, dict):
            out.append(item)
    return out


def _apply_palette_roles(row: BrandVisualIdentity, palette: list[dict[str, Any]]) -> None:
    for swatch in palette:
        role = (swatch.get("role") or "").lower()
        hex_val = swatch.get("hex")
        if not hex_val:
            continue
        field = _ROLE_COLOR_FIELDS.get(role)
        if field:
            setattr(row, field, hex_val)
    if palette and not row.primary_color:
        row.primary_color = palette[0].get("hex")


def _apply_string_field(row: BrandVisualIdentity, attr: str, value: str | None) -> None:
    if _has_text(value):
        setattr(row, attr, value.strip())


def _apply_list_field(row: BrandVisualIdentity, attr: str, value: list | None) -> None:
    if _has_list(value):
        setattr(row, attr, value)


async def apply_visual_proposal(
    session: AsyncSession,
    project_id: UUID,
    proposal: VisualExtractProposal,
) -> BrandVisualIdentity:
    row = await _get_or_create_visual(session, project_id)

    _apply_string_field(row, "primary_logo_url", proposal.primary_logo_url)
    _apply_string_field(row, "secondary_logo_url", proposal.secondary_logo_url)
    _apply_string_field(row, "favicon_url", proposal.favicon_url)
    _apply_string_field(row, "primary_color", proposal.primary_color)
    _apply_string_field(row, "secondary_color", proposal.secondary_color)
    _apply_string_field(row, "accent_color", proposal.accent_color)
    _apply_string_field(row, "background_color", proposal.background_color)
    _apply_string_field(row, "text_color", proposal.text_color)
    _apply_string_field(row, "visual_style_notes", proposal.visual_style_notes)
    _apply_string_field(row, "image_style_notes", proposal.image_style_notes)

    palette = _palette_to_dicts(proposal.color_palette or [])
    if palette:
        row.color_palette = palette
        row.website_extracted_palette = palette
        _apply_palette_roles(row, palette)
    elif proposal.website_extracted_palette:
        extracted = _palette_to_dicts(proposal.website_extracted_palette)
        if extracted:
            row.website_extracted_palette = extracted

    if proposal.fonts:
        fonts = _fonts_to_dicts(proposal.fonts)
        if fonts:
            row.fonts = fonts

    _apply_list_field(row, "do_show", proposal.do_show)
    _apply_list_field(row, "do_not_show", proposal.do_not_show)

    await session.commit()
    await session.refresh(row)
    return row
