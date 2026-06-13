"""BrandContextBuilder profile v1 priority tests."""

from datetime import datetime, timezone
from uuid import uuid4

from app.schemas.brand_intelligence import BrandContextBundleResponse, BrandKnowledgeScoreResponse
from app.services.brand_intelligence.context import BrandIntelligenceContextBuilder

_NOW = datetime.now(timezone.utc)
_PID = uuid4()


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


def test_format_for_prompt_uses_brand_profile_primary() -> None:
    from app.schemas.brand_intelligence import BrandProfileRead

    bundle = BrandContextBundleResponse(
        primary_source="brand_profile",
        missing_context=[],
        profile=BrandProfileRead(
            id=uuid4(),
            project_id=_PID,
            brand_name="Acme",
            short_description="Test brand",
            created_at=_NOW,
            updated_at=_NOW,
        ),
        knowledge_score=_minimal_score(),
    )
    text = BrandIntelligenceContextBuilder.format_for_prompt(bundle)
    assert text is not None
    assert "BRAND PROFILE" in text
    assert "Acme" in text
    assert "Test brand" in text


def test_context_bundle_has_missing_context_field() -> None:
    fields = BrandContextBundleResponse.model_fields
    assert "missing_context" in fields
    assert "primary_source" in fields
