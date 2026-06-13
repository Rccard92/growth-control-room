"""BrandIntelligenceBriefRead handles nullable JSON/list DB columns."""

import uuid
from datetime import datetime, timezone

from app.models.brand_intelligence import BrandIntelligenceBrief
from app.schemas.brand_brief import BrandIntelligenceBriefRead, DEFAULT_BRIEF_PAYLOAD
from app.services.brand_intelligence.brief_service import build_brand_intelligence_brief_read


def _make_brief_row(**overrides) -> BrandIntelligenceBrief:
    now = datetime.now(timezone.utc)
    defaults = {
        "id": uuid.uuid4(),
        "project_id": uuid.uuid4(),
        "source_batch_id": None,
        "version": 1,
        "status": "draft",
        "title": "Test Brief",
        "brief_payload": None,
        "markdown_summary": None,
        "confidence": 0.8,
        "warnings": None,
        "source_document_ids": None,
        "source_external_ids": None,
        "source_fact_ids": None,
        "approved_at": None,
        "archived_at": None,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    return BrandIntelligenceBrief(**defaults)


def test_build_read_with_null_source_fact_ids() -> None:
    row = _make_brief_row()
    result = build_brand_intelligence_brief_read(row)
    assert result.source_fact_ids == []
    assert result.source_document_ids == []
    assert result.source_external_ids == []


def test_build_read_with_null_brief_payload() -> None:
    row = _make_brief_row(brief_payload=None)
    result = build_brand_intelligence_brief_read(row)
    assert result.brief_payload == DEFAULT_BRIEF_PAYLOAD


def test_build_read_with_null_warnings() -> None:
    row = _make_brief_row(warnings=None)
    result = build_brand_intelligence_brief_read(row)
    assert result.warnings is None


def test_schema_validate_row_with_null_lists() -> None:
    row = _make_brief_row()
    result = BrandIntelligenceBriefRead.model_validate(row)
    assert result.source_fact_ids == []


def test_schema_validate_dict_with_all_nulls() -> None:
    now = datetime.now(timezone.utc)
    result = BrandIntelligenceBriefRead.model_validate(
        {
            "id": uuid.uuid4(),
            "project_id": uuid.uuid4(),
            "source_batch_id": None,
            "version": 1,
            "status": "draft",
            "title": "T",
            "brief_payload": None,
            "markdown_summary": None,
            "confidence": None,
            "warnings": None,
            "source_document_ids": None,
            "source_external_ids": None,
            "source_fact_ids": None,
            "created_at": now,
            "updated_at": now,
            "approved_at": None,
            "archived_at": None,
        }
    )
    assert result.source_fact_ids == []
    assert result.brief_payload == DEFAULT_BRIEF_PAYLOAD
