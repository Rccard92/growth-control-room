"""Tests for SEO skill user-facing error messages."""

from app.services.seo_skills.error_messages import (
    OPENAI_EMPTY_RESPONSE_RUN_MESSAGE,
    OPENAI_INVALID_JSON_RUN_MESSAGE,
    humanize_skill_error,
)


def test_humanize_openai_empty_response_for_openai_provider() -> None:
    message = humanize_skill_error(
        Exception("Risposta OpenAI vuota"),
        provider="openai",
    )
    assert message == OPENAI_EMPTY_RESPONSE_RUN_MESSAGE


def test_humanize_provider_not_configured() -> None:
    message = humanize_skill_error(
        Exception("OpenAI provider is not configured"),
        provider="openai",
    )
    assert message == "Provider OpenAI non configurato."


def test_humanize_openai_invalid_json_for_openai_provider() -> None:
    message = humanize_skill_error(
        Exception("Risposta OpenAI non è JSON valido"),
        provider="openai",
    )
    assert message == OPENAI_INVALID_JSON_RUN_MESSAGE
