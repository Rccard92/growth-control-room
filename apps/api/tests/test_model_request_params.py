"""Tests for OpenAI request parameter compatibility."""

from __future__ import annotations

from app.services.ai.model_policy import AiResolvedModel
from app.services.ai.model_request_params import (
    build_openai_request_params,
    infer_model_family,
    is_known_supported_model,
)


def _resolved(model: str, **kwargs: object) -> AiResolvedModel:
    base = {
        "model": model,
        "tier": "cheap",
        "max_output_tokens": 120,
        "temperature": 0.35,
        "policy_source": "manual",
    }
    base.update(kwargs)
    return AiResolvedModel.model_validate(base)


def test_gpt54_mini_uses_max_completion_tokens_without_temperature() -> None:
    params = build_openai_request_params(
        _resolved("gpt-5.4-mini"),
        system_prompt="system",
        user_prompt="user",
        timeout=30.0,
    )
    assert infer_model_family("gpt-5.4-mini") == "reasoning"
    assert "max_completion_tokens" in params
    assert params["max_completion_tokens"] == 120
    assert "max_tokens" not in params
    assert "temperature" not in params


def test_gpt4o_mini_uses_max_tokens_and_temperature() -> None:
    params = build_openai_request_params(
        _resolved("gpt-4o-mini"),
        system_prompt="system",
        user_prompt="user",
        timeout=30.0,
    )
    assert infer_model_family("gpt-4o-mini") == "legacy_chat"
    assert params["max_tokens"] == 120
    assert params["temperature"] == 0.35
    assert "max_completion_tokens" not in params


def test_reasoning_effort_on_gpt5_family() -> None:
    params = build_openai_request_params(
        _resolved("gpt-5.5", reasoning_effort="high"),
        system_prompt="system",
        user_prompt="user",
        timeout=30.0,
    )
    assert params["reasoning_effort"] == "high"


def test_known_supported_models_include_gpt5() -> None:
    assert is_known_supported_model("gpt-5.4-mini")
    assert is_known_supported_model("gpt-4o-mini")
