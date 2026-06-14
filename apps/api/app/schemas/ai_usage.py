"""Pydantic schemas for AI usage monitoring."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AiUsageBreakdownItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    key: str | None = None
    date: str | None = None
    requests: int
    estimated_cost: float = Field(serialization_alias="estimatedCost")
    input_tokens: int | None = Field(default=None, serialization_alias="inputTokens")


class AiRoutingInsights(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    cost_by_tier: dict[str, float] = Field(serialization_alias="costByTier")
    requests_by_tier: dict[str, int] = Field(serialization_alias="requestsByTier")
    premium_on_cheap_profile_count: int = Field(serialization_alias="premiumOnCheapProfileCount")
    explicit_override_count: int = Field(serialization_alias="explicitOverrideCount")
    unconfigured_model_warnings: list[str] = Field(serialization_alias="unconfiguredModelWarnings")
    schema_fallback_retry_count: int = Field(serialization_alias="schemaFallbackRetryCount")


class AiUsageSummaryResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    total_estimated_cost: float = Field(serialization_alias="totalEstimatedCost")
    total_requests: int = Field(serialization_alias="totalRequests")
    successful_requests: int = Field(serialization_alias="successfulRequests")
    failed_requests: int = Field(serialization_alias="failedRequests")
    total_input_tokens: int = Field(serialization_alias="totalInputTokens")
    total_output_tokens: int = Field(serialization_alias="totalOutputTokens")
    total_cached_input_tokens: int = Field(serialization_alias="totalCachedInputTokens")
    by_module: list[AiUsageBreakdownItem] = Field(serialization_alias="byModule")
    by_operation: list[AiUsageBreakdownItem] = Field(serialization_alias="byOperation")
    by_model: list[AiUsageBreakdownItem] = Field(serialization_alias="byModel")
    by_tier: list[AiUsageBreakdownItem] = Field(default_factory=list, serialization_alias="byTier")
    by_day: list[AiUsageBreakdownItem] = Field(serialization_alias="byDay")
    routing_insights: AiRoutingInsights | None = Field(
        default=None, serialization_alias="routingInsights"
    )
    project_count: int | None = Field(default=None, serialization_alias="projectCount")


class AiUsageLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    project_id: UUID | None = Field(serialization_alias="projectId")
    provider: str
    model: str
    module: str
    operation: str
    entity_type: str | None = Field(serialization_alias="entityType")
    entity_id: str | None = Field(serialization_alias="entityId")
    job_id: str | None = Field(serialization_alias="jobId")
    status: str
    input_tokens: int = Field(serialization_alias="inputTokens")
    output_tokens: int = Field(serialization_alias="outputTokens")
    total_tokens: int = Field(serialization_alias="totalTokens")
    cached_input_tokens: int = Field(serialization_alias="cachedInputTokens")
    reasoning_tokens: int = Field(serialization_alias="reasoningTokens")
    estimated_input_cost: float | None = Field(serialization_alias="estimatedInputCost")
    estimated_output_cost: float | None = Field(serialization_alias="estimatedOutputCost")
    estimated_cached_cost: float | None = Field(serialization_alias="estimatedCachedCost")
    estimated_total_cost: float | None = Field(serialization_alias="estimatedTotalCost")
    duration_ms: int | None = Field(serialization_alias="durationMs")
    prompt_chars: int | None = Field(serialization_alias="promptChars")
    output_chars: int | None = Field(serialization_alias="outputChars")
    prompt_hash: str | None = Field(serialization_alias="promptHash")
    prompt_preview: str | None = Field(serialization_alias="promptPreview")
    output_preview: str | None = Field(serialization_alias="outputPreview")
    prompt_cache_key: str | None = Field(serialization_alias="promptCacheKey")
    context_profile: str | None = Field(default=None, serialization_alias="contextProfile")
    context_hash: str | None = Field(default=None, serialization_alias="contextHash")
    context_chars: int | None = Field(default=None, serialization_alias="contextChars")
    context_blocks_used: list[str] | None = Field(
        default=None, serialization_alias="contextBlocksUsed"
    )
    model_tier: str | None = Field(default=None, serialization_alias="modelTier")
    model_policy_source: str | None = Field(default=None, serialization_alias="modelPolicySource")
    requested_model: str | None = Field(default=None, serialization_alias="requestedModel")
    max_output_tokens: int | None = Field(default=None, serialization_alias="maxOutputTokens")
    temperature: float | None = None
    reasoning_effort: str | None = Field(default=None, serialization_alias="reasoningEffort")
    response_id: str | None = Field(serialization_alias="responseId")
    error_type: str | None = Field(serialization_alias="errorType")
    error_message: str | None = Field(serialization_alias="errorMessage")
    created_at: datetime = Field(serialization_alias="createdAt")


class AiUsageLogListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: list[AiUsageLogRead]
    total: int
    limit: int
    offset: int


class AiBudgetStatusResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    daily_spent: float = Field(serialization_alias="dailySpent")
    monthly_spent: float = Field(serialization_alias="monthlySpent")
    daily_budget_usd: float | None = Field(serialization_alias="dailyBudgetUsd")
    monthly_budget_usd: float | None = Field(serialization_alias="monthlyBudgetUsd")
    near_limit: bool = Field(serialization_alias="nearLimit")
    blocked: bool


class AiUsageEstimateResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    operation: str
    count: int
    estimated_total_cost: float | None = Field(serialization_alias="estimatedTotalCost")
    avg_cost_per_request: float | None = Field(serialization_alias="avgCostPerRequest")
    based_on_requests: int = Field(serialization_alias="basedOnRequests")
    message: str | None = None
