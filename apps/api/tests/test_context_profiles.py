"""AI Context Profiles tests."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.schemas.brand_intelligence import (
    BrandContextBundleResponse,
    BrandEditorialGuidelinesRead,
    BrandFaqObjectionsRead,
    BrandIdentityRead,
    BrandKnowledgeScoreResponse,
    BrandProfileRead,
    BrandSafeClaimsRead,
)
from app.services.ai.ai_client import AiRequestMetadata
from app.services.ai.context_profiles import (
    CLAIM_RISK_PROFILES,
    AiContextProfile,
    build_context_for_profile,
    enrich_ai_metadata,
)
from app.services.ai.usage_service import UsageLogInput, record_usage_log

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


def _rich_bundle() -> BrandContextBundleResponse:
    return BrandContextBundleResponse(
        primary_source="brand_profile",
        missing_context=[],
        profile=BrandProfileRead(
            id=uuid4(),
            project_id=_PID,
            brand_name="Acme Foods",
            short_description="Prodotti artigianali italiani",
            created_at=_NOW,
            updated_at=_NOW,
        ),
        brand_identity=BrandIdentityRead(
            id=uuid4(),
            project_id=_PID,
            positioning="Premium artigianale",
            what_brand_is="Autentico e trasparente",
            created_at=_NOW,
            updated_at=_NOW,
        ),
        safe_claims=BrandSafeClaimsRead(
            id=uuid4(),
            project_id=_PID,
            allowed_claims=["100% italiano"],
            forbidden_claims=["cura miracolosa"],
            created_at=_NOW,
            updated_at=_NOW,
        ),
        faq_objections=BrandFaqObjectionsRead(
            id=uuid4(),
            project_id=_PID,
            general_faq=["Domanda lunga su spedizioni? Risposta dettagliata"],
            objections=["Troppo caro"],
            created_at=_NOW,
            updated_at=_NOW,
        ),
        editorial_guidelines=BrandEditorialGuidelinesRead(
            id=uuid4(),
            project_id=_PID,
            content_philosophy="Contenuti utili e umani",
            article_dos=["Usa esempi concreti"],
            article_donts=["Non esagerare con i claim"],
            created_at=_NOW,
            updated_at=_NOW,
        ),
        knowledge_score=_minimal_score(),
    )


def _run(coro):
    return asyncio.run(coro)


@patch(
    "app.services.ai.context_profiles.BrandIntelligenceContextBuilder.build_brand_context",
    new_callable=AsyncMock,
)
def test_minimal_profile_excludes_long_sections(mock_build) -> None:
    mock_build.return_value = _rich_bundle()

    async def run():
        session = AsyncMock()
        result = await build_context_for_profile(
            session, _PID, AiContextProfile.MINIMAL
        )
        assert "EDITORIAL GUIDELINES" not in result.context_text
        assert "FAQ & OBJECTIONS" not in result.context_text
        assert result.profile == "minimal"

    _run(run())


@patch(
    "app.services.ai.context_profiles.BrandIntelligenceContextBuilder.build_brand_context",
    new_callable=AsyncMock,
)
def test_image_alt_excludes_faq_and_editorial(mock_build) -> None:
    mock_build.return_value = _rich_bundle()

    async def run():
        session = AsyncMock()
        result = await build_context_for_profile(
            session, _PID, AiContextProfile.IMAGE_ALT
        )
        assert "FAQ" not in result.context_text or "FAQ & OBJECTIONS" not in result.context_text
        assert "EDITORIAL GUIDELINES" not in result.context_text
        assert "SAFE CLAIMS" in result.context_text
        assert result.profile == "image_alt"

    _run(run())


@patch(
    "app.services.ai.context_profiles.BrandIntelligenceContextBuilder.build_brand_context",
    new_callable=AsyncMock,
)
def test_blog_brief_includes_editorial_guidelines(mock_build) -> None:
    mock_build.return_value = _rich_bundle()

    async def run():
        session = AsyncMock()
        result = await build_context_for_profile(
            session,
            _PID,
            AiContextProfile.BLOG_BRIEF,
            options={"editorial_item": {"title": "Ricetta test", "content_type": "recipe"}},
        )
        assert "EDITORIAL GUIDELINES" in result.context_text
        assert "editorial_guidelines" in result.context_blocks_used
        assert result.profile == "blog_brief"

    _run(run())


@patch(
    "app.services.ai.context_profiles.BrandIntelligenceContextBuilder.build_brand_context",
    new_callable=AsyncMock,
)
def test_article_draft_uses_brief_and_selected_faq(mock_build) -> None:
    mock_build.return_value = _rich_bundle()

    async def run():
        session = AsyncMock()
        result = await build_context_for_profile(
            session,
            _PID,
            AiContextProfile.ARTICLE_DRAFT,
            options={
                "brief_payload": {
                    "proposedTitle": "Guida olio EVO",
                    "primaryKeyword": "olio evo",
                    "faqToInclude": ["spedizioni"],
                }
            },
        )
        assert "BRIEF APPROVATO" in result.context_text
        assert "approved_brief" in result.context_blocks_used
        assert "EDITORIAL GUIDELINES" in result.context_text
        assert "faq_selected" in result.context_blocks_used or "FAQ" in result.context_text

    _run(run())


@patch(
    "app.services.ai.context_profiles.BrandIntelligenceContextBuilder.build_brand_context",
    new_callable=AsyncMock,
)
@pytest.mark.parametrize(
    "profile",
    [
        AiContextProfile.PRODUCT_SEO_FIELD,
        AiContextProfile.COLLECTION_SEO_FIELD,
        AiContextProfile.PRODUCT_SEO_FULL,
        AiContextProfile.BLOG_BRIEF,
        AiContextProfile.ARTICLE_DRAFT,
        AiContextProfile.COMPLIANCE_REVIEW,
    ],
)
def test_claim_risk_profiles_include_safe_claims(mock_build, profile) -> None:
    mock_build.return_value = _rich_bundle()
    assert profile in CLAIM_RISK_PROFILES

    async def run():
        session = AsyncMock()
        opts = (
            {"brief_payload": {"proposedTitle": "Test"}}
            if profile == AiContextProfile.ARTICLE_DRAFT
            else None
        )
        result = await build_context_for_profile(session, _PID, profile, options=opts)
        assert "SAFE CLAIMS" in result.context_text
        assert "safe_claims" in result.context_blocks_used

    _run(run())


@patch(
    "app.services.ai.context_profiles.BrandIntelligenceContextBuilder.build_brand_context",
    new_callable=AsyncMock,
)
def test_missing_sections_add_warnings_no_crash(mock_build) -> None:
    bundle = BrandContextBundleResponse(
        primary_source="minimal",
        missing_context=["safe_claims"],
        profile=BrandProfileRead(
            id=uuid4(),
            project_id=_PID,
            brand_name="Solo nome",
            created_at=_NOW,
            updated_at=_NOW,
        ),
        knowledge_score=_minimal_score(),
    )
    mock_build.return_value = bundle

    async def run():
        session = AsyncMock()
        result = await build_context_for_profile(
            session, _PID, AiContextProfile.PRODUCT_SEO_FIELD
        )
        assert "Safe Claims missing" in result.warnings
        assert result.context_hash
        assert result.estimated_chars > 0

    _run(run())


def test_enrich_ai_metadata() -> None:
    base = AiRequestMetadata(
        project_id=_PID,
        module="blog_brief",
        operation="generate_brief",
    )
    from app.services.ai.context_profiles import AiContextResult

    ctx = AiContextResult(
        profile="blog_brief",
        context_text="CONTEXT PROFILE: blog_brief\n\nBRAND PROFILE",
        context_blocks_used=["brand_profile"],
        estimated_chars=42,
        warnings=[],
        context_hash="abc123",
    )
    enriched = enrich_ai_metadata(base, ctx)
    assert enriched.context_profile == "blog_brief"
    assert enriched.context_chars == 42
    assert enriched.context_hash == "abc123"
    assert enriched.context_blocks_used == ["brand_profile"]


def test_record_usage_log_persists_context_profile() -> None:
    async def run() -> None:
        session = AsyncMock()
        session.flush = AsyncMock()
        project_id = uuid4()
        row = await record_usage_log(
            session,
            UsageLogInput(
                project_id=project_id,
                model="gpt-4o-mini",
                module="product_seo",
                operation="generate_field",
                status="success",
                context_profile="image_alt",
                context_hash="deadbeef",
                context_chars=1200,
                context_blocks_used=["brand_profile", "safe_claims"],
            ),
        )
        session.add.assert_called_once()
        added = session.add.call_args[0][0]
        assert added.context_profile == "image_alt"
        assert added.context_chars == 1200
        assert added.context_blocks_used == ["brand_profile", "safe_claims"]
        assert row.context_profile == "image_alt"

    asyncio.run(run())
