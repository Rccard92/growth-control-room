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
    "technical_scan",
    "ready_for_analysis",
    "finalization",
    "completed",
    "failed",
]
GrowthAuditPageType = Literal[
    "homepage",
    "product",
    "collection",
    "blog",
    "blog_article",
    "article",
    "static_page",
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
    "analyzing",
    "analyzed",
    "failed",
    "skipped",
]
GrowthAuditPageSource = Literal[
    "seed",
    "sitemap",
    "shopify_product",
    "shopify_collection",
    "shopify_page",
    "shopify_blog",
    "crawl",
    "manual",
]


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
    source_entity_type: str | None = Field(
        default=None,
        serialization_alias="sourceEntityType",
    )
    source_entity_id: UUID | None = Field(
        default=None,
        serialization_alias="sourceEntityId",
    )
    source_entity_gid: str | None = Field(
        default=None,
        serialization_alias="sourceEntityGid",
    )
    source_entity_handle: str | None = Field(
        default=None,
        serialization_alias="sourceEntityHandle",
    )
    source_entity_title: str | None = Field(
        default=None,
        serialization_alias="sourceEntityTitle",
    )
    source_entity_synced_at: datetime | None = Field(
        default=None,
        serialization_alias="sourceEntitySyncedAt",
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


class GrowthAuditFindingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    run_id: UUID = Field(serialization_alias="runId")
    page_id: UUID | None = Field(default=None, serialization_alias="pageId")
    project_id: UUID = Field(serialization_alias="projectId")
    source_result_id: UUID | None = Field(
        default=None,
        serialization_alias="sourceResultId",
    )
    category: str
    severity: str
    priority: str
    title: str
    description: str | None = None
    evidence: str | None = None
    recommendation: str | None = None
    how_to_validate: str | None = Field(
        default=None,
        serialization_alias="howToValidate",
    )
    impact: str | None = None
    effort: str | None = None
    status: str
    finding_metadata: dict[str, Any] | None = Field(
        default=None,
        serialization_alias="metadata",
    )
    created_at: datetime | None = Field(default=None, serialization_alias="createdAt")
    updated_at: datetime | None = Field(default=None, serialization_alias="updatedAt")


class GrowthAuditTaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    run_id: UUID = Field(serialization_alias="runId")
    page_id: UUID | None = Field(default=None, serialization_alias="pageId")
    finding_id: UUID | None = Field(default=None, serialization_alias="findingId")
    project_id: UUID = Field(serialization_alias="projectId")
    title: str
    description: str | None = None
    owner_type: str = Field(serialization_alias="ownerType")
    priority: str
    estimated_effort: str = Field(serialization_alias="estimatedEffort")
    status: str
    task_metadata: dict[str, Any] | None = Field(
        default=None,
        serialization_alias="metadata",
    )
    completed_at: datetime | None = Field(default=None, serialization_alias="completedAt")
    created_at: datetime | None = Field(default=None, serialization_alias="createdAt")
    updated_at: datetime | None = Field(default=None, serialization_alias="updatedAt")


class GrowthAuditFindingsListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    findings: list[GrowthAuditFindingRead]


class GrowthAuditTasksListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    tasks: list[GrowthAuditTaskRead]


class GrowthAuditPageRescanRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    clear_previous_open_items: bool = Field(
        default=True,
        alias="clearPreviousOpenItems",
    )
    note: str | None = None


class GrowthAuditPageRescanResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    run: GrowthAuditRunRead
    page: GrowthAuditPageRead
    findings_count: int = Field(serialization_alias="findingsCount")
    tasks_count: int = Field(serialization_alias="tasksCount")
    message: str


GrowthAuditAiAnalysisDepth = Literal["standard", "deep"]


class GrowthAuditPageResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    run_id: UUID = Field(serialization_alias="runId")
    page_id: UUID = Field(serialization_alias="pageId")
    project_id: UUID = Field(serialization_alias="projectId")
    result_type: str = Field(serialization_alias="resultType")
    skill_key: str | None = Field(default=None, serialization_alias="skillKey")
    status: str
    score: int | None = None
    summary: str | None = None
    findings: list[Any] | None = None
    recommendations: list[Any] | None = None
    tasks: list[Any] | None = None
    artifacts: dict[str, Any] | None = None
    raw_output: dict[str, Any] | None = Field(default=None, serialization_alias="rawOutput")
    error_message: str | None = Field(default=None, serialization_alias="errorMessage")
    started_at: datetime | None = Field(default=None, serialization_alias="startedAt")
    completed_at: datetime | None = Field(default=None, serialization_alias="completedAt")
    created_at: datetime | None = Field(default=None, serialization_alias="createdAt")
    updated_at: datetime | None = Field(default=None, serialization_alias="updatedAt")


class GrowthAuditPageAiAnalysisRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    provider: GrowthAuditProvider = "openai"
    depth: GrowthAuditAiAnalysisDepth = "standard"
    include_seo: bool = Field(default=True, alias="includeSeo")
    include_geo: bool = Field(default=True, alias="includeGeo")
    include_cro: bool = Field(default=True, alias="includeCro")
    include_ads_readiness: bool = Field(default=True, alias="includeAdsReadiness")
    note: str | None = None


class GrowthAuditPageAiAnalysisResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    run: GrowthAuditRunRead
    page: GrowthAuditPageRead
    result: GrowthAuditPageResultRead
    findings_count: int = Field(serialization_alias="findingsCount")
    tasks_count: int = Field(serialization_alias="tasksCount")
    message: str


class GrowthAuditPagePerformanceAnalysisRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    strategy: Literal["mobile", "desktop"] = "mobile"


class GrowthAuditPagePerformanceAnalysisResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    run: GrowthAuditRunRead
    page: GrowthAuditPageRead
    result: GrowthAuditPageResultRead
    findings_count: int = Field(serialization_alias="findingsCount")
    tasks_count: int = Field(serialization_alias="tasksCount")
    message: str


class GrowthAuditSearchConsoleAnalysisRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    days: int = Field(default=28, ge=1, le=90)


class GrowthAuditSearchConsoleAnalysisResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    run: GrowthAuditRunRead
    summary: dict[str, Any]
    message: str


class GrowthAuditAnalyticsAnalysisRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    days: int = Field(default=28, ge=1, le=90)


class GrowthAuditAnalyticsAnalysisResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    run: GrowthAuditRunRead
    summary: dict[str, Any]
    message: str


class GrowthAuditShopifyCommerceAnalysisRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    days: int = Field(default=30, ge=7, le=90)


class GrowthAuditShopifyCommerceAnalysisResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    run: GrowthAuditRunRead
    summary: dict[str, Any]
    message: str


class GrowthAuditGa4EcommerceAnalysisRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    days: int = Field(default=30, ge=7, le=90)


class GrowthAuditGa4EcommerceAnalysisResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    run: GrowthAuditRunRead
    summary: dict[str, Any]
    message: str


class GrowthAuditMerchantCenterAnalysisRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class GrowthAuditMerchantCenterAnalysisResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    run: GrowthAuditRunRead
    summary: dict[str, Any]
    message: str


class GrowthAuditPageResultsListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    results: list[GrowthAuditPageResultRead]
