"""Brand Identity CRUD and completion helpers."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brand_intelligence import BrandIdentity
from app.schemas.brand_identity_visual import BrandIdentityUpdate

CompletionStatus = Literal["complete", "partial", "empty"]


def _has_text(value: str | None) -> bool:
    return bool(value and value.strip())


def _has_list(value: list | None) -> bool:
    return bool(value and len(value) > 0)


def identity_has_minimum(identity: BrandIdentity | None) -> bool:
    if not identity:
        return False
    return _has_text(identity.positioning) or _has_list(identity.brand_values)


def identity_missing_fields(identity: BrandIdentity | None) -> list[str]:
    if not identity:
        return ["positioning", "brand_values"]
    missing: list[str] = []
    if not _has_text(identity.positioning):
        missing.append("positioning")
    if not _has_list(identity.brand_values):
        missing.append("brand_values")
    if not _has_list(identity.differentiators):
        missing.append("differentiators")
    if not _has_text(identity.what_brand_is):
        missing.append("what_brand_is")
    if not _has_text(identity.what_brand_is_not):
        missing.append("what_brand_is_not")
    return missing


def identity_completion(identity: BrandIdentity | None) -> CompletionStatus:
    if not identity or not identity_has_minimum(identity):
        return "empty"
    missing = identity_missing_fields(identity)
    core = {"positioning", "brand_values", "differentiators", "what_brand_is", "what_brand_is_not"}
    if not any(m in missing for m in core):
        return "complete"
    if identity_has_minimum(identity):
        return "partial"
    return "empty"


async def _get_or_create_identity(session: AsyncSession, project_id: UUID) -> BrandIdentity:
    row = (
        await session.execute(select(BrandIdentity).where(BrandIdentity.project_id == project_id))
    ).scalar_one_or_none()
    if row is None:
        row = BrandIdentity(project_id=project_id)
        session.add(row)
        await session.commit()
        await session.refresh(row)
    return row


async def get_identity(session: AsyncSession, project_id: UUID) -> BrandIdentity:
    return await _get_or_create_identity(session, project_id)


async def upsert_identity(
    session: AsyncSession,
    project_id: UUID,
    payload: BrandIdentityUpdate,
) -> BrandIdentity:
    row = await _get_or_create_identity(session, project_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    await session.commit()
    await session.refresh(row)
    return row
