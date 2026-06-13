"""BrandIntelligenceContextBuilder.format_for_prompt tests."""

from datetime import datetime, timezone
from uuid import uuid4

from app.schemas.brand_identity_visual import BrandIdentityRead, BrandVisualIdentityRead
from app.schemas.brand_safe_claims import BrandSafeClaimsRead
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
    assert text.startswith("BRAND PROFILE")
    assert "Test Brand" in text
    assert "Premium artisan products" in text
    assert "Qualità artigianale" in text


def test_format_for_prompt_includes_identity_and_visual() -> None:
    bundle = BrandContextBundleResponse(
        primary_source="brand_profile",
        profile=BrandProfileRead(
            id=uuid4(),
            project_id=_PID,
            brand_name="Acme",
            short_description="Artisan brand",
            created_at=_NOW,
            updated_at=_NOW,
        ),
        brand_identity=BrandIdentityRead(
            id=uuid4(),
            project_id=_PID,
            positioning="Premium niche",
            brand_values=["quality", "craft"],
            created_at=_NOW,
            updated_at=_NOW,
        ),
        visual_identity=BrandVisualIdentityRead(
            id=uuid4(),
            project_id=_PID,
            primary_color="#112233",
            primary_logo_url="https://acme.test/logo.png",
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
        knowledge_score=_score(80),
    )

    text = BrandIntelligenceContextBuilder.format_for_prompt(bundle)
    assert text is not None
    assert "BRAND PROFILE" in text
    assert "BRAND IDENTITY" in text
    assert "Premium niche" in text
    assert "VISUAL IDENTITY" in text
    assert "#112233" in text


def test_build_prompt_context_machine_ready() -> None:
    from app.schemas.brand_intelligence import BrandPromptContext

    bundle = BrandContextBundleResponse(
        brand_context_version="v1",
        primary_source="brand_profile",
        profile=BrandProfileRead(
            id=uuid4(),
            project_id=_PID,
            brand_name="Acme",
            short_description="Artisan brand",
            created_at=_NOW,
            updated_at=_NOW,
        ),
        brand_identity=BrandIdentityRead(
            id=uuid4(),
            project_id=_PID,
            positioning="Premium niche",
            brand_values=["quality"],
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
        knowledge_score=_score(80),
    )
    prompt_ctx = BrandIntelligenceContextBuilder.build_prompt_context(bundle)
    assert prompt_ctx is not None
    assert isinstance(prompt_ctx, BrandPromptContext)
    assert prompt_ctx.brand_profile is not None
    assert "Acme" in prompt_ctx.brand_profile
    assert prompt_ctx.brand_identity is not None
    assert "Premium niche" in prompt_ctx.brand_identity
    assert prompt_ctx.full_text is not None
    assert "BRAND PROFILE" in prompt_ctx.full_text
    assert "BRAND IDENTITY" in prompt_ctx.full_text


def test_format_safe_claims_for_prompt() -> None:
    safe = BrandSafeClaimsRead(
        id=uuid4(),
        project_id=_PID,
        allowed_claims=["Artigianale"],
        forbidden_claims=["Cura malattie"],
        caution_claims=["Benefico"],
        created_at=_NOW,
        updated_at=_NOW,
    )
    text = BrandIntelligenceContextBuilder.format_safe_claims_for_prompt(safe)
    assert "SAFE CLAIMS & RED FLAGS" in text
    assert "Claim consentiti" in text
    assert "Artigianale" in text
    assert "Claim vietati" in text
    assert "Cura malattie" in text


def test_build_prompt_context_includes_safe_claims_fallback() -> None:
    bundle = BrandContextBundleResponse(
        brand_context_version="v1",
        primary_source="brand_profile",
        profile=BrandProfileRead(
            id=uuid4(),
            project_id=_PID,
            brand_name="Acme",
            short_description="Artisan brand",
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
        knowledge_score=_score(80),
    )
    prompt_ctx = BrandIntelligenceContextBuilder.build_prompt_context(bundle)
    assert prompt_ctx is not None
    assert prompt_ctx.safe_claims is not None
    assert "SAFE CLAIMS" in prompt_ctx.safe_claims
    assert "fallback prudenza" in prompt_ctx.safe_claims.lower() or "prudenza" in prompt_ctx.safe_claims.lower()
    assert "SAFE CLAIMS" in (prompt_ctx.full_text or "")
