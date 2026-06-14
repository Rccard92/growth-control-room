"""Pydantic schemas for AI model settings."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AiModelSettingUpdateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    model: str | None = None
    model_tier: str | None = Field(default=None, serialization_alias="modelTier")
    max_output_tokens: int | None = Field(default=None, serialization_alias="maxOutputTokens")
    temperature: float | None = None
    fallback_model: str | None = Field(default=None, serialization_alias="fallbackModel")
    allow_fallback: bool | None = Field(default=None, serialization_alias="allowFallback")
    enabled: bool | None = None
    notes: str | None = None
    reasoning_effort: str | None = Field(default=None, serialization_alias="reasoningEffort")


class AiModelSettingItemResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    operation_key: str = Field(serialization_alias="operationKey")
    label: str
    status: str
    enabled: bool
    module: str
    context_profile: str = Field(serialization_alias="contextProfile")
    recommended_tier: str = Field(serialization_alias="recommendedTier")
    recommended_model: str | None = Field(default=None, serialization_alias="recommendedModel")
    recommended_max_output_tokens: int = Field(serialization_alias="recommendedMaxOutputTokens")
    recommended_temperature: float = Field(serialization_alias="recommendedTemperature")
    recommended_use: str = Field(serialization_alias="recommendedUse")
    quality_level: str = Field(serialization_alias="qualityLevel")
    cost_sensitivity: str = Field(serialization_alias="costSensitivity")
    description: str
    warning_notes: str | None = Field(default=None, serialization_alias="warningNotes")
    model: str | None = Field(default=None, serialization_alias="model")
    model_tier: str = Field(serialization_alias="modelTier")
    max_output_tokens: int | None = Field(default=None, serialization_alias="maxOutputTokens")
    temperature: float | None = None
    fallback_model: str | None = Field(default=None, serialization_alias="fallbackModel")
    allow_fallback: bool = Field(serialization_alias="allowFallback")
    reasoning_effort: str | None = Field(default=None, serialization_alias="reasoningEffort")
    notes: str | None = None
    source: str
    has_project_override: bool = Field(serialization_alias="hasProjectOverride")
    guardrail_warnings: list[str] = Field(serialization_alias="guardrailWarnings")
    recent_request_count: int = Field(serialization_alias="recentRequestCount")
    avg_cost_recent: float | None = Field(default=None, serialization_alias="avgCostRecent")
    last_request_at: str | None = Field(default=None, serialization_alias="lastRequestAt")
    ui_category: str = Field(serialization_alias="uiCategory")
    gcr_recommended_model: str = Field(serialization_alias="gcrRecommendedModel")
    gcr_recommendation_reason: str = Field(serialization_alias="gcrRecommendationReason")
    cost_profile_label: str = Field(serialization_alias="costProfileLabel")


class AiBulkActionResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    updated_count: int = Field(serialization_alias="updatedCount")
    message: str


class AiAvailableModelItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    pricing_configured: bool = Field(serialization_alias="pricingConfigured")
    source: str


class AiAvailableModelsResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    env_models: dict[str, str | None] = Field(serialization_alias="envModels")
    models: list[AiAvailableModelItem]
    warnings: list[str]


class AiModelSettingsListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: list[AiModelSettingItemResponse]
    registry_count: int = Field(serialization_alias="registryCount")
    missing_settings: list[str] = Field(serialization_alias="missingSettings")
    unpriced_models: list[str] = Field(default_factory=list, serialization_alias="unpricedModels")
    available_models: AiAvailableModelsResponse = Field(serialization_alias="availableModels")


class AiModelSettingMutationResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    operation_key: str = Field(serialization_alias="operationKey")
    model: str
    model_tier: str = Field(serialization_alias="modelTier")
    source: str
    message: str | None = None
