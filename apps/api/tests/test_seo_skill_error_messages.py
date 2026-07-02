"""Tests for SEO skill user-facing error messages."""

from app.services.seo_skills.error_messages import (
    OPENAI_EMPTY_RESPONSE_RUN_MESSAGE,
    OPENAI_INVALID_JSON_RUN_MESSAGE,
    OPENAI_OUTPUT_TRUNCATED_RUN_MESSAGE,
    humanize_skill_error,
)
from app.services.ai.exceptions import OpenAIRequestError


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


def test_humanize_output_truncated_by_error_code() -> None:
    message = humanize_skill_error(
        OpenAIRequestError("ignored", code="output_truncated"),
        provider="openai",
    )
    assert message == OPENAI_OUTPUT_TRUNCATED_RUN_MESSAGE


def test_humanize_output_truncated_by_message_text() -> None:
    message = humanize_skill_error(
        Exception("OpenAI ha interrotto la risposta perché l'output era troppo lungo."),
        provider="openai",
    )
    assert message == OPENAI_OUTPUT_TRUNCATED_RUN_MESSAGE
