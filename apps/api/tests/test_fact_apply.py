"""Fact apply mapping unit tests."""

import asyncio
from types import SimpleNamespace
from uuid import uuid4

from app.services.brand_intelligence.fact_apply import _apply_single_fact


def test_apply_profile_field_collects_updates() -> None:
    profile_updates: dict = {}
    voice_updates: dict = {}
    seo_updates: dict = {}
    seo_append: list[str] = []

    fact = SimpleNamespace(
        id=uuid4(),
        target_section="brand_profile",
        field_name="brand_name",
        extracted_value="Acme Foods",
        status="approved",
    )

    class FakeSession:
        pass

    result = asyncio.run(
        _apply_single_fact(
            FakeSession(),  # type: ignore[arg-type]
            uuid4(),
            fact,  # type: ignore[arg-type]
            profile_updates,
            voice_updates,
            seo_updates,
            seo_append,
        )
    )
    assert result is not None
    assert profile_updates["brand_name"] == "Acme Foods"


def test_apply_unknown_section_returns_none() -> None:
    fact = SimpleNamespace(
        id=uuid4(),
        target_section="unknown",
        field_name=None,
        extracted_value="something",
        status="approved",
    )
    result = asyncio.run(
        _apply_single_fact(
            None,  # type: ignore[arg-type]
            uuid4(),
            fact,  # type: ignore[arg-type]
            {},
            {},
            {},
            [],
        )
    )
    assert result is None
