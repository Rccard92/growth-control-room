"""External sources service unit tests."""

import pytest
from fastapi import HTTPException

from app.schemas.brand_intelligence import BrandExternalSourceInput
from app.services.brand_intelligence.external_sources_service import (
    build_sources_from_form,
    normalize_url,
    parse_sources_json,
    validate_batch_input,
)


def test_normalize_url_adds_https() -> None:
    assert normalize_url("example.com").startswith("https://")


def test_normalize_url_rejects_invalid() -> None:
    with pytest.raises(HTTPException):
        normalize_url("   ")


def test_build_sources_from_form_dedupes() -> None:
    sources = build_sources_from_form(
        website_url="https://acme.com",
        sources=[
            BrandExternalSourceInput(source_type="instagram", url="https://instagram.com/acme"),
            BrandExternalSourceInput(source_type="instagram", url="https://instagram.com/acme/"),
        ],
    )
    types = [s.source_type for s in sources]
    assert "website" in types
    assert types.count("instagram") == 1


def test_validate_batch_input_requires_something() -> None:
    with pytest.raises(HTTPException):
        validate_batch_input(brand_name=None, website_url=None, files_count=0, sources_count=0)


def test_validate_batch_input_accepts_brand_name() -> None:
    validate_batch_input(brand_name="Acme", website_url=None, files_count=0, sources_count=0)


def test_parse_sources_json() -> None:
    raw = '[{"sourceType": "trustpilot", "url": "https://trustpilot.com/review/acme"}]'
    items = parse_sources_json(raw)
    assert len(items) == 1
    assert items[0].source_type == "trustpilot"
