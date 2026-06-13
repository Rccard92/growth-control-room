"""Conflict detection unit tests."""

import uuid

from app.models.brand_intelligence import BrandExtractedFact, BrandProductKnowledge, BrandProfile
from app.services.brand_intelligence.conflict_detection import (
    OfficialSnapshot,
    build_bi_summary,
    classify_fact_against_official,
)


def _fact(**kwargs) -> BrandExtractedFact:
    defaults = {
        "project_id": uuid.uuid4(),
        "target_section": "brand_profile",
        "field_name": "brand_name",
        "extracted_value": "Acme",
        "confidence": 0.9,
        "status": "suggested",
    }
    defaults.update(kwargs)
    return BrandExtractedFact(**defaults)


def test_classify_create_when_no_official_data() -> None:
    fact = _fact(target_section="product_knowledge", field_name="name", extracted_value="Widget")
    snapshot = OfficialSnapshot()
    classify_fact_against_official(fact, snapshot)
    assert fact.update_mode == "create"
    assert fact.conflict_status == "none"


def test_classify_enrich_when_official_field_empty() -> None:
    profile = BrandProfile(project_id=uuid.uuid4())
    profile.brand_name = None
    fact = _fact(field_name="brand_name", extracted_value="Nuovo Brand")
    snapshot = OfficialSnapshot(profile=profile)
    classify_fact_against_official(fact, snapshot)
    assert fact.update_mode == "enrich"
    assert fact.is_update_suggestion is True
    assert fact.status == "needs_review"


def test_classify_update_conflict_when_values_differ() -> None:
    profile = BrandProfile(project_id=uuid.uuid4())
    profile.brand_name = "Vecchio Brand"
    fact = _fact(field_name="brand_name", extracted_value="Nuovo Brand")
    snapshot = OfficialSnapshot(profile=profile)
    classify_fact_against_official(fact, snapshot)
    assert fact.update_mode == "update"
    assert fact.conflict_status == "possible_conflict"
    assert fact.previous_value == "Vecchio Brand"
    assert fact.status == "needs_review"


def test_classify_duplicate_candidate_same_value() -> None:
    profile = BrandProfile(project_id=uuid.uuid4())
    profile.brand_name = "Acme"
    fact = _fact(field_name="brand_name", extracted_value="Acme")
    snapshot = OfficialSnapshot(profile=profile)
    classify_fact_against_official(fact, snapshot)
    assert fact.update_mode == "duplicate_candidate"
    assert fact.previous_value == "Acme"


def test_classify_duplicate_product_by_name() -> None:
    product = BrandProductKnowledge(
        project_id=uuid.uuid4(),
        name="Widget Pro",
        description="Desc",
        entity_type="product",
    )
    product.id = uuid.uuid4()
    fact = _fact(
        target_section="product_knowledge",
        field_name="name",
        extracted_value={"name": "Widget Pro"},
    )
    snapshot = OfficialSnapshot(products=[product])
    classify_fact_against_official(fact, snapshot)
    assert fact.update_mode == "duplicate_candidate"
    assert fact.existing_target_id == product.id


def test_build_bi_summary_with_profile() -> None:
    profile = BrandProfile(project_id=uuid.uuid4())
    profile.brand_name = "TestCo"
    profile.short_description = "A great brand"
    summary = build_bi_summary(OfficialSnapshot(profile=profile))
    assert "TestCo" in summary
    assert "A great brand" in summary
