"""Tests for AI model policy profiles."""

from app.services.ai.model_policy import PROFILE_PARAMS


def test_seo_skill_audit_profile_exists() -> None:
    profile = PROFILE_PARAMS["seo_skill_audit"]
    assert profile["tier"].value == "standard"
    assert profile["max_output_tokens"] == 6000
    assert profile["temperature"] == 0.3
