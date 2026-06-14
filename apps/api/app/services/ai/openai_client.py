"""Backward-compatible re-export of centralized AI client."""

from app.services.ai.ai_client import (
    AiBudgetExceededError,
    AiRequestMetadata,
    AiSingleRequestBlockedError,
    OpenAINotConfiguredError,
    OpenAIRequestError,
    generate_structured_json,
    is_openai_configured,
)

__all__ = [
    "AiBudgetExceededError",
    "AiRequestMetadata",
    "AiSingleRequestBlockedError",
    "OpenAINotConfiguredError",
    "OpenAIRequestError",
    "generate_structured_json",
    "is_openai_configured",
]
