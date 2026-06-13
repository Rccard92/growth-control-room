"""BrandContextBuilder brief priority tests."""

from uuid import uuid4

from app.schemas.brand_intelligence import BrandContextBundleResponse, BrandKnowledgeScoreResponse
from app.services.brand_intelligence.context import BrandIntelligenceContextBuilder


def _minimal_score() -> BrandKnowledgeScoreResponse:
    return BrandKnowledgeScoreResponse.model_validate(
        {
            "overall_score": 5,
            "status": "incomplete",
            "section_scores": {},
            "missing_required": [],
            "recommendations": [],
        }
    )


def test_format_for_prompt_uses_brief_when_primary() -> None:
    bundle = BrandContextBundleResponse(
        primary_source="brand_intelligence_brief",
        approved_brief_id=uuid4(),
        brief_version=1,
        brand_brief={
            "brand_identity": {"brand_name": "Acme", "short_description": "Test brand"},
            "voice_and_tone": {"tone": "friendly"},
            "missing_information": ["Certificazioni"],
        },
        knowledge_score=_minimal_score(),
    )
    text = BrandIntelligenceContextBuilder.format_for_prompt(bundle)
    assert text is not None
    assert "Brand Intelligence Brief" in text
    assert "Acme" in text
    assert "friendly" in text
    assert "Missing information" in text


def test_context_bundle_primary_source_field() -> None:
    fields = BrandContextBundleResponse.model_fields
    assert "primary_source" in fields
    assert "brand_brief" in fields
