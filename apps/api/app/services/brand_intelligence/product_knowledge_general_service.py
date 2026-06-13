"""Product Knowledge general CRUD and completion helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brand_intelligence import BrandProductKnowledgeGeneral
from app.schemas.brand_product_knowledge import (
    BrandProductKnowledgeGeneralProposal,
    BrandProductKnowledgeGeneralUpdate,
)

if TYPE_CHECKING:
    from app.schemas.brand_product_knowledge import BrandProductKnowledgeGeneralRead

CompletionStatus = Literal["complete", "partial", "empty"]

_LIST_FIELDS = (
    "general_principles",
    "common_strengths",
    "common_quality_rules",
    "common_production_notes",
    "common_usage_notes",
    "common_objections",
    "communication_rules",
    "product_storytelling_rules",
)


def _has_text(value: str | None) -> bool:
    return bool(value and value.strip())


def _has_list(value: list | None) -> bool:
    return bool(value and len(value) > 0)


def _has_faq(value: list | None) -> bool:
    return bool(value and len(value) > 0)


def general_has_content(row: BrandProductKnowledgeGeneral | "BrandProductKnowledgeGeneralRead" | None) -> bool:
    if not row:
        return False
    if _has_text(row.notes):
        return True
    if _has_faq(row.common_faq):
        return True
    return any(_has_list(getattr(row, field)) for field in _LIST_FIELDS)


def general_missing_fields(
    row: BrandProductKnowledgeGeneral | "BrandProductKnowledgeGeneralRead" | None,
) -> list[str]:
    if not general_has_content(row):
        return ["general_knowledge"]
    return []


def general_completion(
    row: BrandProductKnowledgeGeneral | "BrandProductKnowledgeGeneralRead" | None,
) -> CompletionStatus:
    if not row or not general_has_content(row):
        return "empty"
    populated = sum(
        1
        for field in _LIST_FIELDS
        if _has_list(getattr(row, field))
    )
    if _has_faq(row.common_faq):
        populated += 1
    if _has_text(row.notes):
        populated += 1
    if populated >= 3:
        return "complete"
    return "partial"


def _apply_string_field(row: BrandProductKnowledgeGeneral, attr: str, value: str | None) -> None:
    if _has_text(value):
        setattr(row, attr, value.strip())


def _apply_list_field(row: BrandProductKnowledgeGeneral, attr: str, value: list | None) -> None:
    if _has_list(value):
        setattr(row, attr, value)


def _apply_faq_field(row: BrandProductKnowledgeGeneral, value: list | None) -> None:
    if _has_faq(value):
        setattr(row, "common_faq", value)


async def _get_or_create_general(
    session: AsyncSession, project_id: UUID
) -> BrandProductKnowledgeGeneral:
    row = (
        await session.execute(
            select(BrandProductKnowledgeGeneral).where(
                BrandProductKnowledgeGeneral.project_id == project_id
            )
        )
    ).scalar_one_or_none()
    if row is None:
        row = BrandProductKnowledgeGeneral(project_id=project_id)
        session.add(row)
        await session.commit()
        await session.refresh(row)
    return row


async def get_general(session: AsyncSession, project_id: UUID) -> BrandProductKnowledgeGeneral:
    return await _get_or_create_general(session, project_id)


async def upsert_general(
    session: AsyncSession,
    project_id: UUID,
    payload: BrandProductKnowledgeGeneralUpdate,
) -> BrandProductKnowledgeGeneral:
    row = await _get_or_create_general(session, project_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    await session.commit()
    await session.refresh(row)
    return row


async def apply_general_proposal(
    session: AsyncSession,
    project_id: UUID,
    proposal: BrandProductKnowledgeGeneralProposal,
) -> BrandProductKnowledgeGeneral:
    row = await _get_or_create_general(session, project_id)

    _apply_string_field(row, "notes", proposal.notes)
    _apply_list_field(row, "general_principles", proposal.general_principles)
    _apply_list_field(row, "common_strengths", proposal.common_strengths)
    _apply_list_field(row, "common_quality_rules", proposal.common_quality_rules)
    _apply_list_field(row, "common_production_notes", proposal.common_production_notes)
    _apply_list_field(row, "common_usage_notes", proposal.common_usage_notes)
    _apply_list_field(row, "common_objections", proposal.common_objections)
    _apply_faq_field(row, proposal.common_faq)
    _apply_list_field(row, "communication_rules", proposal.communication_rules)
    _apply_list_field(row, "product_storytelling_rules", proposal.product_storytelling_rules)

    await session.commit()
    await session.refresh(row)
    return row
