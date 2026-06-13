"""BrandIntelligenceContextBuilder.format_for_prompt tests."""

from datetime import datetime, timezone
from uuid import uuid4

from app.schemas.brand_intelligence import (
    BrandAiGuardrailRead,
    BrandClaimRuleRead,
    BrandContextBundleResponse,
    BrandKnowledgeScoreResponse,
    BrandProductKnowledgeRead,
    BrandProfileRead,
    BrandSeoStrategyRead,
    BrandVoiceRead,
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


def test_format_for_prompt_includes_brand_block() -> None:
    bundle = BrandContextBundleResponse(
        profile=BrandProfileRead(
            id=uuid4(),
            project_id=_PID,
            brand_name="Test Brand",
            short_description="Premium artisan products",
            created_at=_NOW,
            updated_at=_NOW,
        ),
        voice=BrandVoiceRead(
            id=uuid4(),
            project_id=_PID,
            tone="authentic",
            words_to_use=["craft", "natural"],
            created_at=_NOW,
            updated_at=_NOW,
        ),
        products=[
            BrandProductKnowledgeRead(
                id=uuid4(),
                project_id=_PID,
                name="Olio EVO",
                entity_type="product",
                description="Cold pressed",
                priority="high",
                created_at=_NOW,
                updated_at=_NOW,
            )
        ],
        categories=[],
        audience=[],
        claims=[
            BrandClaimRuleRead(
                id=uuid4(),
                project_id=_PID,
                rule_type="forbidden",
                title="No health cures",
                severity="critical",
                created_at=_NOW,
                updated_at=_NOW,
            )
        ],
        seo_strategy=BrandSeoStrategyRead(
            id=uuid4(),
            project_id=_PID,
            primary_keywords=["olio evo", "extra virgin"],
            created_at=_NOW,
            updated_at=_NOW,
        ),
        content_pillars=[],
        guardrails=[
            BrandAiGuardrailRead(
                id=uuid4(),
                project_id=_PID,
                title="Do not invent ingredients",
                rule_type="must_not",
                created_at=_NOW,
                updated_at=_NOW,
            )
        ],
        assets=[],
        knowledge_score=_score(72),
    )

    text = BrandIntelligenceContextBuilder.format_for_prompt(bundle)
    assert text is not None
    assert text.startswith("# Brand Intelligence")
    assert "Test Brand" in text
    assert "authentic" in text
    assert "Olio EVO" in text
    assert "No health cures" in text
    assert "must NOT" in text
    assert "olio evo" in text
