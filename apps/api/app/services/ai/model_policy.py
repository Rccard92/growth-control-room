"""Centralized AI model routing policy."""

from __future__ import annotations

import logging
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services.ai.operation_registry import (
    get_operation,
    infer_operation_key,
    resolve_registry_model,
)

if TYPE_CHECKING:
    from app.services.ai.ai_client import AiRequestMetadata

logger = logging.getLogger(__name__)


class AiModelTier(str, Enum):
    CHEAP = "cheap"
    STANDARD = "standard"
    PREMIUM = "premium"
    REASONING = "reasoning"
    FALLBACK = "fallback"


CHEAP_CONTEXT_PROFILES = frozenset(
    {
        "image_alt",
        "product_seo_field",
        "collection_seo_field",
        "minimal",
        "social_response",
    }
)

PREMIUM_CONTEXT_PROFILES = frozenset({"article_draft"})

PROFILE_PARAMS: dict[str, dict[str, object]] = {
    "image_alt": {"tier": AiModelTier.CHEAP, "max_output_tokens": 120, "temperature": 0.3},
    "product_seo_field": {"tier": AiModelTier.CHEAP, "max_output_tokens": 400, "temperature": 0.35},
    "collection_seo_field": {"tier": AiModelTier.CHEAP, "max_output_tokens": 400, "temperature": 0.35},
    "minimal": {"tier": AiModelTier.CHEAP, "max_output_tokens": 500, "temperature": 0.3},
    "social_response": {"tier": AiModelTier.CHEAP, "max_output_tokens": 600, "temperature": 0.4},
    "product_seo_full": {"tier": AiModelTier.STANDARD, "max_output_tokens": 2500, "temperature": 0.45},
    "collection_seo_full": {"tier": AiModelTier.STANDARD, "max_output_tokens": 2500, "temperature": 0.45},
    "blog_brief": {"tier": AiModelTier.STANDARD, "max_output_tokens": 3000, "temperature": 0.5},
    "brand_import": {"tier": AiModelTier.STANDARD, "max_output_tokens": 4500, "temperature": 0.4},
    "generic": {"tier": AiModelTier.STANDARD, "max_output_tokens": 2000, "temperature": 0.45},
    "article_draft": {"tier": AiModelTier.PREMIUM, "max_output_tokens": 8000, "temperature": 0.55},
    "compliance_review": {
        "tier": AiModelTier.STANDARD,
        "max_output_tokens": 1500,
        "temperature": 0.2,
        "reasoning_if_available": True,
    },
    "seo_skill_audit": {
        "tier": AiModelTier.STANDARD,
        "max_output_tokens": 6000,
        "temperature": 0.3,
    },
}


class AiModelPolicyRule(BaseModel):
    module: str | None = None
    operation: str | None = None
    context_profile: str | None = None
    entity_type: str | None = None
    tier: AiModelTier
    default_model: str | None = None
    max_output_tokens: int | None = None
    temperature: float | None = None
    reasoning_effort: str | None = None
    notes: str | None = None


class AiResolvedModel(BaseModel):
    model: str
    tier: str
    max_output_tokens: int
    temperature: float
    reasoning_effort: str | None = None
    fallback_model: str | None = None
    operation_key: str | None = None
    policy_source: str
    warning: str | None = None

    model_config = {"populate_by_name": True}


def tier_to_model_name(tier: AiModelTier) -> str | None:
    if tier == AiModelTier.CHEAP:
        raw = settings.openai_model_cheap or settings.openai_model
    elif tier == AiModelTier.STANDARD:
        raw = settings.openai_model_standard or settings.openai_model
    elif tier == AiModelTier.PREMIUM:
        raw = settings.openai_model_premium or "gpt-4o"
    elif tier == AiModelTier.REASONING:
        raw = settings.openai_model_reasoning
    else:
        raw = settings.openai_model_fallback or settings.openai_model_standard or settings.openai_model
    if raw and str(raw).strip():
        return str(raw).strip()
    return None


def infer_tier_from_model(model_name: str) -> AiModelTier:
    normalized = model_name.strip().lower()
    cheap = (settings.openai_model_cheap or settings.openai_model or "").strip().lower()
    standard = (settings.openai_model_standard or settings.openai_model or "").strip().lower()
    premium = (settings.openai_model_premium or "gpt-4o").strip().lower()
    reasoning = (settings.openai_model_reasoning or "").strip().lower()
    fallback = (
        settings.openai_model_fallback or settings.openai_model_standard or settings.openai_model or ""
    ).strip().lower()
    if premium and normalized == premium:
        return AiModelTier.PREMIUM
    if reasoning and normalized == reasoning:
        return AiModelTier.REASONING
    if cheap and normalized == cheap:
        return AiModelTier.CHEAP
    if standard and normalized == standard:
        return AiModelTier.STANDARD
    if fallback and normalized == fallback:
        return AiModelTier.FALLBACK
    if normalized in ("gpt-4o", "gpt-4.1", "gpt-4"):
        return AiModelTier.PREMIUM
    if "mini" in normalized or "nano" in normalized:
        return AiModelTier.CHEAP
    return AiModelTier.STANDARD


def _resolve_compliance_tier() -> AiModelTier:
    if settings.openai_model_reasoning and str(settings.openai_model_reasoning).strip():
        return AiModelTier.REASONING
    return AiModelTier.STANDARD


def _profile_tier(profile: str | None) -> AiModelTier:
    if not profile:
        return AiModelTier.STANDARD
    params = PROFILE_PARAMS.get(profile)
    if not params:
        return AiModelTier.STANDARD
    tier = params["tier"]
    if profile == "compliance_review" and params.get("reasoning_if_available"):
        return _resolve_compliance_tier()
    assert isinstance(tier, AiModelTier)
    return tier


def _profile_params(profile: str | None) -> dict[str, object]:
    if profile and profile in PROFILE_PARAMS:
        return PROFILE_PARAMS[profile]
    return PROFILE_PARAMS["generic"]


def _legacy_fallback_model() -> str | None:
    if settings.openai_model_fallback and str(settings.openai_model_fallback).strip():
        return str(settings.openai_model_fallback).strip()
    if settings.openai_model and str(settings.openai_model).strip():
        return str(settings.openai_model).strip()
    return None


def _resolve_from_registry(operation_key: str) -> AiResolvedModel | None:
    op = get_operation(operation_key)
    if op is None:
        return None
    tier = AiModelTier(op.recommended_tier)
    model = resolve_registry_model(op) or tier_to_model_name(tier)
    if not model:
        return None
    return AiResolvedModel(
        model=model,
        tier=tier.value,
        max_output_tokens=op.recommended_max_output_tokens,
        temperature=op.recommended_temperature,
        reasoning_effort="low" if op.module == "seo_skills" else None,
        fallback_model=_legacy_fallback_model(),
        operation_key=operation_key,
        policy_source="registry_default",
        warning=None,
    )


async def resolve_standard_fallback(
    session: AsyncSession,
    project_id: UUID,
) -> AiResolvedModel:
    from app.services.ai.model_settings_service import (
        get_effective_setting_with_source,
        seed_default_settings,
    )

    """Resolve standard tier for schema-error retry."""
    await seed_default_settings(session, project_id=None, source="env_seed")
    setting = await get_effective_setting_with_source(session, project_id, "blog_brief_generation")
    if setting[0] and setting[0].enabled:
        row = setting[0]
        return AiResolvedModel(
            model=row.model,
            tier=row.model_tier,
            max_output_tokens=row.max_output_tokens or 2000,
            temperature=float(row.temperature or 0.45),
            reasoning_effort=row.reasoning_effort,
            fallback_model=row.fallback_model,
            operation_key="blog_brief_generation",
            policy_source="schema_fallback_retry",
            warning=None,
        )
    params = PROFILE_PARAMS["generic"]
    tier = AiModelTier.STANDARD
    model = tier_to_model_name(tier) or _legacy_fallback_model()
    if not model:
        raise ValueError("Nessun modello AI disponibile per schema fallback")
    return AiResolvedModel(
        model=model,
        tier=tier.value,
        max_output_tokens=int(params["max_output_tokens"]),
        temperature=float(params["temperature"]),
        fallback_model=_legacy_fallback_model(),
        operation_key=None,
        policy_source="schema_fallback_retry",
        warning=None,
    )


def _resolve_operation_key(
    metadata: AiRequestMetadata,
    *,
    context_profile: str | None,
    operation_key: str | None,
) -> tuple[str | None, list[str]]:
    warnings: list[str] = []
    if operation_key:
        return operation_key, warnings
    if metadata.operation_key:
        return metadata.operation_key, warnings
    inferred = infer_operation_key(
        metadata.module,
        metadata.operation,
        context_profile or metadata.context_profile,
        metadata.entity_type,
    )
    if inferred:
        warnings.append(f"operation_key mancante; inferito '{inferred}'")
        return inferred, warnings
    warnings.append("operation_key mancante e non inferibile")
    return None, warnings


async def resolve_ai_model(
    session: AsyncSession,
    metadata: AiRequestMetadata,
    *,
    project_id: UUID,
    context_profile: str | None = None,
    operation_key: str | None = None,
    requested_model: str | None = None,
    task_complexity: str | None = None,
) -> AiResolvedModel:
    del task_complexity
    from app.services.ai.model_settings_service import (
        compute_guardrail_warnings,
        get_effective_setting_with_source,
        seed_default_settings,
    )

    profile = context_profile or metadata.context_profile
    warnings: list[str] = []

    resolved_key, key_warnings = _resolve_operation_key(
        metadata,
        context_profile=profile,
        operation_key=operation_key,
    )
    warnings.extend(key_warnings)
    if resolved_key:
        for w in key_warnings:
            logger.warning("AI routing: %s (project=%s module=%s)", w, project_id, metadata.module)

    await seed_default_settings(session, project_id=None, source="env_seed")

    if requested_model and str(requested_model).strip() and settings.ai_allow_model_override:
        model = str(requested_model).strip()
        tier = infer_tier_from_model(model).value
        params = _profile_params(profile)
        op = get_operation(resolved_key) if resolved_key else None
        guardrails = compute_guardrail_warnings(op, model_tier=tier, model_name=model) if op else []
        warnings.extend(guardrails)
        return AiResolvedModel(
            model=model,
            tier=tier,
            max_output_tokens=int(params.get("max_output_tokens", 2000)),
            temperature=float(params.get("temperature", 0.45)),
            operation_key=resolved_key,
            policy_source="explicit_override",
            fallback_model=_legacy_fallback_model(),
            warning="; ".join(warnings) if warnings else None,
        )

    if resolved_key:
        setting_row, source = await get_effective_setting_with_source(
            session, project_id, resolved_key
        )
        if setting_row is not None and source:
            op = get_operation(resolved_key)
            guardrails = compute_guardrail_warnings(
                op,
                model_tier=setting_row.model_tier,
                model_name=setting_row.model,
            )
            warnings.extend(guardrails)
            return AiResolvedModel(
                model=setting_row.model,
                tier=setting_row.model_tier,
                max_output_tokens=setting_row.max_output_tokens or 2000,
                temperature=float(setting_row.temperature or 0.45),
                reasoning_effort=setting_row.reasoning_effort,
                fallback_model=setting_row.fallback_model,
                operation_key=resolved_key,
                policy_source=source,
                warning="; ".join(warnings) if warnings else None,
            )

    if resolved_key:
        registry_resolved = _resolve_from_registry(resolved_key)
        if registry_resolved:
            op = get_operation(resolved_key)
            guardrails = compute_guardrail_warnings(
                op,
                model_tier=registry_resolved.tier,
                model_name=registry_resolved.model,
            )
            warnings.extend(guardrails)
            if (
                resolved_key.startswith("claude_seo_")
                and not registry_resolved.reasoning_effort
            ):
                registry_resolved = registry_resolved.model_copy(
                    update={"reasoning_effort": "low"}
                )
            registry_resolved.warning = "; ".join(warnings) if warnings else None
            return registry_resolved

    tier = _profile_tier(profile)
    params = _profile_params(profile)
    model = tier_to_model_name(tier)
    policy_source = "env_fallback"
    if not model:
        model = _legacy_fallback_model()
        policy_source = "legacy_openai_model"
    if not model:
        raise ValueError(
            "Nessun modello AI configurato. Imposta AI Model Settings o variabili env tier."
        )

    op = get_operation(resolved_key) if resolved_key else None
    guardrails = compute_guardrail_warnings(op, model_tier=tier.value, model_name=model) if op else []
    warnings.extend(guardrails)

    return AiResolvedModel(
        model=model,
        tier=tier.value,
        max_output_tokens=int(params["max_output_tokens"]),
        temperature=float(params["temperature"]),
        fallback_model=_legacy_fallback_model(),
        operation_key=resolved_key,
        policy_source=policy_source,
        warning="; ".join(warnings) if warnings else None,
    )
