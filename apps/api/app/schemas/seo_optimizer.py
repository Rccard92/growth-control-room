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


class SeoProposalListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: list[SeoProposalRead]


class SeoApplyResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    applied: bool
    requires_scope: str | None = Field(default=None, serialization_alias="requiresScope")
    message: str | None = None
    proposal_id: str | None = Field(default=None, serialization_alias="proposalId")


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
    last_analyzed_at: datetime | None = Field(default=None, serialization_alias="lastAnalyzedAt")


class SeoOptimizerSyncResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    products_synced: int = Field(default=0, serialization_alias="productsSynced")
    collections_synced: int = Field(default=0, serialization_alias="collectionsSynced")
    duration_seconds: float = Field(default=0.0, serialization_alias="durationSeconds")
