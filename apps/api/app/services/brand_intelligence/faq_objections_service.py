"""FAQ & Objections CRUD and completion helpers."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Literal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brand_intelligence import BrandFaqObjections
from app.schemas.brand_faq_objections import BrandFaqObjectionsProposal, BrandFaqObjectionsUpdate
from app.services.brand_intelligence.faq_objections_normalize import normalize_to_string_list

if TYPE_CHECKING:
    from app.schemas.brand_faq_objections import BrandFaqObjectionsRead

logger = logging.getLogger(__name__)

CompletionStatus = Literal["complete", "partial", "empty"]

_FAQ_FIELDS = (
    "general_faq",
    "product_process_questions",
    "purchase_shipping_questions",
)
_LIST_FIELDS = (
    "objections",
    "myths_misconceptions",
    "recommended_answers",
    "content_opportunities",
)
_STRING_LIST_FIELDS = (
    "general_faq",
    "product_process_questions",
    "purchase_shipping_questions",
    "objections",
    "myths_misconceptions",
    "recommended_answers",
    "content_opportunities",
    "social_comment_insights",
)


def has_text(value: object | None) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (dict, list)):
        return bool(normalize_to_string_list(value))
    return False


def _field_value_changed(current: object | None, normalized: list[str]) -> bool:
    if current is None:
        return bool(normalized)
    if not isinstance(current, list):
        return True
    if len(current) != len(normalized):
        return True
    for item, norm in zip(current, normalized, strict=False):
        if item != norm:
            return True
    return False


def normalize_faq_objections_row(row: BrandFaqObjections) -> bool:
    """Normalize all FAQ list fields in-place. Returns True if any field changed."""
    changed = False
    for field in _STRING_LIST_FIELDS:
        current = getattr(row, field)
        normalized = normalize_to_string_list(current)
        if _field_value_changed(current, normalized):
            setattr(row, field, normalized)
            changed = True
    return changed


def _has_string_list(value: object | None) -> bool:
    return bool(normalize_to_string_list(value))


def _any_faq_populated(row: BrandFaqObjections | "BrandFaqObjectionsRead" | None) -> bool:
    if not row:
        return False
    return any(
        _has_string_list(getattr(row, field, None)) for field in _FAQ_FIELDS
    )


def _any_content_populated(row: BrandFaqObjections | "BrandFaqObjectionsRead" | None) -> bool:
    if not row:
        return False
    if _any_faq_populated(row):
        return True
    if any(_has_string_list(getattr(row, field, None)) for field in _LIST_FIELDS):
        return True
    if _has_string_list(getattr(row, "social_comment_insights", None)):
        return True
    return has_text(getattr(row, "notes", None))


def faq_objections_has_content(row: BrandFaqObjections | "BrandFaqObjectionsRead" | None) -> bool:
    return _any_content_populated(row)


def faq_objections_missing_fields(
    row: BrandFaqObjections | "BrandFaqObjectionsRead" | None,
) -> list[str]:
    if not row:
        return ["general_faq", "objections", "recommended_answers"]
    missing: list[str] = []
    if not _any_faq_populated(row):
        missing.append("general_faq")
    if not _has_string_list(getattr(row, "objections", None)):
        missing.append("objections")
    if not _has_string_list(getattr(row, "recommended_answers", None)):
        missing.append("recommended_answers")
    return missing


def faq_objections_completion(
    row: BrandFaqObjections | "BrandFaqObjectionsRead" | None,
) -> CompletionStatus:
    if not row:
        return "empty"
    if (
        _any_faq_populated(row)
        and _has_string_list(getattr(row, "objections", None))
        and _has_string_list(getattr(row, "recommended_answers", None))
    ):
        return "complete"
    if _any_content_populated(row):
        return "partial"
    return "empty"


def faq_objections_missing_context(
    row: BrandFaqObjections | "BrandFaqObjectionsRead" | None,
) -> list[str]:
    if faq_objections_completion(row) == "empty":
        return [
            "FAQ & Objections non compilata: i moduli AI avranno meno contesto su dubbi e obiezioni clienti."
        ]
    return []


def _apply_string_field(row: BrandFaqObjections, attr: str, value: str | None) -> None:
    if has_text(value) and isinstance(value, str):
        setattr(row, attr, value.strip())


def _apply_string_list_field(row: BrandFaqObjections, attr: str, value: list[str] | None) -> None:
    if value is None:
        return
    setattr(row, attr, normalize_to_string_list(value))


def _merge_warnings(row: BrandFaqObjections, warnings: list[str]) -> None:
    if not warnings:
        return
    existing = list(row.warnings or [])
    for warning in warnings:
        if warning not in existing:
            existing.append(warning)
    row.warnings = existing
    for warning in warnings:
        logger.warning("FAQ & Objections normalization: %s", warning)


async def _get_or_create_faq_objections(
    session: AsyncSession, project_id: UUID
) -> BrandFaqObjections:
    row = (
        await session.execute(
            select(BrandFaqObjections).where(BrandFaqObjections.project_id == project_id)
        )
    ).scalar_one_or_none()
    if row is None:
        row = BrandFaqObjections(project_id=project_id)
        session.add(row)
        await session.commit()
        await session.refresh(row)
    return row


async def _repair_faq_objections_row_if_needed(
    session: AsyncSession, row: BrandFaqObjections
) -> BrandFaqObjections:
    if normalize_faq_objections_row(row):
        await session.commit()
        await session.refresh(row)
    return row


async def get_faq_objections(session: AsyncSession, project_id: UUID) -> BrandFaqObjections:
    row = await _get_or_create_faq_objections(session, project_id)
    return await _repair_faq_objections_row_if_needed(session, row)


async def upsert_faq_objections(
    session: AsyncSession,
    project_id: UUID,
    payload: BrandFaqObjectionsUpdate,
) -> BrandFaqObjections:
    row = await _get_or_create_faq_objections(session, project_id)
    data = payload.model_dump(exclude_unset=True)
    all_warnings: list[str] = []

    for key, value in data.items():
        if key in _STRING_LIST_FIELDS:
            field_warnings: list[str] = []
            normalized = normalize_to_string_list(value, field_warnings)
            setattr(row, key, normalized)
            all_warnings.extend(field_warnings)
        else:
            setattr(row, key, value)

    _merge_warnings(row, all_warnings)
    await session.commit()
    await session.refresh(row)
    return row


async def apply_faq_objections_proposal(
    session: AsyncSession,
    project_id: UUID,
    proposal: BrandFaqObjectionsProposal,
) -> BrandFaqObjections:
    row = await _get_or_create_faq_objections(session, project_id)

    _apply_string_field(row, "notes", proposal.notes)
    _apply_string_list_field(row, "general_faq", proposal.general_faq)
    _apply_string_list_field(row, "product_process_questions", proposal.product_process_questions)
    _apply_string_list_field(row, "purchase_shipping_questions", proposal.purchase_shipping_questions)
    _apply_string_list_field(row, "objections", proposal.objections)
    _apply_string_list_field(row, "myths_misconceptions", proposal.myths_misconceptions)
    _apply_string_list_field(row, "recommended_answers", proposal.recommended_answers)
    _apply_string_list_field(row, "content_opportunities", proposal.content_opportunities)
    _apply_string_list_field(row, "social_comment_insights", proposal.social_comment_insights)

    await session.commit()
    await session.refresh(row)
    return row
