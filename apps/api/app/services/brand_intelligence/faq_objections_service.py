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


def _has_text(value: str | None) -> bool:
    return bool(value and value.strip())


def _has_list(value: list | None) -> bool:
    return bool(value and len(value) > 0)


def _has_string_list(value: list[str] | None) -> bool:
    if not value:
        return False
    return any(_has_text(item) for item in value)


def _any_faq_populated(row: BrandFaqObjections | "BrandFaqObjectionsRead" | None) -> bool:
    if not row:
        return False
    return any(_has_string_list(getattr(row, field)) for field in _FAQ_FIELDS)


def _any_content_populated(row: BrandFaqObjections | "BrandFaqObjectionsRead" | None) -> bool:
    if not row:
        return False
    if _any_faq_populated(row):
        return True
    if any(_has_list(getattr(row, field)) for field in _LIST_FIELDS):
        return True
    if _has_string_list(row.social_comment_insights):
        return True
    return _has_text(row.notes)


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
    if not _has_list(row.objections):
        missing.append("objections")
    if not _has_list(row.recommended_answers):
        missing.append("recommended_answers")
    return missing


def faq_objections_completion(
    row: BrandFaqObjections | "BrandFaqObjectionsRead" | None,
) -> CompletionStatus:
    if not row:
        return "empty"
    if (
        _any_faq_populated(row)
        and _has_list(row.objections)
        and _has_list(row.recommended_answers)
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
    if _has_text(value):
        setattr(row, attr, value.strip())


def _apply_string_list_field(row: BrandFaqObjections, attr: str, value: list[str] | None) -> None:
    if value is None:
        return
    normalized = normalize_to_string_list(value)
    if normalized:
        setattr(row, attr, normalized)


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


async def get_faq_objections(session: AsyncSession, project_id: UUID) -> BrandFaqObjections:
    return await _get_or_create_faq_objections(session, project_id)


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
