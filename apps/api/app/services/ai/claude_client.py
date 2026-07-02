"""Centralized Anthropic Claude client for structured JSON responses."""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from typing import Any

from anthropic import APIError, AsyncAnthropic

from app.core.config import settings
from app.db.session import get_session_factory
from app.services.ai.ai_client import AiRequestMetadata
from app.services.ai.exceptions import ClaudeNotConfiguredError, ClaudeRequestError
from app.services.ai.usage_service import UsageLogInput, record_usage_log, truncate_preview

logger = logging.getLogger(__name__)

__all__ = [
    "ClaudeNotConfiguredError",
    "ClaudeRequestError",
    "generate_claude_structured_json",
    "is_claude_configured",
]

_JSON_ONLY_INSTRUCTION = (
    "Rispondi esclusivamente con un oggetto JSON valido. "
    "Nessun markdown, nessun blocco ```json, nessun testo prima o dopo."
)
_CLAUDE_MAX_OUTPUT_TOKENS = 4096
_JSON_FENCE_PATTERN = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE)


def is_claude_configured() -> bool:
    return bool(settings.anthropic_api_key and settings.anthropic_api_key.strip())


def _client() -> AsyncAnthropic:
    if not is_claude_configured():
        raise ClaudeNotConfiguredError("ANTHROPIC_API_KEY non configurata")
    return AsyncAnthropic(api_key=settings.anthropic_api_key)


def _hash_prompt(system_prompt: str, user_prompt: str) -> str:
    payload = f"{system_prompt}\n---\n{user_prompt}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _strip_json_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = _JSON_FENCE_PATTERN.sub("", cleaned).strip()
    return cleaned


def _parse_json_object_response(content: str) -> dict[str, Any]:
    cleaned = content.strip()
    if not cleaned:
        raise ClaudeRequestError("Risposta Claude vuota")

    candidates = [cleaned, _strip_json_fences(cleaned)]
    last_error: json.JSONDecodeError | None = None
    for candidate in candidates:
        if not candidate:
            continue
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError as exc:
            last_error = exc
            continue
        if not isinstance(parsed, dict):
            raise ClaudeRequestError("Risposta Claude deve essere un oggetto JSON")
        return parsed

    raise ClaudeRequestError("Risposta Claude non è JSON valido") from last_error


def _extract_text_content(response: Any) -> str:
    content_blocks = getattr(response, "content", None) or []
    parts: list[str] = []
    for block in content_blocks:
        text = getattr(block, "text", None)
        if text:
            parts.append(str(text))
    return "".join(parts).strip()


def _extract_usage(response: Any) -> dict[str, int]:
    usage = getattr(response, "usage", None)
    if usage is None:
        return {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

    input_tokens = int(getattr(usage, "input_tokens", 0) or 0)
    output_tokens = int(getattr(usage, "output_tokens", 0) or 0)
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
    }


def _context_fields_from_metadata(metadata: AiRequestMetadata) -> dict[str, Any]:
    return {
        "context_profile": metadata.context_profile,
        "context_hash": metadata.context_hash,
        "context_chars": metadata.context_chars,
        "context_blocks_used": metadata.context_blocks_used,
    }


async def _persist_log(data: UsageLogInput) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            await record_usage_log(session, data)
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("Failed to persist Claude usage log")


async def generate_claude_structured_json(
    *,
    system_prompt: str,
    user_prompt: str,
    metadata: AiRequestMetadata,
    timeout: float | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    resolved_model = (model or settings.claude_model).strip()
    resolved_timeout = timeout if timeout is not None else settings.claude_timeout_seconds
    effective_system_prompt = f"{system_prompt.strip()}\n\n{_JSON_ONLY_INSTRUCTION}".strip()

    prompt_hash = _hash_prompt(effective_system_prompt, user_prompt)
    prompt_chars = len(effective_system_prompt) + len(user_prompt)
    prompt_preview = None
    if settings.ai_log_prompt_preview:
        prompt_preview = truncate_preview(
            f"[system]\n{effective_system_prompt}\n\n[user]\n{user_prompt}"
        )

    started = time.perf_counter()
    response = None
    content = ""
    parsed: dict[str, Any] | None = None

    try:
        client = _client()
        response = await client.messages.create(
            model=resolved_model,
            max_tokens=_CLAUDE_MAX_OUTPUT_TOKENS,
            system=effective_system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            timeout=resolved_timeout,
        )
        content = _extract_text_content(response)
        parsed = _parse_json_object_response(content)
    except ClaudeNotConfiguredError:
        raise
    except ClaudeRequestError as exc:
        duration_ms = int((time.perf_counter() - started) * 1000)
        await _persist_log(
            UsageLogInput(
                project_id=metadata.project_id,
                provider="claude",
                model=resolved_model,
                module=metadata.module,
                operation=metadata.operation,
                entity_type=metadata.entity_type,
                entity_id=metadata.entity_id,
                job_id=metadata.job_id,
                status="error",
                duration_ms=duration_ms,
                prompt_chars=prompt_chars,
                prompt_hash=prompt_hash,
                prompt_preview=prompt_preview,
                output_chars=len(content),
                output_preview=truncate_preview(content) if settings.ai_log_prompt_preview else None,
                operation_key=metadata.operation_key,
                response_id=getattr(response, "id", None) if response else None,
                error_type=type(exc).__name__,
                error_message=exc.message,
                **_context_fields_from_metadata(metadata),
            )
        )
        raise
    except APIError as exc:
        duration_ms = int((time.perf_counter() - started) * 1000)
        error_message = str(exc).strip().split("\n")[0] or type(exc).__name__
        logger.warning(
            "Claude request failed module=%s operation=%s model=%s error_type=%s error_message=%s",
            metadata.module,
            metadata.operation,
            resolved_model,
            type(exc).__name__,
            error_message,
        )
        await _persist_log(
            UsageLogInput(
                project_id=metadata.project_id,
                provider="claude",
                model=resolved_model,
                module=metadata.module,
                operation=metadata.operation,
                entity_type=metadata.entity_type,
                entity_id=metadata.entity_id,
                job_id=metadata.job_id,
                status="error",
                duration_ms=duration_ms,
                prompt_chars=prompt_chars,
                prompt_hash=prompt_hash,
                prompt_preview=prompt_preview,
                operation_key=metadata.operation_key,
                error_type=type(exc).__name__,
                error_message=error_message,
                **_context_fields_from_metadata(metadata),
            )
        )
        raise ClaudeRequestError(f"Errore AI Claude: {error_message}") from exc

    assert parsed is not None
    duration_ms = int((time.perf_counter() - started) * 1000)
    usage = _extract_usage(response)

    # TODO: Claude pricing in pricing.py
    await _persist_log(
        UsageLogInput(
            project_id=metadata.project_id,
            provider="claude",
            model=resolved_model,
            module=metadata.module,
            operation=metadata.operation,
            entity_type=metadata.entity_type,
            entity_id=metadata.entity_id,
            job_id=metadata.job_id,
            status="success",
            duration_ms=duration_ms,
            input_tokens=usage["input_tokens"],
            output_tokens=usage["output_tokens"],
            total_tokens=usage["total_tokens"],
            prompt_chars=prompt_chars,
            prompt_hash=prompt_hash,
            prompt_preview=prompt_preview,
            output_chars=len(content),
            output_preview=truncate_preview(content) if settings.ai_log_prompt_preview else None,
            operation_key=metadata.operation_key,
            response_id=getattr(response, "id", None),
            requested_model=model,
            **_context_fields_from_metadata(metadata),
        )
    )

    return parsed
