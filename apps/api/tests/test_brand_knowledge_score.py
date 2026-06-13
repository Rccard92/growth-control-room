"""Brand Knowledge Score unit tests (no DB)."""

from types import SimpleNamespace

from app.services.brand_intelligence.score import (
    _overall_status,
    _score_brand_profile,
    profile_has_minimum,
    profile_is_complete,
    profile_missing_context,
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
    assert "short_description" in missing
    assert "website_url" in missing


def test_overall_status_thresholds() -> None:
    assert _overall_status(30) == "incomplete"
    assert _overall_status(65) == "developing"
    assert _overall_status(85) == "ready"
