"""OpenAI Chat Completions request parameter compatibility by model family."""

from __future__ import annotations

from typing import Any, Literal

from app.core.config import settings
from app.services.ai.model_policy import AiResolvedModel
from app.services.ai.pricing import OPENAI_MODEL_PRICING

ModelFamily = Literal["legacy_chat", "reasoning"]

KNOWN_SUPPORTED_MODELS: frozenset[str] = frozenset(
    list(OPENAI_MODEL_PRICING.keys())
    + [
        "gpt-5.5",
        "gpt-5.4",
        "gpt-5.4-mini",
        "gpt-5.4-nano",
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4.1",
        "gpt-4.1-mini",
        "o1",
        "o1-mini",
        "o3-mini",
    ]
)


def infer_model_family(model: str) -> ModelFamily:
    normalized = model.strip().lower()
    if normalized.startswith("gpt-5"):
        return "reasoning"
    if normalized.startswith(("o1", "o3")):
        return "reasoning"
    return "legacy_chat"


def is_known_supported_model(model: str | None) -> bool:
    if not model or not str(model).strip():
        return False
    name = str(model).strip()
    if name in KNOWN_SUPPORTED_MODELS:
        return True
    family = infer_model_family(name)
    if family == "reasoning" and name.startswith("gpt-5"):
        return True
    return name in OPENAI_MODEL_PRICING


def build_openai_request_params(
    resolved: AiResolvedModel,
    *,
    system_prompt: str,
    user_prompt: str,
    structured_json: bool = True,
    timeout: float,
) -> dict[str, Any]:
    family = infer_model_family(resolved.model)
    kwargs: dict[str, Any] = {
        "model": resolved.model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "timeout": timeout,
    }

    if family == "reasoning":
        kwargs["max_completion_tokens"] = resolved.max_output_tokens
        if resolved.reasoning_effort:
            kwargs["reasoning_effort"] = resolved.reasoning_effort
        elif (settings.openai_model_reasoning or "").strip() == resolved.model:
            kwargs.setdefault("reasoning_effort", "medium")
    else:
        kwargs["max_tokens"] = resolved.max_output_tokens
        kwargs["temperature"] = resolved.temperature
        reasoning_model = (settings.openai_model_reasoning or "").strip()
        if (
            resolved.reasoning_effort
            and reasoning_model
            and resolved.model == reasoning_model
        ):
            kwargs["reasoning_effort"] = resolved.reasoning_effort

    if structured_json:
        kwargs["response_format"] = {"type": "json_object"}

    return kwargs
