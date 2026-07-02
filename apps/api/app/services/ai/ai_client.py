"""Centralized OpenAI client with usage logging and budget guardrails."""

from __future__ import annotations

import hashlib
import json
import logging
import time
from decimal import Decimal
from typing import Any
from uuid import UUID

from openai import AsyncOpenAI, BadRequestError, OpenAIError
from pydantic import BaseModel, field_validator

from app.core.config import settings
from app.db.session import get_session_factory
from app.services.ai.exceptions import (
    AiBudgetExceededError,
    AiSingleRequestBlockedError,
    OpenAINotConfiguredError,
    OpenAIRequestError,
)
from app.services.ai.model_policy import AiResolvedModel, resolve_ai_model, resolve_standard_fallback
from app.services.ai.model_request_params import build_openai_request_params
from app.services.ai.pricing import estimate_image_cost, estimate_usage_cost
from app.services.ai.usage_service import (
    UsageLogInput,
    check_budget_before_request,
    check_single_request_cost,
    record_usage_log,
    truncate_preview,
)
from app.services.seo_skills.error_messages import (
    OPENAI_EMPTY_RESPONSE_USER_MESSAGE,
    OPENAI_INVALID_JSON_USER_MESSAGE,
)

logger = logging.getLogger(__name__)

__all__ = [
    "AiBudgetExceededError",
    "AiRequestMetadata",
    "AiSingleRequestBlockedError",
    "OpenAINotConfiguredError",
    "OpenAIRequestError",
    "generate_image",
    "generate_structured_json",
    "is_openai_configured",
]


def _coerce_optional_id_to_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


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
    operation_key: str | None = None

    @field_validator("project_id", mode="before")
    @classmethod
    def _coerce_project_id(cls, value: object) -> UUID:
        if isinstance(value, UUID):
            return value
        return UUID(str(value))

    @field_validator("entity_id", "job_id", mode="before")
    @classmethod
    def _coerce_ids_to_string(cls, value: object) -> str | None:
        return _coerce_optional_id_to_str(value)


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
    metadata: AiRequestMetadata,
) -> dict[str, Any]:
    return {
        "model_tier": resolved.tier,
        "model_policy_source": resolved.policy_source,
        "requested_model": requested_model,
        "max_output_tokens": resolved.max_output_tokens,
        "temperature": Decimal(str(resolved.temperature)),
        "reasoning_effort": resolved.reasoning_effort,
        "operation_key": resolved.operation_key or metadata.operation_key,
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
    def __init__(
        self,
        *,
        content: str,
        response: Any | None,
        message: str,
        empty_content: bool = False,
        invalid_json: bool = False,
    ) -> None:
        super().__init__(message)
        self.content = content
        self.response = response
        self.error_message = message
        self.empty_content = empty_content
        self.invalid_json = invalid_json


def _user_message_for_parse_error(parse_exc: _SchemaParseError) -> str:
    if parse_exc.empty_content:
        return OPENAI_EMPTY_RESPONSE_USER_MESSAGE
    if parse_exc.invalid_json:
        return OPENAI_INVALID_JSON_USER_MESSAGE
    return parse_exc.error_message


def _strip_code_fences(content: str) -> str:
    stripped = content.strip()
    if not stripped.startswith("```"):
        return stripped
    lines = stripped.splitlines()
    if len(lines) < 2:
        return stripped
    if lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _extract_json_object_substring(content: str) -> str | None:
    start = content.find("{")
    end = content.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    return content[start : end + 1]


def _try_parse_json_object(content: str) -> dict[str, Any] | None:
    candidates = [content.strip(), _strip_code_fences(content)]
    extracted = _extract_json_object_substring(content)
    if extracted:
        candidates.append(extracted)
    seen: set[str] = set()
    for candidate in candidates:
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


def _log_invalid_json_response(content: str) -> None:
    preview = content[:500]
    if len(content) > 500:
        preview = f"{preview}..."
    logger.warning("OpenAI invalid JSON response preview=%s", preview)


def _log_empty_openai_response(
    *,
    response: Any | None,
    metadata: AiRequestMetadata,
    resolved: AiResolvedModel,
) -> None:
    usage = _extract_usage(response) if response is not None else {}
    logger.warning(
        "OpenAI empty response module=%s operation_key=%s context_profile=%s "
        "model=%s output_tokens=%s",
        metadata.module,
        metadata.operation_key,
        metadata.context_profile,
        resolved.model,
        usage.get("output_tokens", 0),
    )


def _parse_json_object_response(response: Any) -> tuple[dict[str, Any], str]:
    content = (response.choices[0].message.content or "").strip()
    if not content:
        raise _SchemaParseError(
            content=content,
            response=response,
            message="Risposta OpenAI vuota",
            empty_content=True,
        )
    parsed = _try_parse_json_object(content)
    if parsed is None:
        _log_invalid_json_response(content)
        raise _SchemaParseError(
            content=content,
            response=response,
            message="Risposta OpenAI non è JSON valido",
            invalid_json=True,
        )
    return parsed, content


OPENAI_CHAT_COMPLETIONS_ENDPOINT = "chat.completions.create"


def _openai_error_snippet(exc: OpenAIError) -> str:
    body = getattr(exc, "body", None)
    if isinstance(body, dict):
        err = body.get("error")
        if isinstance(err, dict) and err.get("message"):
            return str(err["message"]).split("\n")[0]
    message = str(exc).strip()
    return message.split("\n")[0] if message else type(exc).__name__


def _classify_openai_error(exc: OpenAIError) -> tuple[str, str]:
    snippet = _openai_error_snippet(exc)
    lowered = snippet.lower()
    if "does not exist" in lowered or "model_not_found" in lowered:
        return (
            "access_denied",
            "Il modello è configurato ma la tua API key potrebbe non avere accesso. "
            "Prova un modello diverso o verifica l'account OpenAI.",
        )
    if "access" in lowered and ("denied" in lowered or "permission" in lowered):
        return (
            "access_denied",
            "Il modello è configurato ma la tua API key potrebbe non avere accesso. "
            "Prova un modello diverso o verifica l'account OpenAI.",
        )
    if isinstance(exc, BadRequestError) or "unsupported parameter" in lowered:
        return (
            "model_incompatible",
            f"Errore AI: modello o parametri non compatibili. Dettaglio: {snippet}",
        )
    if "invalid_request" in lowered:
        return (
            "invalid_request",
            f"Errore AI: richiesta non valida. Dettaglio: {snippet}",
        )
    return ("openai_error", f"Errore AI: {snippet}")


def _log_openai_failure(
    *,
    metadata: AiRequestMetadata,
    resolved: AiResolvedModel,
    params: dict[str, Any],
    exc: OpenAIError,
) -> None:
    snippet = _openai_error_snippet(exc)
    logger.warning(
        "OpenAI request failed endpoint=%s operation_key=%s context_profile=%s "
        "resolved_model=%s model_policy_source=%s params_keys=%s error_type=%s error_message=%s",
        OPENAI_CHAT_COMPLETIONS_ENDPOINT,
        resolved.operation_key or metadata.operation_key,
        metadata.context_profile,
        resolved.model,
        resolved.policy_source,
        sorted(k for k in params if k not in ("messages",)),
        type(exc).__name__,
        snippet,
    )


async def _call_openai(
    client: AsyncOpenAI,
    *,
    resolved: AiResolvedModel,
    system_prompt: str,
    user_prompt: str,
    timeout: float,
    json_schema: dict | None = None,
    json_schema_name: str | None = None,
) -> Any:
    kwargs = build_openai_request_params(
        resolved,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        structured_json=True,
        timeout=timeout,
        json_schema=json_schema,
        json_schema_name=json_schema_name,
    )
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
        **_model_policy_fields(resolved, requested_model, metadata),
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
    json_schema: dict | None = None,
    json_schema_name: str | None = None,
) -> dict[str, Any]:
    session_factory = get_session_factory()
    async with session_factory() as session:
        await check_budget_before_request(session, metadata.project_id)
        resolved = await resolve_ai_model(
            session,
            metadata,
            project_id=metadata.project_id,
            context_profile=metadata.context_profile,
            requested_model=model,
        )
        await session.commit()

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

    started = time.perf_counter()
    response = None
    content = ""
    parsed: dict[str, Any] | None = None
    active_resolved = resolved
    schema_retried = False
    last_request_params: dict[str, Any] | None = None

    try:
        client = _client()
        last_request_params = build_openai_request_params(
            active_resolved,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            structured_json=True,
            timeout=timeout,
            json_schema=json_schema,
            json_schema_name=json_schema_name,
        )
        response = await _call_openai(
            client,
            resolved=active_resolved,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            timeout=timeout,
            json_schema=json_schema,
            json_schema_name=json_schema_name,
        )
        try:
            parsed, content = _parse_json_object_response(response)
        except _SchemaParseError as parse_exc:
            if parse_exc.empty_content:
                _log_empty_openai_response(
                    response=parse_exc.response,
                    metadata=metadata,
                    resolved=active_resolved,
                )
            if (
                parse_exc.empty_content
                and metadata.module == "seo_skills"
                and active_resolved.policy_source != "empty_response_retry"
            ):
                async with session_factory() as retry_session:
                    active_resolved = await resolve_standard_fallback(
                        retry_session, metadata.project_id
                    )
                    active_resolved = active_resolved.model_copy(
                        update={"policy_source": "empty_response_retry"}
                    )
                    await retry_session.commit()
                logger.warning(
                    "OpenAI empty response; retry with standard tier (project=%s module=%s)",
                    metadata.project_id,
                    metadata.module,
                )
                response = await _call_openai(
                    client,
                    resolved=active_resolved,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    timeout=timeout,
                    json_schema=json_schema,
                    json_schema_name=json_schema_name,
                )
                last_request_params = build_openai_request_params(
                    active_resolved,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    structured_json=True,
                    timeout=timeout,
                    json_schema=json_schema,
                    json_schema_name=json_schema_name,
                )
                parsed, content = _parse_json_object_response(response)
            elif (
                settings.ai_enable_model_fallback_on_schema_error
                and not parse_exc.empty_content
                and active_resolved.policy_source != "schema_fallback_retry"
            ):
                schema_retried = True
                async with session_factory() as retry_session:
                    active_resolved = await resolve_standard_fallback(
                        retry_session, metadata.project_id
                    )
                    await retry_session.commit()
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
                    json_schema=json_schema,
                    json_schema_name=json_schema_name,
                )
                last_request_params = build_openai_request_params(
                    active_resolved,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    structured_json=True,
                    timeout=timeout,
                    json_schema=json_schema,
                    json_schema_name=json_schema_name,
                )
                parsed, content = _parse_json_object_response(response)
            else:
                raise OpenAIRequestError(
                    _user_message_for_parse_error(parse_exc)
                ) from parse_exc
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
        raise OpenAIRequestError(_user_message_for_parse_error(parse_exc))
    except OpenAIError as exc:
        status = "error"
        error_type = type(exc).__name__
        error_message = _openai_error_snippet(exc)
        error_code, user_message = _classify_openai_error(exc)
        if last_request_params is None:
            last_request_params = build_openai_request_params(
                active_resolved,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                structured_json=True,
                timeout=timeout,
                json_schema=json_schema,
                json_schema_name=json_schema_name,
            )
        _log_openai_failure(
            metadata=metadata,
            resolved=active_resolved,
            params=last_request_params,
            exc=exc,
        )
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
        raise OpenAIRequestError(user_message, code=error_code) from exc

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


async def probe_resolved_model(
    *,
    resolved: AiResolvedModel,
    metadata: AiRequestMetadata,
    timeout: float = 20.0,
) -> dict[str, Any]:
    """Lightweight OpenAI probe for model validation (minimal tokens)."""
    if not is_openai_configured():
        raise OpenAINotConfiguredError("OPENAI_API_KEY non configurata")

    probe_resolved = resolved.model_copy(
        update={"max_output_tokens": min(resolved.max_output_tokens, 32)}
    )
    prompt_hash = _hash_prompt('{"ok":true}', "ping")
    started = time.perf_counter()
    params = build_openai_request_params(
        probe_resolved,
        system_prompt='Rispondi con JSON: {"ok": true}',
        user_prompt="ping",
        structured_json=True,
        timeout=timeout,
    )

    try:
        client = _client()
        response = await _call_openai(
            client,
            resolved=probe_resolved,
            system_prompt='Rispondi con JSON: {"ok": true}',
            user_prompt="ping",
            timeout=timeout,
        )
        parsed, _content = _parse_json_object_response(response)
        duration_ms = int((time.perf_counter() - started) * 1000)
        await _persist_log(
            _base_log_input(
                metadata=metadata,
                resolved=probe_resolved,
                requested_model=resolved.model,
                prompt_hash=prompt_hash,
                prompt_chars=20,
                prompt_preview=None,
                prompt_cache_key=None,
                status="success",
                duration_ms=duration_ms,
                response_id=getattr(response, "id", None),
            )
        )
        return parsed
    except OpenAIError as exc:
        duration_ms = int((time.perf_counter() - started) * 1000)
        error_message = _openai_error_snippet(exc)
        error_code, user_message = _classify_openai_error(exc)
        _log_openai_failure(
            metadata=metadata,
            resolved=probe_resolved,
            params=params,
            exc=exc,
        )
        await _persist_log(
            _base_log_input(
                metadata=metadata,
                resolved=probe_resolved,
                requested_model=resolved.model,
                prompt_hash=prompt_hash,
                prompt_chars=20,
                prompt_preview=None,
                prompt_cache_key=None,
                status="error",
                duration_ms=duration_ms,
                error_type=type(exc).__name__,
                error_message=error_message,
            )
        )
        raise OpenAIRequestError(user_message, code=error_code) from exc


class GenerateImageResult(BaseModel):
    image_bytes: bytes
    model: str
    log_id: str | None = None
    estimated_total_cost: float | None = None


async def generate_image(
    prompt: str,
    *,
    metadata: AiRequestMetadata,
    model: str | None = None,
    size: str = "1536x1024",
    timeout: float = 120.0,
) -> GenerateImageResult:
    """Generate an image via OpenAI Images API and log usage."""
    import base64

    if not is_openai_configured():
        raise OpenAINotConfiguredError("OPENAI_API_KEY non configurata")

    image_model = (model or settings.openai_image_model or "gpt-image-1").strip()
    prompt_text = prompt.strip()
    if not prompt_text:
        raise OpenAIRequestError("Prompt immagine vuoto.")

    resolved = AiResolvedModel(
        model=image_model,
        tier="standard",
        policy_source="image_direct",
        operation_key=metadata.operation_key,
        max_output_tokens=0,
        temperature=0.0,
        reasoning_effort=None,
    )

    session_factory = get_session_factory()
    async with session_factory() as budget_session:
        await check_budget_before_request(budget_session, metadata.project_id)
        await budget_session.commit()

    prompt_hash = _hash_prompt("", prompt_text)
    started = time.perf_counter()
    status = "error"
    error_type: str | None = None
    error_message: str | None = None
    image_bytes = b""
    response_id: str | None = None

    try:
        client = _client()
        response = await client.images.generate(
            model=image_model,
            prompt=prompt_text,
            size=size,
            n=1,
            timeout=timeout,
        )
        if not response.data:
            raise OpenAIRequestError("OpenAI non ha restituito immagini.")
        item = response.data[0]
        b64_data = getattr(item, "b64_json", None)
        if b64_data:
            image_bytes = base64.b64decode(b64_data)
        elif getattr(item, "url", None):
            import httpx

            async with httpx.AsyncClient(timeout=timeout) as http_client:
                fetch = await http_client.get(item.url)
                fetch.raise_for_status()
                image_bytes = fetch.content
        else:
            raise OpenAIRequestError("Formato risposta immagine OpenAI non supportato.")
        status = "success"
        response_id = getattr(response, "created", None)
        if response_id is not None:
            response_id = str(response_id)
    except OpenAINotConfiguredError:
        raise
    except OpenAIError as exc:
        error_type = type(exc).__name__
        error_message = _openai_error_snippet(exc)
        _error_code, user_message = _classify_openai_error(exc)
        duration_ms = int((time.perf_counter() - started) * 1000)
        await _persist_log(
            _base_log_input(
                metadata=metadata,
                resolved=resolved,
                requested_model=model,
                prompt_hash=prompt_hash,
                prompt_chars=len(prompt_text),
                prompt_preview=truncate_preview(prompt_text) if settings.ai_log_prompt_preview else None,
                prompt_cache_key=None,
                status=status,
                duration_ms=duration_ms,
                error_type=error_type,
                error_message=error_message,
            )
        )
        raise OpenAIRequestError(user_message) from exc

    duration_ms = int((time.perf_counter() - started) * 1000)
    estimated_total = estimate_image_cost(image_model, size=size)
    if estimated_total is not None:
        check_single_request_cost(estimated_total)

    log_id: str | None = None
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            log_row = await record_usage_log(
                session,
                _base_log_input(
                    metadata=metadata,
                    resolved=resolved,
                    requested_model=model,
                    prompt_hash=prompt_hash,
                    prompt_chars=len(prompt_text),
                    prompt_preview=truncate_preview(prompt_text)
                    if settings.ai_log_prompt_preview
                    else None,
                    prompt_cache_key=None,
                    status=status,
                    duration_ms=duration_ms,
                    estimated_total_cost=estimated_total,
                    output_chars=len(image_bytes),
                    response_id=response_id,
                ),
            )
            await session.commit()
            log_id = str(log_row.id) if log_row else None
        except Exception:
            await session.rollback()
            logger.exception("Failed to persist AI image usage log")

    return GenerateImageResult(
        image_bytes=image_bytes,
        model=image_model,
        log_id=log_id,
        estimated_total_cost=float(estimated_total) if estimated_total is not None else None,
    )
