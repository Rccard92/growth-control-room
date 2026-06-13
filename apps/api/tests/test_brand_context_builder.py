"""BrandIntelligenceContextBuilder.format_for_prompt tests."""

from datetime import datetime, timezone
from uuid import uuid4

from app.schemas.brand_intelligence import (
    BrandContextBundleResponse,
    BrandKnowledgeScoreResponse,
    BrandProfileRead,
)
from app.services.brand_intelligence.context import BrandIntelligenceContextBuilder

_NOW = datetime.now(timezone.utc)
_PID = uuid4()


def _score(overall: int = 50) -> BrandKnowledgeScoreResponse:
    return BrandKnowledgeScoreResponse(
        overall_score=overall,
        status="developing",
        section_scores={},
        missing_required=[],
        recommendations=[],
    )


def test_format_for_prompt_empty_returns_none() -> None:
    bundle = BrandContextBundleResponse(
        primary_source="minimal",
        products=[],
        categories=[],
        audience=[],
        claims=[],
        content_pillars=[],
        guardrails=[],
        assets=[],
        knowledge_score=_score(),
    )
    assert BrandIntelligenceContextBuilder.format_for_prompt(bundle) is None


def test_format_for_prompt_uses_profile_v1() -> None:
    bundle = BrandContextBundleResponse(
        primary_source="brand_profile",
        profile=BrandProfileRead(
            id=uuid4(),
            project_id=_PID,
            brand_name="Test Brand",
            short_description="Premium artisan products",
            mission="Qualità artigianale",
            values=["tradizione", "qualità"],
            tone_notes="Caldo e autentico",
            created_at=_NOW,
            updated_at=_NOW,
        ),
        products=[],
        categories=[],
        audience=[],
        claims=[],
        content_pillars=[],
        guardrails=[],
        assets=[],
        knowledge_score=_score(72),
    )

    text = BrandIntelligenceContextBuilder.format_for_prompt(bundle)
    assert text is not None
    assert text.startswith("# Brand Profile")
    assert "Test Brand" in text
    assert "Premium artisan products" in text
    assert "Qualità artigianale" in text
    assert "tradizione" in text
    assert "Caldo e autentico" in text
