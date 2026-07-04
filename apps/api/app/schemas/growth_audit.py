from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


GrowthAuditProvider = Literal["openai", "claude"]
GrowthAuditMode = Literal["full_site_mvp"]
GrowthAuditRunStatus = Literal[
    "pending",
    "queued",
    "discovering",
    "classifying",
    "analyzing",
    "ready_for_analysis",
    "completed",
    "failed",
    "partial_failed",
    "cancelled",
]
GrowthAuditPhase = Literal[
    "queued",
    "discovery",
    "classification",
    "analysis",
    "ready_for_analysis",
    "completed",
    "failed",
]
GrowthAuditPageType = Literal[
    "homepage",
    "product",
    "collection",
    "blog",
    "article",
    "page",
    "policy",
    "cart",
    "checkout",
    "search",
    "account",
    "other",
    "unknown",
]
GrowthAuditPageStatus = Literal[
    "pending",
    "discovered",
    "classified",
    "analyzed",
    "failed",
    "skipped",
]
GrowthAuditPageSource = Literal["seed", "sitemap", "crawl", "manual"]


class GrowthAuditRunCreateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    root_url: str = Field(alias="rootUrl")
    provider: GrowthAuditProvider = "openai"
    audit_mode: GrowthAuditMode = Field(default="full_site_mvp", alias="auditMode")
    max_pages: int = Field(default=50, alias="maxPages")
    include_ai_analysis: bool = Field(default=False, alias="includeAiAnalysis")


class GrowthAuditRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    project_id: UUID = Field(serialization_alias="projectId")
    root_url: str = Field(serialization_alias="rootUrl")
    normalized_domain: str = Field(serialization_alias="normalizedDomain")
    status: str
    phase: str | None = None
    audit_mode: str = Field(serialization_alias="auditMode")
    provider: GrowthAuditProvider
    progress_percent: int = Field(serialization_alias="progressPercent")
    pages_discovered: int = Field(serialization_alias="pagesDiscovered")
    pages_classified: int = Field(serialization_alias="pagesClassified")
    pages_analyzed: int = Field(serialization_alias="pagesAnalyzed")
    pages_failed: int = Field(serialization_alias="pagesFailed")
    total_pages: int | None = Field(default=None, serialization_alias="totalPages")
    current_url: str | None = Field(default=None, serialization_alias="currentUrl")
    config: dict[str, Any] | None = None
    summary: dict[str, Any] | None = None
    site_score: int | None = Field(default=None, serialization_alias="siteScore")
    seo_score: int | None = Field(default=None, serialization_alias="seoScore")
    geo_score: int | None = Field(default=None, serialization_alias="geoScore")
    cro_score: int | None = Field(default=None, serialization_alias="croScore")
    performance_score: int | None = Field(
        default=None,
        serialization_alias="performanceScore",
    )
    error_message: str | None = Field(default=None, serialization_alias="errorMessage")
    started_at: datetime | None = Field(default=None, serialization_alias="startedAt")
    completed_at: datetime | None = Field(default=None, serialization_alias="completedAt")
    created_at: datetime | None = Field(default=None, serialization_alias="createdAt")
    updated_at: datetime | None = Field(default=None, serialization_alias="updatedAt")


class GrowthAuditPageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    run_id: UUID = Field(serialization_alias="runId")
    project_id: UUID = Field(serialization_alias="projectId")
    url: str
    normalized_url: str = Field(serialization_alias="normalizedUrl")
    path: str | None = None
    page_type: str = Field(serialization_alias="pageType")
    source: str
    status: str
    priority: str
    title: str | None = None
    meta_description: str | None = Field(
        default=None,
        serialization_alias="metaDescription",
    )
    canonical_url: str | None = Field(default=None, serialization_alias="canonicalUrl")
    h1: str | None = None
    http_status: int | None = Field(default=None, serialization_alias="httpStatus")
    depth: int | None = None
    score: int | None = None
    seo_score: int | None = Field(default=None, serialization_alias="seoScore")
    geo_score: int | None = Field(default=None, serialization_alias="geoScore")
    cro_score: int | None = Field(default=None, serialization_alias="croScore")
    performance_score: int | None = Field(
        default=None,
        serialization_alias="performanceScore",
    )
    discovered_at: datetime | None = Field(default=None, serialization_alias="discoveredAt")
    classified_at: datetime | None = Field(default=None, serialization_alias="classifiedAt")
    analyzed_at: datetime | None = Field(default=None, serialization_alias="analyzedAt")
    error_message: str | None = Field(default=None, serialization_alias="errorMessage")
    page_metadata: dict[str, Any] | None = Field(
        default=None,
        serialization_alias="metadata",
    )
    created_at: datetime | None = Field(default=None, serialization_alias="createdAt")
    updated_at: datetime | None = Field(default=None, serialization_alias="updatedAt")


class GrowthAuditEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    run_id: UUID = Field(serialization_alias="runId")
    project_id: UUID = Field(serialization_alias="projectId")
    event_type: str = Field(serialization_alias="eventType")
    phase: str | None = None
    message: str
    progress_percent: int | None = Field(
        default=None,
        serialization_alias="progressPercent",
    )
    payload: dict[str, Any] | None = None
    created_at: datetime | None = Field(default=None, serialization_alias="createdAt")


class GrowthAuditRunDetailResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    run: GrowthAuditRunRead
    pages: list[GrowthAuditPageRead]
    events: list[GrowthAuditEventRead]
    findings_count: int = Field(serialization_alias="findingsCount")
    tasks_count: int = Field(serialization_alias="tasksCount")


class GrowthAuditRunsListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    runs: list[GrowthAuditRunRead]


class GrowthAuditPagesListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pages: list[GrowthAuditPageRead]


class GrowthAuditEventsListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    events: list[GrowthAuditEventRead]


class GrowthAuditStartResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    run: GrowthAuditRunRead
