"""Upsert batch sources helper tests."""

import uuid

from app.models.brand_intelligence import BrandExternalSource
from app.schemas.brand_intelligence import BrandExternalSourceInput
from app.services.brand_intelligence.external_sources_service import (
    REMOVED_BY_USER_MSG,
    _dedupe_key,
    _mark_source_skipped,
    _reset_source_for_refetch,
    build_sources_from_form,
)


def test_dedupe_key_normalizes_trailing_slash() -> None:
    a = _dedupe_key("instagram", "https://instagram.com/acme")
    b = _dedupe_key("instagram", "https://instagram.com/acme/")
    assert a == b


def test_build_sources_from_form_includes_website_and_social() -> None:
    sources = build_sources_from_form(
        website_url="https://acme.com",
        sources=[
            BrandExternalSourceInput(source_type="instagram", url="https://instagram.com/acme"),
        ],
    )
    types = {s.source_type for s in sources}
    assert types == {"website", "instagram"}


def test_reset_source_for_refetch_clears_fetched_fields() -> None:
    row = BrandExternalSource(
        project_id=uuid.uuid4(),
        source_type="website",
        url="https://acme.com",
        status="fetched",
        fetched_title="Old",
        fetched_text="Body",
        fetched_summary="Sum",
        fetch_error="err",
    )
    _reset_source_for_refetch(row)
    assert row.status == "pending"
    assert row.fetched_title is None
    assert row.fetched_text is None
    assert row.fetched_summary is None
    assert row.fetch_error is None
    assert row.last_fetched_at is None


def test_mark_source_skipped_sets_message() -> None:
    row = BrandExternalSource(
        project_id=uuid.uuid4(),
        source_type="instagram",
        url="https://instagram.com/acme",
        status="pending",
    )
    _mark_source_skipped(row)
    assert row.status == "skipped"
    assert row.fetch_error == REMOVED_BY_USER_MSG
