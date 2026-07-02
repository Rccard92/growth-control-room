"""AI provider router for structured JSON generation."""

from __future__ import annotations

from typing import Any

from app.services.ai.ai_client import AiRequestMetadata, generate_structured_json
from app.services.ai.claude_client import generate_claude_structured_json

__all__ = ["generate_structured_json_with_provider"]


async def generate_structured_json_with_provider(
    *,
    provider: str | None,
    system_prompt: str,
    user_prompt: str,
    metadata: AiRequestMetadata,
    timeout: float = 60.0,
    model: str | None = None,
    prompt_cache_key: str | None = None,
) -> dict[str, Any]:
    normalized_provider = (provider or "openai").strip().lower()

    if normalized_provider == "openai":
        return await generate_structured_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            metadata=metadata,
            timeout=timeout,
            model=model,
            prompt_cache_key=prompt_cache_key,
        )

    if normalized_provider == "claude":
        return await generate_claude_structured_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            metadata=metadata,
            timeout=timeout,
            model=model,
        )

    raise ValueError(f"Unsupported AI provider: {provider}")
