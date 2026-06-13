from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BrandProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    project_id: UUID = Field(serialization_alias="projectId")
    brand_name: str | None = Field(default=None, serialization_alias="brandName")
    website_url: str | None = Field(default=None, serialization_alias="websiteUrl")
    industry: str | None = None
    country: str | None = None
    short_description: str | None = Field(default=None, serialization_alias="shortDescription")
    story: str | None = None
    mission: str | None = None
    values: list[str] | None = None
    differentiators: list[str] | None = None
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class BrandProfileUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    brand_name: str | None = Field(default=None, validation_alias="brandName")
    website_url: str | None = Field(default=None, validation_alias="websiteUrl")
    industry: str | None = None
    country: str | None = None
    short_description: str | None = Field(default=None, validation_alias="shortDescription")
    story: str | None = None
    mission: str | None = None
    values: list[str] | None = None
    differentiators: list[str] | None = None


class BrandVoiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    project_id: UUID = Field(serialization_alias="projectId")
    tone: str | None = None
    style_notes: str | None = Field(default=None, serialization_alias="styleNotes")
    formality_level: str | None = Field(default=None, serialization_alias="formalityLevel")
    emoji_policy: str | None = Field(default=None, serialization_alias="emojiPolicy")
    words_to_use: list[str] | None = Field(default=None, serialization_alias="wordsToUse")
    words_to_avoid: list[str] | None = Field(default=None, serialization_alias="wordsToAvoid")
    examples_good: list[str] | None = Field(default=None, serialization_alias="examplesGood")
    examples_bad: list[str] | None = Field(default=None, serialization_alias="examplesBad")
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class BrandVoiceUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    tone: str | None = None
    style_notes: str | None = Field(default=None, validation_alias="styleNotes")
    formality_level: str | None = Field(default=None, validation_alias="formalityLevel")
    emoji_policy: str | None = Field(default=None, validation_alias="emojiPolicy")
    words_to_use: list[str] | None = Field(default=None, validation_alias="wordsToUse")
    words_to_avoid: list[str] | None = Field(default=None, validation_alias="wordsToAvoid")
    examples_good: list[str] | None = Field(default=None, validation_alias="examplesGood")
    examples_bad: list[str] | None = Field(default=None, validation_alias="examplesBad")


class BrandProductKnowledgeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    project_id: UUID = Field(serialization_alias="projectId")
    name: str
    entity_type: str = Field(serialization_alias="entityType")
    shopify_gid: str | None = Field(default=None, serialization_alias="shopifyGid")
    description: str | None = None
    ingredients: str | None = None
    origin: str | None = None
    production_process: str | None = Field(default=None, serialization_alias="productionProcess")
    usage_suggestions: str | None = Field(default=None, serialization_alias="usageSuggestions")
    conservation: str | None = None
    taste_notes: str | None = Field(default=None, serialization_alias="tasteNotes")
    objections: list[str] | None = None
    faq: list[dict[str, Any]] | None = None
    claims_allowed: list[str] | None = Field(default=None, serialization_alias="claimsAllowed")
    claims_forbidden: list[str] | None = Field(default=None, serialization_alias="claimsForbidden")
    related_products: list[str] | None = Field(default=None, serialization_alias="relatedProducts")
    priority: str = "medium"
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class BrandProductKnowledgeCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    entity_type: str = Field(default="product", validation_alias="entityType")
    shopify_gid: str | None = Field(default=None, validation_alias="shopifyGid")
    description: str | None = None
    ingredients: str | None = None
    origin: str | None = None
    production_process: str | None = Field(default=None, validation_alias="productionProcess")
    usage_suggestions: str | None = Field(default=None, validation_alias="usageSuggestions")
    conservation: str | None = None
    taste_notes: str | None = Field(default=None, validation_alias="tasteNotes")
    objections: list[str] | None = None
    faq: list[dict[str, Any]] | None = None
    claims_allowed: list[str] | None = Field(default=None, validation_alias="claimsAllowed")
    claims_forbidden: list[str] | None = Field(default=None, validation_alias="claimsForbidden")
    related_products: list[str] | None = Field(default=None, validation_alias="relatedProducts")
    priority: str = "medium"


class BrandProductKnowledgeUpdate(BrandProductKnowledgeCreate):
    name: str | None = None  # type: ignore[assignment]


class BrandAudienceInsightRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    project_id: UUID = Field(serialization_alias="projectId")
    segment_name: str = Field(serialization_alias="segmentName")
    description: str | None = None
    motivations: list[str] | None = None
    pain_points: list[str] | None = Field(default=None, serialization_alias="painPoints")
    objections: list[str] | None = None
    questions: list[str] | None = None
    buying_triggers: list[str] | None = Field(default=None, serialization_alias="buyingTriggers")
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class BrandAudienceInsightCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    segment_name: str = Field(validation_alias="segmentName")
    description: str | None = None
    motivations: list[str] | None = None
    pain_points: list[str] | None = Field(default=None, validation_alias="painPoints")
    objections: list[str] | None = None
    questions: list[str] | None = None
    buying_triggers: list[str] | None = Field(default=None, validation_alias="buyingTriggers")


class BrandAudienceInsightUpdate(BrandAudienceInsightCreate):
    segment_name: str | None = Field(default=None, validation_alias="segmentName")  # type: ignore[assignment]


class BrandClaimRuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    project_id: UUID = Field(serialization_alias="projectId")
    rule_type: str = Field(serialization_alias="ruleType")
    title: str
    description: str | None = None
    examples: list[str] | None = None
    severity: str = "info"
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class BrandClaimRuleCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    rule_type: str = Field(validation_alias="ruleType")
    title: str
    description: str | None = None
    examples: list[str] | None = None
    severity: str = "info"


class BrandClaimRuleUpdate(BrandClaimRuleCreate):
    rule_type: str | None = Field(default=None, validation_alias="ruleType")  # type: ignore[assignment]
    title: str | None = None  # type: ignore[assignment]


class BrandSeoStrategyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    project_id: UUID = Field(serialization_alias="projectId")
    primary_keywords: list[str] | None = Field(default=None, serialization_alias="primaryKeywords")
    secondary_keywords: list[str] | None = Field(default=None, serialization_alias="secondaryKeywords")
    keyword_clusters: list[dict[str, Any]] | None = Field(default=None, serialization_alias="keywordClusters")
    priority_pages: list[str] | None = Field(default=None, serialization_alias="priorityPages")
    internal_linking_notes: str | None = Field(default=None, serialization_alias="internalLinkingNotes")
    meta_title_pattern: str | None = Field(default=None, serialization_alias="metaTitlePattern")
    meta_description_pattern: str | None = Field(default=None, serialization_alias="metaDescriptionPattern")
    url_handle_pattern: str | None = Field(default=None, serialization_alias="urlHandlePattern")
    competitors: list[str] | None = None
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class BrandSeoStrategyUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    primary_keywords: list[str] | None = Field(default=None, validation_alias="primaryKeywords")
    secondary_keywords: list[str] | None = Field(default=None, validation_alias="secondaryKeywords")
    keyword_clusters: list[dict[str, Any]] | None = Field(default=None, validation_alias="keywordClusters")
    priority_pages: list[str] | None = Field(default=None, validation_alias="priorityPages")
    internal_linking_notes: str | None = Field(default=None, validation_alias="internalLinkingNotes")
    meta_title_pattern: str | None = Field(default=None, validation_alias="metaTitlePattern")
    meta_description_pattern: str | None = Field(default=None, validation_alias="metaDescriptionPattern")
    url_handle_pattern: str | None = Field(default=None, validation_alias="urlHandlePattern")
    competitors: list[str] | None = None


class BrandContentPillarRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    project_id: UUID = Field(serialization_alias="projectId")
    name: str
    description: str | None = None
    objective: str | None = None
    products: list[str] | None = None
    channels: list[str] | None = None
    example_topics: list[str] | None = Field(default=None, serialization_alias="exampleTopics")
    cta_notes: str | None = Field(default=None, serialization_alias="ctaNotes")
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class BrandContentPillarCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    description: str | None = None
    objective: str | None = None
    products: list[str] | None = None
    channels: list[str] | None = None
    example_topics: list[str] | None = Field(default=None, validation_alias="exampleTopics")
    cta_notes: str | None = Field(default=None, validation_alias="ctaNotes")


class BrandContentPillarUpdate(BrandContentPillarCreate):
    name: str | None = None  # type: ignore[assignment]


class BrandAiGuardrailRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    project_id: UUID = Field(serialization_alias="projectId")
    title: str
    description: str | None = None
    rule_type: str = Field(serialization_alias="ruleType")
    applies_to: list[str] | None = Field(default=None, serialization_alias="appliesTo")
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class BrandAiGuardrailCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: str
    description: str | None = None
    rule_type: str = Field(validation_alias="ruleType")
    applies_to: list[str] | None = Field(default=None, validation_alias="appliesTo")


class BrandAiGuardrailUpdate(BrandAiGuardrailCreate):
    title: str | None = None  # type: ignore[assignment]
    rule_type: str | None = Field(default=None, validation_alias="ruleType")  # type: ignore[assignment]


class BrandAssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    project_id: UUID = Field(serialization_alias="projectId")
    asset_type: str = Field(serialization_alias="assetType")
    name: str
    value: str | None = None
    file_url: str | None = Field(default=None, serialization_alias="fileUrl")
    notes: str | None = None
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class BrandAssetCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    asset_type: str = Field(validation_alias="assetType")
    name: str
    value: str | None = None
    file_url: str | None = Field(default=None, validation_alias="fileUrl")
    notes: str | None = None


class BrandAssetUpdate(BrandAssetCreate):
    asset_type: str | None = Field(default=None, validation_alias="assetType")  # type: ignore[assignment]
    name: str | None = None  # type: ignore[assignment]


class BrandKnowledgeScoreResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    overall_score: int = Field(serialization_alias="overallScore")
    status: str
    section_scores: dict[str, int] = Field(serialization_alias="sectionScores")
    missing_required: list[str] = Field(serialization_alias="missingRequired")
    recommendations: list[str]


class BrandSectionStatus(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    key: str
    label: str
    complete: bool
    score: int


class BrandIntelligenceOverviewResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    score: BrandKnowledgeScoreResponse
    sections: list[BrandSectionStatus]
    has_profile: bool = Field(serialization_alias="hasProfile")
    has_voice: bool = Field(serialization_alias="hasVoice")
    products_count: int = Field(serialization_alias="productsCount")
    audience_count: int = Field(serialization_alias="audienceCount")
    claims_count: int = Field(serialization_alias="claimsCount")
    guardrails_count: int = Field(serialization_alias="guardrailsCount")
    pillars_count: int = Field(serialization_alias="pillarsCount")
    assets_count: int = Field(serialization_alias="assetsCount")


class BrandContextBundleResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    profile: BrandProfileRead | None = None
    voice: BrandVoiceRead | None = None
    products: list[BrandProductKnowledgeRead] = []
    categories: list[BrandProductKnowledgeRead] = []
    audience: list[BrandAudienceInsightRead] = []
    claims: list[BrandClaimRuleRead] = []
    seo_strategy: BrandSeoStrategyRead | None = Field(default=None, serialization_alias="seoStrategy")
    content_pillars: list[BrandContentPillarRead] = Field(
        default_factory=list, serialization_alias="contentPillars"
    )
    guardrails: list[BrandAiGuardrailRead] = []
    assets: list[BrandAssetRead] = []
    knowledge_score: BrandKnowledgeScoreResponse = Field(serialization_alias="knowledgeScore")
