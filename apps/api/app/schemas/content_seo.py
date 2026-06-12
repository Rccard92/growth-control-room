from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ContentSeoSyncResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    collections_synced: int = Field(serialization_alias="collectionsSynced")
    pages_synced: int = Field(serialization_alias="pagesSynced")
    blogs_synced: int = Field(serialization_alias="blogsSynced")
    articles_synced: int = Field(serialization_alias="articlesSynced")
    duration_seconds: float = Field(serialization_alias="durationSeconds")


class ContentSeoAnalyzeResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    issues_created: int = Field(serialization_alias="issuesCreated")
    opportunities_created: int = Field(serialization_alias="opportunitiesCreated")
    critical_issues: int = Field(serialization_alias="criticalIssues")
    high_priority_opportunities: int = Field(
        serialization_alias="highPriorityOpportunities"
    )


class SeoAuditIssueRead(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    entity_type: str = Field(serialization_alias="entityType")
    entity_id: str = Field(serialization_alias="entityId")
    issue_type: str = Field(serialization_alias="issueType")
    severity: str
    title: str
    description: str
    recommendation: str
    status: str
    created_at: datetime | None = Field(default=None, serialization_alias="createdAt")


class ContentOpportunityRead(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    opportunity_type: str = Field(serialization_alias="opportunityType")
    priority: str
    title: str
    description: str
    target_entity_type: str | None = Field(
        default=None, serialization_alias="targetEntityType"
    )
    target_entity_id: str | None = Field(default=None, serialization_alias="targetEntityId")
    suggested_keyword: str | None = Field(default=None, serialization_alias="suggestedKeyword")
    search_intent: str | None = Field(default=None, serialization_alias="searchIntent")
    suggested_products: list[dict[str, Any]] | None = Field(
        default=None, serialization_alias="suggestedProducts"
    )
    suggested_collections: list[dict[str, Any]] | None = Field(
        default=None, serialization_alias="suggestedCollections"
    )
    reason: str
    status: str
    created_at: datetime | None = Field(default=None, serialization_alias="createdAt")


class ContentBriefRead(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: UUID
    title: str
    primary_keyword: str | None = Field(default=None, serialization_alias="primaryKeyword")
    secondary_keywords: list[str] | None = Field(
        default=None, serialization_alias="secondaryKeywords"
    )
    search_intent: str | None = Field(default=None, serialization_alias="searchIntent")
    outline: dict[str, Any] | None = None
    internal_links: list[dict[str, Any]] | None = Field(
        default=None, serialization_alias="internalLinks"
    )
    products_to_feature: list[dict[str, Any]] | None = Field(
        default=None, serialization_alias="productsToFeature"
    )
    faq: list[dict[str, Any]] | None = None
    cta: str | None = None
    status: str


class ContentSeoDashboardSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    total_issues: int = Field(serialization_alias="totalIssues")
    critical_issues: int = Field(serialization_alias="criticalIssues")
    warnings: int = Field(serialization_alias="warnings")
    opportunities: int
    content_opportunities: int = Field(serialization_alias="contentOpportunities")
    products_without_meta: int = Field(serialization_alias="productsWithoutMeta")
    collections_weak: int = Field(serialization_alias="collectionsWeak")
    articles_weak: int = Field(serialization_alias="articlesWeak")
    has_synced_content: bool = Field(default=False, serialization_alias="hasSyncedContent")
    content_entities_count: int = Field(default=0, serialization_alias="contentEntitiesCount")


class ContentSeoDashboardResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    summary: ContentSeoDashboardSummary
    issues: list[SeoAuditIssueRead]
    opportunities: list[ContentOpportunityRead]
    top_product_opportunities: list[ContentOpportunityRead] = Field(
        serialization_alias="topProductOpportunities"
    )
    top_collection_opportunities: list[ContentOpportunityRead] = Field(
        serialization_alias="topCollectionOpportunities"
    )
    internal_linking_opportunities: list[ContentOpportunityRead] = Field(
        serialization_alias="internalLinkingOpportunities"
    )
