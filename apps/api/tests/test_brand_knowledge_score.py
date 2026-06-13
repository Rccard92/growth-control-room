"""Brand Knowledge Score unit tests (no DB)."""

from types import SimpleNamespace

from app.services.brand_intelligence.score import (
    _overall_status,
    _score_audience,
    _score_brand_profile,
    _score_claims,
    _score_guardrails,
    _score_products,
    _score_voice,
)


def test_empty_profile_scores_zero() -> None:
    score, missing, _ = _score_brand_profile(None)
    assert score == 0
    assert "brand_name" in missing


def test_minimal_profile_scores_full() -> None:
    profile = SimpleNamespace(
        brand_name="Acme",
        short_description="Artisan food",
        story=None,
        website_url="https://acme.test",
        industry=None,
    )
    score, missing, _ = _score_brand_profile(profile)
    assert score == 100
    assert missing == []


def test_voice_requires_tone() -> None:
    score, missing, _ = _score_voice(None)
    assert score == 0
    assert "tone" in missing


def test_voice_with_tone_and_style() -> None:
    voice = SimpleNamespace(
        tone="warm",
        style_notes="Short sentences",
        words_to_use=None,
        words_to_avoid=None,
    )
    score, missing, _ = _score_voice(voice)
    assert score == 100
    assert missing == []


def test_products_need_name_and_description() -> None:
    score, missing, _ = _score_products([])
    assert score == 0
    assert "product_or_category_knowledge" in missing

    product = SimpleNamespace(name="Olio EVO", description="Extra virgin olive oil")
    score2, missing2, _ = _score_products([product])
    assert score2 >= 60
    assert missing2 == []


def test_claims_need_forbidden_or_caution() -> None:
    score, missing, _ = _score_claims([])
    assert score == 0
    assert "claim_forbidden_or_caution" in missing

    claim = SimpleNamespace(rule_type="forbidden", title="No medical claims")
    score2, missing2, _ = _score_claims([claim])
    assert score2 >= 50
    assert missing2 == []


def test_guardrails_need_must_not() -> None:
    score, missing, _ = _score_guardrails([])
    assert score == 0
    assert "must_not_guardrail" in missing

    guard = SimpleNamespace(rule_type="must_not", title="No invented ingredients")
    score2, missing2, _ = _score_guardrails([guard])
    assert score2 >= 50
    assert missing2 == []


def test_audience_segment() -> None:
    seg = SimpleNamespace(segment_name="Food lovers")
    score, _, _ = _score_audience([seg])
    assert score >= 50


def test_overall_status_thresholds() -> None:
    assert _overall_status(30) == "incomplete"
    assert _overall_status(65) == "developing"
    assert _overall_status(85) == "ready"
