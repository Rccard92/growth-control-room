"""Safe Claims CRUD and completion helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brand_intelligence import BrandSafeClaims
from app.schemas.brand_safe_claims import BrandSafeClaimsProposal, BrandSafeClaimsUpdate

if TYPE_CHECKING:
    from app.schemas.brand_safe_claims import BrandSafeClaimsRead

CompletionStatus = Literal["complete", "partial", "empty"]

_LIST_FIELDS = (
    "allowed_claims",
    "forbidden_claims",
    "caution_claims",
    "disclaimers",
    "health_claim_rules",
    "competitor_rules",
    "process_secrets",
    "tone_red_flags",
)


def _has_text(value: str | None) -> bool:
    return bool(value and value.strip())


def _has_list(value: list | None) -> bool:
    return bool(value and len(value) > 0)


def _any_list_populated(row: BrandSafeClaims | None) -> bool:
    if not row:
        return False
    return any(_has_list(getattr(row, field)) for field in _LIST_FIELDS)


def safe_claims_has_minimum(row: BrandSafeClaims | "BrandSafeClaimsRead" | None) -> bool:
    if not row:
        return False
    return _has_list(row.allowed_claims) and _has_list(row.forbidden_claims)


def safe_claims_missing_fields(row: BrandSafeClaims | "BrandSafeClaimsRead" | None) -> list[str]:
    if not row:
        return ["allowed_claims", "forbidden_claims"]
    missing: list[str] = []
    if not _has_list(row.allowed_claims):
        missing.append("allowed_claims")
    if not _has_list(row.forbidden_claims):
        missing.append("forbidden_claims")
    if not _has_list(row.caution_claims) and not _has_list(row.disclaimers):
        missing.append("caution_claims_or_disclaimers")
    return missing


def safe_claims_completion(row: BrandSafeClaims | "BrandSafeClaimsRead" | None) -> CompletionStatus:
    if not row:
        return "empty"
    if (
        _has_list(row.allowed_claims)
        and _has_list(row.forbidden_claims)
        and (_has_list(row.caution_claims) or _has_list(row.disclaimers))
    ):
        return "complete"
    if _any_list_populated(row) or _has_text(row.notes):
        return "partial"
    return "empty"


def _apply_string_field(row: BrandSafeClaims, attr: str, value: str | None) -> None:
    if _has_text(value):
        setattr(row, attr, value.strip())


def _apply_list_field(row: BrandSafeClaims, attr: str, value: list | None) -> None:
    if _has_list(value):
        setattr(row, attr, value)


async def _get_or_create_safe_claims(session: AsyncSession, project_id: UUID) -> BrandSafeClaims:
    row = (
        await session.execute(
            select(BrandSafeClaims).where(BrandSafeClaims.project_id == project_id)
        )
    ).scalar_one_or_none()
    if row is None:
        row = BrandSafeClaims(project_id=project_id)
        session.add(row)
        await session.commit()
        await session.refresh(row)
    return row


async def get_safe_claims(session: AsyncSession, project_id: UUID) -> BrandSafeClaims:
    return await _get_or_create_safe_claims(session, project_id)


async def upsert_safe_claims(
    session: AsyncSession,
    project_id: UUID,
    payload: BrandSafeClaimsUpdate,
) -> BrandSafeClaims:
    row = await _get_or_create_safe_claims(session, project_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    await session.commit()
    await session.refresh(row)
    return row


async def apply_safe_claims_proposal(
    session: AsyncSession,
    project_id: UUID,
    proposal: BrandSafeClaimsProposal,
) -> BrandSafeClaims:
    row = await _get_or_create_safe_claims(session, project_id)

    _apply_string_field(row, "notes", proposal.notes)
    _apply_list_field(row, "allowed_claims", proposal.allowed_claims)
    _apply_list_field(row, "forbidden_claims", proposal.forbidden_claims)
    _apply_list_field(row, "caution_claims", proposal.caution_claims)
    _apply_list_field(row, "disclaimers", proposal.disclaimers)
    _apply_list_field(row, "health_claim_rules", proposal.health_claim_rules)
    _apply_list_field(row, "competitor_rules", proposal.competitor_rules)
    _apply_list_field(row, "process_secrets", proposal.process_secrets)
    _apply_list_field(row, "tone_red_flags", proposal.tone_red_flags)

    await session.commit()
    await session.refresh(row)
    return row
