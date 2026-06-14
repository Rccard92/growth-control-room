"""Centralized AI model routing policy."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from app.core.config import settings

if TYPE_CHECKING:
    from app.services.ai.ai_client import AiRequestMetadata


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
    tier: str = Field(serialization_alias="tier")
    max_output_tokens: int
    temperature: float
    reasoning_effort: str | None = None
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


def resolve_standard_fallback() -> AiResolvedModel:
    """Resolve standard tier for schema-error retry."""
    tier = AiModelTier.STANDARD
    model = tier_to_model_name(tier) or settings.openai_model
    params = PROFILE_PARAMS["generic"]
    return AiResolvedModel(
        model=model,
        tier=tier.value,
        max_output_tokens=int(params["max_output_tokens"]),
        temperature=float(params["temperature"]),
        policy_source="schema_fallback_retry",
        warning=None,
    )


def resolve_ai_model(
    metadata: AiRequestMetadata,
    *,
    context_profile: str | None = None,
    requested_model: str | None = None,
    task_complexity: str | None = None,
) -> AiResolvedModel:
    del task_complexity  # reserved for future complexity hints

    profile = context_profile or metadata.context_profile
    warnings: list[str] = []
    policy_source = "context_profile"
    tier = _profile_tier(profile)
    params = _profile_params(profile)

    if requested_model and str(requested_model).strip():
        if settings.ai_allow_model_override:
            model = str(requested_model).strip()
            inferred = infer_tier_from_model(model)
            expected = _profile_tier(profile)
            policy_source = "explicit_override"
            if expected == AiModelTier.CHEAP and inferred in (
                AiModelTier.PREMIUM,
                AiModelTier.REASONING,
            ):
                warnings.append(
                    f"Override premium/reasoning su profilo cheap ({profile or 'unknown'})"
                )
            tier = inferred
            max_tokens = int(params.get("max_output_tokens", 2000))
            temperature = float(params.get("temperature", 0.45))
        else:
            warnings.append("Model override ignorato: AI_ALLOW_MODEL_OVERRIDE=false")
            model = tier_to_model_name(tier) or settings.openai_model
            max_tokens = int(params["max_output_tokens"])
            temperature = float(params["temperature"])
            policy_source = "context_profile"
    else:
        model = tier_to_model_name(tier)
        if not model:
            fallback_tier = AiModelTier.FALLBACK
            model = tier_to_model_name(fallback_tier) or settings.openai_model
            warnings.append(f"Modello non configurato per tier {tier.value}; uso fallback")
            tier = fallback_tier
            policy_source = "fallback"
        max_tokens = int(params["max_output_tokens"])
        temperature = float(params["temperature"])

    reasoning_effort: str | None = None
    if tier == AiModelTier.REASONING and settings.openai_model_reasoning:
        reasoning_effort = "medium"
    elif params.get("reasoning_if_available") and tier != AiModelTier.REASONING:
        pass

    if not profile:
        policy_source = "fallback"

    return AiResolvedModel(
        model=model,
        tier=tier.value,
        max_output_tokens=max_tokens,
        temperature=temperature,
        reasoning_effort=reasoning_effort,
        policy_source=policy_source,
        warning="; ".join(warnings) if warnings else None,
    )
