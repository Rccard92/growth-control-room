"""DataForSEO API schemas."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DataForSeoAccountInfo(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    balance_usd: float | None = Field(default=None, serialization_alias="balanceUsd")
    total_deposited_usd: float | None = Field(
        default=None,
        serialization_alias="totalDepositedUsd",
    )


class DataForSeoStatusResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    configured: bool
    real_calls_enabled: bool = Field(serialization_alias="realCallsEnabled")
    missing_vars: list[str] = Field(serialization_alias="missingVars")
    single_run_limit_usd: float = Field(serialization_alias="singleRunLimitUsd")
    daily_budget_usd: float = Field(serialization_alias="dailyBudgetUsd")
    monthly_budget_usd: float = Field(serialization_alias="monthlyBudgetUsd")
    usage_today_usd: float = Field(serialization_alias="usageTodayUsd")
    usage_month_usd: float = Field(serialization_alias="usageMonthUsd")
    account: dict[str, Any] | None = None


class DataForSeoEstimateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    mode: str
    run_id: UUID | None = Field(default=None, serialization_alias="runId")
    product_pages_count: int | None = Field(
        default=None,
        serialization_alias="productPagesCount",
    )
    seed_queries_per_page: int | None = Field(
        default=None,
        serialization_alias="seedQueriesPerPage",
    )
    keyword_ideas_per_seed: int | None = Field(
        default=None,
        serialization_alias="keywordIdeasPerSeed",
    )
    serp_queries_per_page: int | None = Field(
        default=None,
        serialization_alias="serpQueriesPerPage",
    )


class DataForSeoEstimatedCalls(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    search_volume: int = Field(serialization_alias="searchVolume")
    keyword_ideas: int = Field(serialization_alias="keywordIdeas")
    serp: int


class DataForSeoEstimateResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    mode: str
    estimated_calls: DataForSeoEstimatedCalls = Field(serialization_alias="estimatedCalls")
    estimated_cost_usd: float = Field(serialization_alias="estimatedCostUsd")
    assumptions: list[str]
    budget_warnings: list[str] = Field(default_factory=list, serialization_alias="budgetWarnings")
    audit_context: dict[str, Any] | None = Field(default=None, serialization_alias="auditContext")


class DataForSeoTestRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    test_type: str = Field(serialization_alias="testType")
    keyword: str
    location_code: int = Field(default=2380, serialization_alias="locationCode")
    language_code: str = Field(default="it", serialization_alias="languageCode")


class DataForSeoTestResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    test_type: str = Field(serialization_alias="testType")
    keyword: str
    cost_usd: float = Field(serialization_alias="costUsd")
    endpoints: list[str]
    response_summary: dict[str, Any] | None = Field(
        default=None,
        serialization_alias="responseSummary",
    )
    raw_preview: dict[str, Any] | None = Field(default=None, serialization_alias="rawPreview")


class DataForSeoUsageLogRead(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: UUID
    endpoint: str
    operation: str
    status: str
    cost_usd: float | None = Field(serialization_alias="costUsd")
    items_count: int | None = Field(default=None, serialization_alias="itemsCount")
    metadata_json: dict[str, Any] | None = Field(default=None, serialization_alias="metadata")
    response_summary: dict[str, Any] | None = Field(
        default=None,
        serialization_alias="responseSummary",
    )
    error_message: str | None = Field(default=None, serialization_alias="errorMessage")
    created_at: str = Field(serialization_alias="createdAt")


class DataForSeoUsageResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    logs: list[DataForSeoUsageLogRead]
    usage_today_usd: float = Field(serialization_alias="usageTodayUsd")
    usage_month_usd: float = Field(serialization_alias="usageMonthUsd")
    average_cost_by_operation: dict[str, float] = Field(
        serialization_alias="averageCostByOperation",
    )
