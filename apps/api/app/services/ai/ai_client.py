"""Centralized OpenAI client with usage logging and budget guardrails."""

from __future__ import annotations

import hashlib
import json
import logging
import time
from decimal import Decimal
from typing import Any
from uuid import UUID

from openai import AsyncOpenAI, OpenAIError
from pydantic import BaseModel

from app.core.config import settings
from app.db.session import get_session_factory
from app.services.ai.exceptions import (
    AiBudgetExceededError,
    AiSingleRequestBlockedError,
    OpenAINotConfiguredError,
    OpenAIRequestError,
)
from app.services.ai.model_policy import AiResolvedModel, resolve_ai_model, resolve_standard_fallback
from app.services.ai.pricing import estimate_usage_cost
from app.services.ai.usage_service import (
    UsageLogInput,
    check_budget_before_request,
    check_single_request_cost,
    record_usage_log,
    truncate_preview,
)

logger = logging.getLogger(__name__)

__all__ = [
    "AiBudgetExceededError",
    "AiRequestMetadata",
    "AiSingleRequestBlockedError",
    "OpenAINotConfiguredError",
    "OpenAIRequestError",
    "generate_structured_json",
    "is_openai_configured",
]


class AiRequestMetadata(BaseModel):
    project_id: UUID
    module: str
    operation: str
    entity_type: str | None = None
    entity_id: str | None = None
    job_id: str | None = None
    context_profile: str | None = None
    context_hash: str | None = None
    context_chars: int | None = None
    context_blocks_used: list[str] | None = None


def is_openai_configured() -> bool:
    return bool(settings.openai_api_key and settings.openai_api_key.strip())


def _client() -> AsyncOpenAI:
    if not is_openai_configured():
        raise OpenAINotConfiguredError("OPENAI_API_KEY non configurata")
    return AsyncOpenAI(api_key=settings.openai_api_key)


def _hash_prompt(system_prompt: str, user_prompt: str) -> str:
    payload = f"{system_prompt}\n---\n{user_prompt}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _context_fields_from_metadata(metadata: AiRequestMetadata) -> dict[str, Any]:
    return {
        "context_profile": metadata.context_profile,
        "context_hash": metadata.context_hash,
        "context_chars": metadata.context_chars,
        "context_blocks_used": metadata.context_blocks_used,
    }


def _model_policy_fields(
    resolved: AiResolvedModel,
    requested_model: str | None,
) -> dict[str, Any]:
    return {
        "model_tier": resolved.tier,
        "model_policy_source": resolved.policy_source,
        "requested_model": requested_model,
        "max_output_tokens": resolved.max_output_tokens,
        "temperature": Decimal(str(resolved.temperature)),
        "reasoning_effort": resolved.reasoning_effort,
    }


def _extract_usage(response: Any) -> dict[str, int]:
    usage = getattr(response, "usage", None)
    if usage is None:
        return {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "cached_input_tokens": 0,
            "reasoning_tokens": 0,
        }

    input_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
    output_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
    total_tokens = int(getattr(usage, "total_tokens", 0) or 0)
    cached = 0
    reasoning = 0

    prompt_details = getattr(usage, "prompt_tokens_details", None)
    if prompt_details is not None:
        cached = int(getattr(prompt_details, "cached_tokens", 0) or 0)
    completion_details = getattr(usage, "completion_tokens_details", None)
    if completion_details is not None:
        reasoning = int(getattr(completion_details, "reasoning_tokens", 0) or 0)

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "cached_input_tokens": cached,
        "reasoning_tokens": reasoning,
    }


class _SchemaParseError(Exception):
    def __init__(self, *, content: str, response: Any | None, message: str) -> None:
        super().__init__(message)
        self.content = content
        self.response = response
        self.error_message = message


def _parse_json_object_response(response: Any) -> tuple[dict[str, Any], str]:
    content = (response.choices[0].message.content or "").strip()
    if not content:
        raise _SchemaParseError(
            content=content,
            response=response,
            message="Risposta OpenAI vuota",
        )
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise _SchemaParseError(
            content=content,
            response=response,
            message="Risposta OpenAI non è JSON valido",
        ) from exc
    if not isinstance(parsed, dict):
        raise _SchemaParseError(
            content=content,
            response=response,
            message="Risposta OpenAI deve essere un oggetto JSON",
        )
    return parsed, content


async def _call_openai(
    client: AsyncOpenAI,
    *,
    resolved: AiResolvedModel,
    system_prompt: str,
    user_prompt: str,
    timeout: float,
) -> Any:
    kwargs: dict[str, Any] = {
        "model": resolved.model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "response_format": {"type": "json_object"},
        "timeout": timeout,
        "max_tokens": resolved.max_output_tokens,
        "temperature": resolved.temperature,
    }
    reasoning_model = (settings.openai_model_reasoning or "").strip()
    if (
        resolved.reasoning_effort
        and reasoning_model
        and resolved.model == reasoning_model
    ):
        kwargs["reasoning_effort"] = resolved.reasoning_effort
    return await client.chat.completions.create(**kwargs)


async def _persist_log(data: UsageLogInput) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            await record_usage_log(session, data)
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("Failed to persist AI usage log")


def _base_log_input(
    *,
    metadata: AiRequestMetadata,
    resolved: AiResolvedModel,
    requested_model: str | None,
    prompt_hash: str,
    prompt_chars: int,
    prompt_preview: str | None,
    prompt_cache_key: str | None,
    status: str,
    duration_ms: int,
    **extra: Any,
) -> UsageLogInput:
    return UsageLogInput(
        project_id=metadata.project_id,
        model=resolved.model,
        module=metadata.module,
        operation=metadata.operation,
        entity_type=metadata.entity_type,
        entity_id=metadata.entity_id,
        job_id=metadata.job_id,
        status=status,
        duration_ms=duration_ms,
        prompt_chars=prompt_chars,
        prompt_hash=prompt_hash,
        prompt_preview=prompt_preview,
        prompt_cache_key=prompt_cache_key,
        **_context_fields_from_metadata(metadata),
        **_model_policy_fields(resolved, requested_model),
        **extra,
    )


async def generate_structured_json(
    *,
    system_prompt: str,
    user_prompt: str,
    metadata: AiRequestMetadata,
    timeout: float = 60.0,
    model: str | None = None,
    prompt_cache_key: str | None = None,
) -> dict[str, Any]:
    resolved = resolve_ai_model(
        metadata,
        context_profile=metadata.context_profile,
        requested_model=model,
    )
    if resolved.warning:
        logger.info(
            "AI model policy warning (project=%s module=%s): %s",
            metadata.project_id,
            metadata.module,
            resolved.warning,
        )

    prompt_hash = _hash_prompt(system_prompt, user_prompt)
    prompt_chars = len(system_prompt) + len(user_prompt)
    prompt_preview = None
    if settings.ai_log_prompt_preview:
        prompt_preview = truncate_preview(f"[system]\n{system_prompt}\n\n[user]\n{user_prompt}")

    session_factory = get_session_factory()
    async with session_factory() as session:
        await check_budget_before_request(session, metadata.project_id)
        await session.commit()

    started = time.perf_counter()
    response = None
    content = ""
    parsed: dict[str, Any] | None = None
    active_resolved = resolved
    schema_retried = False

    try:
        client = _client()
        response = await _call_openai(
            client,
            resolved=active_resolved,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            timeout=timeout,
        )
        try:
            parsed, content = _parse_json_object_response(response)
        except _SchemaParseError as parse_exc:
            if (
                settings.ai_enable_model_fallback_on_schema_error
                and active_resolved.policy_source != "schema_fallback_retry"
            ):
                schema_retried = True
                active_resolved = resolve_standard_fallback()
                logger.warning(
                    "Schema parse failed; retry with standard tier (project=%s module=%s)",
                    metadata.project_id,
                    metadata.module,
                )
                response = await _call_openai(
                    client,
                    resolved=active_resolved,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    timeout=timeout,
                )
                parsed, content = _parse_json_object_response(response)
            else:
                raise OpenAIRequestError(parse_exc.error_message) from parse_exc
    except OpenAINotConfiguredError:
        raise
    except OpenAIRequestError:
        raise
    except _SchemaParseError as parse_exc:
        status = "error"
        error_type = "SchemaParseError"
        error_message = parse_exc.error_message
        content = parse_exc.content
        response = parse_exc.response
        duration_ms = int((time.perf_counter() - started) * 1000)
        await _persist_log(
            _base_log_input(
                metadata=metadata,
                resolved=active_resolved,
                requested_model=model,
                prompt_hash=prompt_hash,
                prompt_chars=prompt_chars,
                prompt_preview=prompt_preview,
                prompt_cache_key=prompt_cache_key,
                status=status,
                duration_ms=duration_ms,
                output_chars=len(content),
                output_preview=truncate_preview(content) if settings.ai_log_prompt_preview else None,
                response_id=getattr(response, "id", None) if response else None,
                error_type=error_type,
                error_message=error_message,
            )
        )
        raise OpenAIRequestError(error_message)
    except OpenAIError as exc:
        status = "error"
        error_type = type(exc).__name__
        error_message = str(exc).split("\n")[0]
        logger.warning("OpenAI request failed: %s", error_message)
        duration_ms = int((time.perf_counter() - started) * 1000)
        await _persist_log(
            _base_log_input(
                metadata=metadata,
                resolved=active_resolved,
                requested_model=model,
                prompt_hash=prompt_hash,
                prompt_chars=prompt_chars,
                prompt_preview=prompt_preview,
                prompt_cache_key=prompt_cache_key,
                status=status,
                duration_ms=duration_ms,
                error_type=error_type,
                error_message=error_message,
            )
        )
        raise OpenAIRequestError("Richiesta OpenAI non riuscita") from exc

    assert parsed is not None
    duration_ms = int((time.perf_counter() - started) * 1000)
    usage = _extract_usage(response)
    cost = estimate_usage_cost(
        active_resolved.model,
        input_tokens=usage["input_tokens"],
        output_tokens=usage["output_tokens"],
        cached_input_tokens=usage["cached_input_tokens"],
        reasoning_tokens=usage["reasoning_tokens"],
    )

    estimated_input = cost.input_cost if cost else None
    estimated_output = cost.output_cost if cost else None
    estimated_cached = cost.cached_cost if cost else None
    estimated_total = cost.total_cost if cost else None

    if estimated_total is not None:
        warn_threshold = settings.ai_single_request_warn_usd
        if warn_threshold and warn_threshold > 0 and estimated_total >= Decimal(str(warn_threshold)):
            logger.warning(
                "AI request cost %.4f USD exceeds warn threshold %.2f (project=%s module=%s)",
                estimated_total,
                warn_threshold,
                metadata.project_id,
                metadata.module,
            )
        check_single_request_cost(estimated_total)

    output_preview = truncate_preview(content) if settings.ai_log_prompt_preview else None

    await _persist_log(
        _base_log_input(
            metadata=metadata,
            resolved=active_resolved,
            requested_model=model,
            prompt_hash=prompt_hash,
            prompt_chars=prompt_chars,
            prompt_preview=prompt_preview,
            prompt_cache_key=prompt_cache_key,
            status="success",
            duration_ms=duration_ms,
            input_tokens=usage["input_tokens"],
            output_tokens=usage["output_tokens"],
            total_tokens=usage["total_tokens"],
            cached_input_tokens=usage["cached_input_tokens"],
            reasoning_tokens=usage["reasoning_tokens"],
            estimated_input_cost=estimated_input,
            estimated_output_cost=estimated_output,
            estimated_cached_cost=estimated_cached,
            estimated_total_cost=estimated_total,
            output_chars=len(content),
            output_preview=output_preview,
            response_id=getattr(response, "id", None),
        )
    )

    if schema_retried:
        logger.info(
            "Schema fallback retry succeeded (project=%s module=%s tier=%s)",
            metadata.project_id,
            metadata.module,
            active_resolved.tier,
        )

    return parsed
