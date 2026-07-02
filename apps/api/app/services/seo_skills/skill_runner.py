"""Execute a single prompt-only SEO skill via the AI provider router."""

from __future__ import annotations

import hashlib
import logging
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.seo_skills import SeoSkillCatalogItem
from app.services.ai.ai_client import AiRequestMetadata
from app.services.ai.context_profiles import build_prompt_cache_key
from app.services.ai.exceptions import ClaudeNotConfiguredError, ClaudeRequestError, OpenAIRequestError
from app.services.ai.operation_registry import get_operation_key_for_seo_skill
from app.services.ai.provider_router import generate_structured_json_with_provider
from app.services.seo_skills.catalog_loader import get_seo_skill_by_key
from app.services.seo_skills.error_messages import humanize_skill_error
from app.services.seo_skills.exceptions import (
    SeoSkillNotAvailableError,
    SeoSkillProviderError,
    SeoSkillRunnerError,
    SkillInputCollectionError,
)
from app.services.seo_skills.input_collector import collect_skill_input
from app.services.seo_skills.output_schema import normalize_skill_output
from app.services.seo_skills.prompt_builder import (
    build_skill_system_prompt,
    build_skill_user_prompt,
)

logger = logging.getLogger(__name__)

SUPPORTED_PROVIDERS = frozenset({"openai", "claude"})
SKILL_RUN_TIMEOUT_SECONDS = 90.0


def _resolve_operation_key(skill_key: str) -> str:
    try:
        return get_operation_key_for_seo_skill(skill_key)
    except ValueError:
        return f"claude_{skill_key}"


def _validate_skill(skill_key: str) -> SeoSkillCatalogItem:
    skill = get_seo_skill_by_key(skill_key)
    if skill is None:
        raise SeoSkillNotAvailableError(f"Unknown SEO skill: {skill_key}")

    if not skill.enabled:
        raise SeoSkillNotAvailableError(f"SEO skill is disabled: {skill_key}")

    if skill.status != "available":
        status_messages = {
            "needs_config": f"SEO skill requires additional configuration: {skill_key}",
            "external_required": f"SEO skill requires an external integration: {skill_key}",
            "planned": f"SEO skill is planned but not implemented yet: {skill_key}",
        }
        raise SeoSkillNotAvailableError(
            status_messages.get(
                skill.status,
                f"SEO skill is not available: {skill_key}",
            )
        )

    if skill.runtime != "prompt_only":
        raise SeoSkillNotAvailableError(
            f"SEO skill runtime is not supported yet: {skill_key}"
        )

    return skill


def _validate_provider(provider: str) -> str:
    normalized = (provider or "").strip().lower()
    if normalized not in SUPPORTED_PROVIDERS:
        raise SeoSkillProviderError(
            f"Unsupported AI provider for SEO skill: {provider}"
        )
    return normalized


def _build_prompt_cache_key(
    *,
    project_id: UUID,
    provider: str,
    skill_key: str,
    target_type: str,
    target_id: UUID | None,
    url: str | None,
) -> str | None:
    if provider != "openai":
        return None
    cache_seed = "|".join(
        [
            skill_key,
            target_type,
            str(target_id or ""),
            url or "",
        ]
    )
    context_hash = hashlib.sha256(cache_seed.encode("utf-8")).hexdigest()[:16]
    return build_prompt_cache_key(project_id, "seo_skills", context_hash)


def _build_ai_metadata(
    *,
    project_id: UUID,
    operation_key: str,
    target_type: str,
    target_id: UUID | None,
    run_id: UUID | None,
) -> AiRequestMetadata:
    return AiRequestMetadata(
        project_id=project_id,
        module="seo_skills",
        operation="run_skill",
        operation_key=operation_key,
        entity_type=target_type,
        entity_id=str(target_id) if target_id else None,
        job_id=str(run_id) if run_id else None,
        context_profile="seo_skill_audit",
    )


def _merge_warnings(*warning_groups: list[str] | None) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for group in warning_groups:
        if not group:
            continue
        for warning in group:
            text = str(warning).strip()
            if not text or text in seen:
                continue
            seen.add(text)
            merged.append(text)
    return merged


def _build_final_output(
    *,
    skill_key: str,
    provider: str,
    operation_key: str,
    target_type: str,
    target_id: UUID | None,
    skill_input: dict[str, Any],
    normalized_output: dict[str, Any],
    raw_output: dict[str, Any],
) -> dict[str, Any]:
    input_warnings = skill_input.get("warnings")
    input_warning_list = (
        [str(item) for item in input_warnings if str(item).strip()]
        if isinstance(input_warnings, list)
        else []
    )
    return {
        "skillKey": skill_key,
        "provider": provider,
        "operationKey": operation_key,
        "targetType": target_type,
        "targetId": str(target_id) if target_id else skill_input.get("targetId") or "",
        "url": skill_input.get("url") or "",
        "summary": normalized_output.get("summary", ""),
        "score": normalized_output.get("score"),
        "findings": normalized_output.get("findings", []),
        "recommendations": normalized_output.get("recommendations", []),
        "tasks": normalized_output.get("tasks", []),
        "artifacts": normalized_output.get("artifacts", {}),
        "warnings": _merge_warnings(input_warning_list, normalized_output.get("warnings")),
        "rawOutput": raw_output,
    }


async def run_single_seo_skill(
    session: AsyncSession,
    project_id: UUID,
    skill_key: str,
    target_type: str,
    *,
    target_id: UUID | None = None,
    url: str | None = None,
    provider: str = "claude",
    run_id: UUID | None = None,
) -> dict[str, Any]:
    skill = _validate_skill(skill_key)
    normalized_provider = _validate_provider(provider)
    operation_key = _resolve_operation_key(skill_key)

    logger.info(
        "Running SEO skill project_id=%s skill_key=%s provider=%s target_type=%s run_id=%s",
        project_id,
        skill_key,
        normalized_provider,
        target_type,
        run_id,
    )

    try:
        skill_input = await collect_skill_input(
            session=session,
            project_id=project_id,
            target_type=target_type,
            target_id=target_id,
            url=url,
        )
    except SkillInputCollectionError as exc:
        raise SeoSkillRunnerError(str(exc)) from exc

    system_prompt = build_skill_system_prompt(skill, skill_input)
    user_prompt = build_skill_user_prompt(skill, skill_input)
    metadata = _build_ai_metadata(
        project_id=project_id,
        operation_key=operation_key,
        target_type=target_type,
        target_id=target_id,
        run_id=run_id,
    )
    prompt_cache_key = _build_prompt_cache_key(
        project_id=project_id,
        provider=normalized_provider,
        skill_key=skill_key,
        target_type=target_type,
        target_id=target_id,
        url=url,
    )

    try:
        raw_output = await generate_structured_json_with_provider(
            provider=normalized_provider,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            metadata=metadata,
            timeout=SKILL_RUN_TIMEOUT_SECONDS,
            model=None,
            prompt_cache_key=prompt_cache_key,
        )
    except (
        ValueError,
        OpenAIRequestError,
        ClaudeRequestError,
        ClaudeNotConfiguredError,
    ) as exc:
        logger.warning(
            "SEO skill provider error project_id=%s skill_key=%s provider=%s run_id=%s error=%s",
            project_id,
            skill_key,
            normalized_provider,
            run_id,
            exc,
        )
        raise SeoSkillProviderError(
            humanize_skill_error(exc, provider=normalized_provider)
        ) from exc

    if not isinstance(raw_output, dict):
        raise SeoSkillRunnerError("SEO skill provider returned a non-object JSON response")

    normalized_output = normalize_skill_output(skill_key, raw_output)
    return _build_final_output(
        skill_key=skill_key,
        provider=normalized_provider,
        operation_key=operation_key,
        target_type=target_type,
        target_id=target_id,
        skill_input=skill_input,
        normalized_output=normalized_output,
        raw_output=raw_output,
    )
