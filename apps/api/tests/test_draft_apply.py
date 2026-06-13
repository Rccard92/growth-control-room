"""Draft apply enrich/conflict unit tests."""

import asyncio
from types import SimpleNamespace
from uuid import uuid4

from app.services.brand_intelligence.draft_apply import _apply_scalar_section
from app.schemas.brand_intelligence import BrandProfileUpdate


def test_scalar_enrich_empty_official() -> None:
    profile = SimpleNamespace(brand_name=None, short_description=None)
    updates_holder: list[dict] = []

    async def fake_upsert(session, project_id, schema):
        updates_holder.append(schema.model_dump(exclude_unset=True))

    result, conflicts = asyncio.run(
        _apply_scalar_section(
            None,  # type: ignore[arg-type]
            uuid4(),
            {"brand_name": "Acme", "short_description": "Desc"},
            profile,
            {"brand_name", "short_description"},
            upsert_fn=fake_upsert,
            schema=BrandProfileUpdate,
        )
    )
    assert not conflicts
    assert updates_holder[0]["brand_name"] == "Acme"


def test_scalar_conflict_when_official_differs() -> None:
    profile = SimpleNamespace(brand_name="Existing Brand")

    async def fake_upsert(session, project_id, schema):
        pass

    result, conflicts = asyncio.run(
        _apply_scalar_section(
            None,  # type: ignore[arg-type]
            uuid4(),
            {"brand_name": "New Brand"},
            profile,
            {"brand_name"},
            upsert_fn=fake_upsert,
            schema=BrandProfileUpdate,
        )
    )
    assert conflicts
    assert "brand_name" in conflicts[0]
