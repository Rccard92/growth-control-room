from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SeoAnalyzeCountResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    products_analyzed: int | None = Field(default=None, serialization_alias="productsAnalyzed")
    collections_analyzed: int | None = Field(
        default=None, serialization_alias="collectionsAnalyzed"
    )
    critical: int = 0
    warnings: int = 0
    opportunities: int = 0
    message: str | None = None


class SeoProductListItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    shopify_gid: str = Field(serialization_alias="shopifyGid")
    title: str
    handle: str | None = None
    score: int | None = None
    severity: str | None = None
    main_issues: list[str] = Field(default_factory=list, serialization_alias="mainIssues")
    quantity_sold: int = Field(default=0, serialization_alias="quantitySold")
    revenue: float = 0
    stock: int | None = None
    has_proposal: bool = Field(default=False, serialization_alias="hasProposal")
    analysis_id: str | None = Field(default=None, serialization_alias="analysisId")


class SeoCollectionListItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    shopify_gid: str = Field(serialization_alias="shopifyGid")
    title: str
    handle: str | None = None
    score: int | None = None
    severity: str | None = None
    main_issues: list[str] = Field(default_factory=list, serialization_alias="mainIssues")
    products_count: int | None = Field(default=None, serialization_alias="productsCount")
    has_proposal: bool = Field(default=False, serialization_alias="hasProposal")
    analysis_id: str | None = Field(default=None, serialization_alias="analysisId")


class SeoProductListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: list[SeoProductListItem]
    openai_configured: bool = Field(serialization_alias="openaiConfigured")
    write_products_available: bool = Field(serialization_alias="writeProductsAvailable")


class SeoCollectionListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: list[SeoCollectionListItem]
    openai_configured: bool = Field(serialization_alias="openaiConfigured")
    write_products_available: bool = Field(serialization_alias="writeProductsAvailable")


class SeoProposalGenerateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    entity_type: str = Field(validation_alias="entityType")
    entity_id: UUID = Field(validation_alias="entityId")
    use_ai: bool = Field(default=True, validation_alias="useAi")
    mode: str = Field(default="fill_missing_and_improve")


class SeoProposalManualRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    entity_type: str = Field(validation_alias="entityType")
    entity_id: UUID = Field(validation_alias="entityId")
    proposed_values: dict[str, Any] = Field(validation_alias="proposedValues")
    changed_fields: list[str] | None = Field(
        default=None, validation_alias="changedFields"
    )


class SeoProposalGenerateFieldRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    entity_type: str = Field(validation_alias="entityType")
    entity_id: UUID = Field(validation_alias="entityId")
    field: str
    image_id: str | None = Field(default=None, validation_alias="imageId")
    use_ai: bool = Field(default=True, validation_alias="useAi")


class SeoProposalGenerateFieldResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    field: str
    value: Any
    reasoning: str | None = None
    risk_level: str = Field(serialization_alias="riskLevel")


class SeoScoreBreakdownItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    score: int
    max: int
    issues: list[dict[str, Any]] = Field(default_factory=list)


class SeoProposalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    entity_type: str = Field(serialization_alias="entityType")
    entity_id: UUID = Field(serialization_alias="entityId")
    entity_gid: str = Field(serialization_alias="entityGid")
    status: str
    source: str
    current_values: dict[str, Any] | None = Field(
        default=None, serialization_alias="currentValues"
    )
    proposed_values: dict[str, Any] | None = Field(
        default=None, serialization_alias="proposedValues"
    )
    reasoning: list[Any] | None = None
    risk_level: str = Field(serialization_alias="riskLevel")
    approved_at: datetime | None = Field(default=None, serialization_alias="approvedAt")
    applied_at: datetime | None = Field(default=None, serialization_alias="appliedAt")
    created_at: datetime | None = Field(default=None, serialization_alias="createdAt")
    changed_fields: list[str] = Field(
        default_factory=list, serialization_alias="changedFields"
    )


class SeoProposalPreviewField(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    field: str
    current: Any = None
    proposed: Any = None
    changed: bool = False
    reasoning: str | None = None
    risk: str | None = None


class SeoProposalPreviewResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    proposal_id: str = Field(serialization_alias="proposalId")
    entity_type: str = Field(serialization_alias="entityType")
    entity_id: str = Field(serialization_alias="entityId")
    status: str
    source: str
    risk_level: str = Field(serialization_alias="riskLevel")
    reasoning: list[Any] | None = None
    fields: list[SeoProposalPreviewField]
    changed_fields: list[str] = Field(serialization_alias="changedFields")
    current_values: dict[str, Any] | None = Field(
        default=None, serialization_alias="currentValues"
    )
    proposed_values: dict[str, Any] | None = Field(
        default=None, serialization_alias="proposedValues"
    )


class SeoSkillMetaRead(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = "GCR Shopify SEO Skill"
    version: str = "1.0.0"
    attribution: str = ""
    score_rule_categories: list[str] = Field(
        default_factory=list,
        serialization_alias="scoreRuleCategories",
    )
    external_skills: list[str] = Field(
        default_factory=list, serialization_alias="externalSkills"
    )


class SeoProductDetailResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    product: dict[str, Any]
    analysis: dict[str, Any] | None = None
    score_breakdown: dict[str, SeoScoreBreakdownItem] | None = Field(
        default=None, serialization_alias="scoreBreakdown"
    )
    current_values: dict[str, Any] = Field(serialization_alias="currentValues")
    images: list[dict[str, Any]] = Field(default_factory=list)
    quantity_sold: int = Field(default=0, serialization_alias="quantitySold")
    revenue: float = 0
    stock: int | None = None
    latest_proposal: SeoProposalRead | None = Field(
        default=None, serialization_alias="latestProposal"
    )
    proposal_history: list[SeoProposalRead] = Field(
        default_factory=list, serialization_alias="proposalHistory"
    )
    change_logs: list[dict[str, Any]] = Field(
        default_factory=list, serialization_alias="changeLogs"
    )
    skill_meta: SeoSkillMetaRead | None = Field(
        default=None, serialization_alias="skillMeta"
    )


class SeoCollectionDetailResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    collection: dict[str, Any]
    analysis: dict[str, Any] | None = None
    score_breakdown: dict[str, SeoScoreBreakdownItem] | None = Field(
        default=None, serialization_alias="scoreBreakdown"
    )
    current_values: dict[str, Any] = Field(serialization_alias="currentValues")
    image: dict[str, Any] | None = None
    latest_proposal: SeoProposalRead | None = Field(
        default=None, serialization_alias="latestProposal"
    )
    proposal_history: list[SeoProposalRead] = Field(
        default_factory=list, serialization_alias="proposalHistory"
    )
    change_logs: list[dict[str, Any]] = Field(
        default_factory=list, serialization_alias="changeLogs"
    )
    skill_meta: SeoSkillMetaRead | None = Field(
        default=None, serialization_alias="skillMeta"
    )


class SeoProposalListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: list[SeoProposalRead]


class SeoApplyResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    applied: bool
    requires_scope: str | None = Field(default=None, serialization_alias="requiresScope")
    requires_reconnect: bool = Field(default=False, serialization_alias="requiresReconnect")
    local_update_failed: bool = Field(default=False, serialization_alias="localUpdateFailed")
    entity_type: str | None = Field(default=None, serialization_alias="entityType")
    entity_id: str | None = Field(default=None, serialization_alias="entityId")
    updated_entity: dict[str, Any] | None = Field(
        default=None, serialization_alias="updatedEntity"
    )
    updated_analysis: dict[str, Any] | None = Field(
        default=None, serialization_alias="updatedAnalysis"
    )
    detail: dict[str, Any] | None = None
    proposal: dict[str, Any] | None = None
    message: str | None = None
    proposal_id: str | None = Field(default=None, serialization_alias="proposalId")


class SeoEntitySyncResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    entity_type: str = Field(serialization_alias="entityType")
    entity_id: str = Field(serialization_alias="entityId")
    detail: dict[str, Any]
    message: str


class SeoEntityAnalysisRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    entity_type: str = Field(serialization_alias="entityType")
    entity_id: UUID = Field(serialization_alias="entityId")
    entity_title: str = Field(serialization_alias="entityTitle")
    score_total: int = Field(serialization_alias="scoreTotal")
    score_title: int = Field(serialization_alias="scoreTitle")
    score_seo_title: int = Field(serialization_alias="scoreSeoTitle")
    score_meta_description: int = Field(serialization_alias="scoreMetaDescription")
    score_description: int = Field(serialization_alias="scoreDescription")
    score_image_alt: int = Field(serialization_alias="scoreImageAlt")
    score_handle: int = Field(serialization_alias="scoreHandle")
    score_tags: int = Field(serialization_alias="scoreTags")
    severity: str
    issues: list[dict[str, Any]] | None = None
    recommendations: list[dict[str, Any]] | None = None
    score_breakdown: dict[str, SeoScoreBreakdownItem] | None = Field(
        default=None, serialization_alias="scoreBreakdown"
    )
    last_analyzed_at: datetime | None = Field(default=None, serialization_alias="lastAnalyzedAt")


class SeoOptimizerSyncResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    products_synced: int = Field(default=0, serialization_alias="productsSynced")
    collections_synced: int = Field(default=0, serialization_alias="collectionsSynced")
    pages_synced: int = Field(default=0, serialization_alias="pagesSynced")
    blogs_synced: int = Field(default=0, serialization_alias="blogsSynced")
    articles_synced: int = Field(default=0, serialization_alias="articlesSynced")
    duration_seconds: float = Field(default=0.0, serialization_alias="durationSeconds")
    warnings: list[str] = Field(default_factory=list)
    message: str | None = None


class SeoContentDebugResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    products_count: int = Field(serialization_alias="productsCount")
    collections_count: int = Field(serialization_alias="collectionsCount")
    collection_analyses_count: int = Field(serialization_alias="collectionAnalysesCount")
    last_content_sync: datetime | None = Field(
        default=None, serialization_alias="lastContentSync"
    )
    last_errors: list[str] = Field(default_factory=list, serialization_alias="lastErrors")
