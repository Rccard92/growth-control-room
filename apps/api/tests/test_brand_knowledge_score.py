"""Brand Knowledge Score unit tests (no DB)."""

from types import SimpleNamespace

from app.services.brand_intelligence.identity_service import (
    identity_completion,
    identity_has_minimum,
)
from app.services.brand_intelligence.score import (
    SECTION_LABELS,
    _overall_status,
    _score_brand_profile,
    product_knowledge_module_completion,
    profile_has_minimum,
    profile_is_complete,
    profile_missing_context,
)
from app.services.brand_intelligence.safe_claims_service import (
    safe_claims_completion,
    safe_claims_has_minimum,
)
from app.services.brand_intelligence.visual_identity_service import (
    visual_completion,
    visual_has_minimum,
)


def test_empty_profile_scores_zero() -> None:
    score, missing, _ = _score_brand_profile(None)
    assert score == 0
    assert "brand_name" in missing


def test_minimal_profile_has_points() -> None:
    profile = SimpleNamespace(
        brand_name="Acme",
        short_description="Artisan food",
        story=None,
        website_url="https://acme.test",
        mission=None,
        values=None,
        differentiators=None,
        origin_notes=None,
        production_notes=None,
        tone_notes=None,
        ai_summary=None,
    )
    score, missing, _ = _score_brand_profile(profile)
    assert score >= 50
    assert "brand_name" not in missing


def test_profile_has_minimum() -> None:
    profile = SimpleNamespace(brand_name="Acme", short_description="Desc", story=None)
    assert profile_has_minimum(profile) is True
    assert profile_has_minimum(None) is False


def test_profile_is_complete() -> None:
    profile = SimpleNamespace(
        brand_name="Acme",
        short_description="Desc",
        story=None,
        website_url="https://acme.test",
        mission="Mission",
        values=["v1"],
        ai_summary="Summary",
    )
    assert profile_is_complete(profile) is True


def test_profile_missing_context() -> None:
    profile = SimpleNamespace(
        brand_name="Acme",
        short_description=None,
        story=None,
        website_url=None,
        mission=None,
        values=None,
    )
    missing = profile_missing_context(profile)
    assert "brand_profile.short_description" in missing
    assert "brand_profile.website_url" in missing


def test_overall_status_thresholds() -> None:
    assert _overall_status(30) == "incomplete"
    assert _overall_status(65) == "developing"
    assert _overall_status(85) == "ready"


def test_section_labels_five_modules() -> None:
    assert set(SECTION_LABELS.keys()) == {
        "brandProfile",
        "brandIdentity",
        "visualIdentity",
        "safeClaims",
        "productKnowledge",
    }


def test_identity_has_minimum() -> None:
    identity = SimpleNamespace(
        positioning="Premium",
        brand_values=None,
        differentiators=None,
        what_brand_is=None,
        what_brand_is_not=None,
    )
    assert identity_has_minimum(identity) is True
    assert identity_completion(identity) == "partial"


def test_safe_claims_completion() -> None:
    row = SimpleNamespace(
        allowed_claims=["ok"],
        forbidden_claims=["no"],
        caution_claims=None,
        disclaimers=["disc"],
        health_claim_rules=None,
        competitor_rules=None,
        process_secrets=None,
        tone_red_flags=None,
        notes=None,
    )
    assert safe_claims_has_minimum(row) is True
    assert safe_claims_completion(row) == "complete"


def test_product_knowledge_module_completion() -> None:
    general = SimpleNamespace(
        general_principles=["p"],
        common_strengths=None,
        common_quality_rules=None,
        common_production_notes=None,
        common_usage_notes=None,
        common_objections=None,
        common_faq=None,
        communication_rules=None,
        product_storytelling_rules=None,
        notes=None,
    )
    assert product_knowledge_module_completion(None, 0) == "empty"
    assert product_knowledge_module_completion(general, 0) == "partial"
    assert product_knowledge_module_completion(general, 1) == "complete"
    assert product_knowledge_module_completion(None, 2) == "partial"


def test_visual_has_minimum() -> None:
    visual = SimpleNamespace(
        primary_logo_url="https://x.test/logo.png",
        primary_color=None,
        secondary_color=None,
        accent_color=None,
        color_palette=None,
    )
    assert visual_has_minimum(visual) is True
    assert visual_completion(visual) == "partial"
