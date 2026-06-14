"""Editorial Guidelines CRUD and completion helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brand_intelligence import BrandEditorialGuidelines
from app.schemas.brand_editorial_guidelines import (
    BrandEditorialGuidelinesUpdate,
    BrandPersonEntry,
)

if TYPE_CHECKING:
    from app.schemas.brand_editorial_guidelines import BrandEditorialGuidelinesRead

CompletionStatus = Literal["complete", "partial", "empty"]

DEFAULT_BRAND_PEOPLE: list[dict[str, str]] = [
    {
        "name": "Davide",
        "role": "coordinatore della produzione",
        "whenToUse": "",
        "tone": "",
    },
    {
        "name": "Filippo Leonardi",
        "role": "titolare e apicoltore dell'azienda",
        "whenToUse": "",
        "tone": "",
    },
    {
        "name": "Salvo Leonardi",
        "role": "figlio di Filippo Leonardi",
        "whenToUse": "",
        "tone": "",
    },
]

_LIST_FIELDS = (
    "storytelling_rules",
    "author_voice_rules",
    "community_cta_rules",
    "article_dos",
    "article_donts",
)

_TEXT_FIELDS = (
    "content_philosophy",
    "article_length_policy",
    "reading_style",
)


def _has_text(value: str | None) -> bool:
    return bool(value and value.strip())


def _has_list(value: list | None) -> bool:
    return bool(value and len(value) > 0)


def _has_brand_people(value: list | None) -> bool:
    if not value:
        return False
    for person in value:
        if isinstance(person, dict):
            if str(person.get("name") or "").strip():
                return True
        elif getattr(person, "name", ""):
            return True
    return False


def editorial_guidelines_has_content(
    row: BrandEditorialGuidelines | "BrandEditorialGuidelinesRead" | None,
) -> bool:
    if not row:
        return False
    if any(_has_text(getattr(row, field, None)) for field in _TEXT_FIELDS):
        return True
    if any(_has_list(getattr(row, field, None)) for field in _LIST_FIELDS):
        return True
    if _has_brand_people(getattr(row, "brand_people", None)):
        return True
    return bool(getattr(row, "default_article_length", None))


def editorial_guidelines_missing_fields(
    row: BrandEditorialGuidelines | "BrandEditorialGuidelinesRead" | None,
) -> list[str]:
    if not row:
        return ["content_philosophy", "reading_style", "default_article_length"]
    missing: list[str] = []
    if not _has_text(row.content_philosophy):
        missing.append("content_philosophy")
    if not _has_text(row.reading_style):
        missing.append("reading_style")
    if not row.default_article_length:
        missing.append("default_article_length")
    if not _has_brand_people(row.brand_people):
        missing.append("brand_people")
    return missing


def editorial_guidelines_completion(
    row: BrandEditorialGuidelines | "BrandEditorialGuidelinesRead" | None,
) -> CompletionStatus:
    if not row:
        return "empty"
    has_core = (
        _has_text(row.content_philosophy)
        and _has_text(row.reading_style)
        and bool(row.default_article_length)
        and _has_brand_people(row.brand_people)
    )
    if has_core and (_has_list(row.community_cta_rules) or _has_list(row.article_dos)):
        return "complete"
    if editorial_guidelines_has_content(row):
        return "partial"
    return "empty"


def editorial_guidelines_missing_context(
    row: BrandEditorialGuidelines | "BrandEditorialGuidelinesRead" | None,
) -> list[str]:
    if editorial_guidelines_completion(row) == "empty":
        return ["Editorial Guidelines non compilate: articoli potrebbero essere troppo SEO-oriented."]
    return []


async def _get_or_create_editorial_guidelines(
    session: AsyncSession,
    project_id: UUID,
) -> BrandEditorialGuidelines:
    row = (
        await session.execute(
            select(BrandEditorialGuidelines).where(
                BrandEditorialGuidelines.project_id == project_id
            )
        )
    ).scalar_one_or_none()
    if row is None:
        row = BrandEditorialGuidelines(
            project_id=project_id,
            brand_people=DEFAULT_BRAND_PEOPLE,
            default_article_length="medio",
        )
        session.add(row)
        await session.commit()
        await session.refresh(row)
    elif not row.brand_people:
        row.brand_people = DEFAULT_BRAND_PEOPLE
        await session.commit()
        await session.refresh(row)
    return row


async def get_editorial_guidelines(
    session: AsyncSession,
    project_id: UUID,
) -> BrandEditorialGuidelines:
    return await _get_or_create_editorial_guidelines(session, project_id)


async def upsert_editorial_guidelines(
    session: AsyncSession,
    project_id: UUID,
    payload: BrandEditorialGuidelinesUpdate,
) -> BrandEditorialGuidelines:
    row = await _get_or_create_editorial_guidelines(session, project_id)
    data = payload.model_dump(exclude_unset=True)
    if "brand_people" in data and data["brand_people"] is not None:
        data["brand_people"] = [
            p.model_dump(by_alias=True) if isinstance(p, BrandPersonEntry) else p
            for p in data["brand_people"]
        ]
    for key, value in data.items():
        setattr(row, key, value)
    await session.commit()
    await session.refresh(row)
    return row
