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
from app.services.ai.model_request_params import (
    build_openai_request_params,
    infer_model_family,
    is_known_supported_model,
)

__all__ = [
    "AiBudgetExceededError",
    "AiRequestMetadata",
    "AiSingleRequestBlockedError",
    "OpenAINotConfiguredError",
    "OpenAIRequestError",
    "build_openai_request_params",
    "generate_structured_json",
    "infer_model_family",
    "is_known_supported_model",
    "is_openai_configured",
]
