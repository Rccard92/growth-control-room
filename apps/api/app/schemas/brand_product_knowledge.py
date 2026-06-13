from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

ModuleCompletionStatus = Literal["complete", "partial", "empty"]


class FaqEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    question: str
    answer: str


class BrandProductKnowledgeGeneralRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    project_id: UUID = Field(serialization_alias="projectId")
    general_principles: list[str] | None = Field(
        default=None, serialization_alias="generalPrinciples"
    )
    common_strengths: list[str] | None = Field(
        default=None, serialization_alias="commonStrengths"
    )
    common_quality_rules: list[str] | None = Field(
        default=None, serialization_alias="commonQualityRules"
    )
    common_production_notes: list[str] | None = Field(
        default=None, serialization_alias="commonProductionNotes"
    )
    common_usage_notes: list[str] | None = Field(
        default=None, serialization_alias="commonUsageNotes"
    )
    common_objections: list[str] | None = Field(
        default=None, serialization_alias="commonObjections"
    )
    common_faq: list[dict[str, Any]] | None = Field(default=None, serialization_alias="commonFaq")
    communication_rules: list[str] | None = Field(
        default=None, serialization_alias="communicationRules"
    )
    product_storytelling_rules: list[str] | None = Field(
        default=None, serialization_alias="productStorytellingRules"
    )
    notes: str | None = None
    last_import_source: str | None = Field(default=None, serialization_alias="lastImportSource")
    last_confidence: float | None = Field(default=None, serialization_alias="lastConfidence")
    warnings: list[str] | None = None
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class BrandProductKnowledgeGeneralUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    general_principles: list[str] | None = Field(
        default=None, validation_alias="generalPrinciples"
    )
    common_strengths: list[str] | None = Field(default=None, validation_alias="commonStrengths")
    common_quality_rules: list[str] | None = Field(
        default=None, validation_alias="commonQualityRules"
    )
    common_production_notes: list[str] | None = Field(
        default=None, validation_alias="commonProductionNotes"
    )
    common_usage_notes: list[str] | None = Field(default=None, validation_alias="commonUsageNotes")
    common_objections: list[str] | None = Field(default=None, validation_alias="commonObjections")
    common_faq: list[dict[str, Any]] | None = Field(default=None, validation_alias="commonFaq")
    communication_rules: list[str] | None = Field(
        default=None, validation_alias="communicationRules"
    )
    product_storytelling_rules: list[str] | None = Field(
        default=None, validation_alias="productStorytellingRules"
    )
    notes: str | None = None


class BrandProductKnowledgeGeneralProposal(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    general_principles: list[str] | None = Field(
        default=None, validation_alias="generalPrinciples", serialization_alias="generalPrinciples"
    )
    common_strengths: list[str] | None = Field(
        default=None, validation_alias="commonStrengths", serialization_alias="commonStrengths"
    )
    common_quality_rules: list[str] | None = Field(
        default=None, validation_alias="commonQualityRules", serialization_alias="commonQualityRules"
    )
    common_production_notes: list[str] | None = Field(
        default=None,
        validation_alias="commonProductionNotes",
        serialization_alias="commonProductionNotes",
    )
    common_usage_notes: list[str] | None = Field(
        default=None, validation_alias="commonUsageNotes", serialization_alias="commonUsageNotes"
    )
    common_objections: list[str] | None = Field(
        default=None, validation_alias="commonObjections", serialization_alias="commonObjections"
    )
    common_faq: list[dict[str, Any]] | None = Field(
        default=None, validation_alias="commonFaq", serialization_alias="commonFaq"
    )
    communication_rules: list[str] | None = Field(
        default=None, validation_alias="communicationRules", serialization_alias="communicationRules"
    )
    product_storytelling_rules: list[str] | None = Field(
        default=None,
        validation_alias="productStorytellingRules",
        serialization_alias="productStorytellingRules",
    )
    notes: str | None = None


class BrandProductKnowledgeGeneralImportResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    proposal: BrandProductKnowledgeGeneralProposal
    confidence: float = 0.0
    warnings: list[str] = Field(default_factory=list)
    source_summary: str = Field(default="", serialization_alias="sourceSummary")


class BrandProductKnowledgeGeneralApplyProposalRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    proposal: BrandProductKnowledgeGeneralProposal


class BrandProductKnowledgeGeneralApplyProposalResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    general: BrandProductKnowledgeGeneralRead
    message: str = "Product Knowledge generale aggiornata."


class BrandProductKnowledgeItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    project_id: UUID = Field(serialization_alias="projectId")
    shopify_product_id: UUID | None = Field(default=None, serialization_alias="shopifyProductId")
    shopify_product_gid: str | None = Field(default=None, serialization_alias="shopifyProductGid")
    shopify_handle: str | None = Field(default=None, serialization_alias="shopifyHandle")
    shopify_title: str | None = Field(default=None, serialization_alias="shopifyTitle")
    product_name: str = Field(serialization_alias="productName")
    product_line: str | None = Field(default=None, serialization_alias="productLine")
    priority: str | None = None
    strategic_description: str | None = Field(
        default=None, serialization_alias="strategicDescription"
    )
    origin: str | None = None
    ingredients: str | None = None
    production_process: str | None = Field(default=None, serialization_alias="productionProcess")
    taste_notes: str | None = Field(default=None, serialization_alias="tasteNotes")
    color_notes: str | None = Field(default=None, serialization_alias="colorNotes")
    texture_notes: str | None = Field(default=None, serialization_alias="textureNotes")
    usage_suggestions: str | None = Field(default=None, serialization_alias="usageSuggestions")
    conservation: str | None = None
    target_audience: str | None = Field(default=None, serialization_alias="targetAudience")
    objections: list[str] | None = None
    faq: list[dict[str, Any]] | None = None
    allowed_claims: list[str] | None = Field(default=None, serialization_alias="allowedClaims")
    forbidden_claims: list[str] | None = Field(default=None, serialization_alias="forbiddenClaims")
    seo_notes: str | None = Field(default=None, serialization_alias="seoNotes")
    ads_social_notes: str | None = Field(default=None, serialization_alias="adsSocialNotes")
    related_products: list[str] | None = Field(default=None, serialization_alias="relatedProducts")
    source_type: str | None = Field(default=None, serialization_alias="sourceType")
    last_synced_from_shopify_at: datetime | None = Field(
        default=None, serialization_alias="lastSyncedFromShopifyAt"
    )
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")
    completion_status: ModuleCompletionStatus | None = Field(
        default=None, serialization_alias="completionStatus"
    )


class BrandProductKnowledgeItemUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    product_name: str | None = Field(default=None, validation_alias="productName")
    product_line: str | None = Field(default=None, validation_alias="productLine")
    priority: str | None = None
    strategic_description: str | None = Field(
        default=None, validation_alias="strategicDescription"
    )
    origin: str | None = None
    ingredients: str | None = None
    production_process: str | None = Field(default=None, validation_alias="productionProcess")
    taste_notes: str | None = Field(default=None, validation_alias="tasteNotes")
    color_notes: str | None = Field(default=None, validation_alias="colorNotes")
    texture_notes: str | None = Field(default=None, validation_alias="textureNotes")
    usage_suggestions: str | None = Field(default=None, validation_alias="usageSuggestions")
    conservation: str | None = None
    target_audience: str | None = Field(default=None, validation_alias="targetAudience")
    objections: list[str] | None = None
    faq: list[dict[str, Any]] | None = None
    allowed_claims: list[str] | None = Field(default=None, validation_alias="allowedClaims")
    forbidden_claims: list[str] | None = Field(default=None, validation_alias="forbiddenClaims")
    seo_notes: str | None = Field(default=None, validation_alias="seoNotes")
    ads_social_notes: str | None = Field(default=None, validation_alias="adsSocialNotes")
    related_products: list[str] | None = Field(default=None, validation_alias="relatedProducts")


class BrandProductKnowledgeItemFromShopifyRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    shopify_product_id: UUID = Field(validation_alias="shopifyProductId")


class BrandProductKnowledgeShopifyProductOption(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: UUID
    shopify_gid: str = Field(serialization_alias="shopifyGid")
    title: str
    handle: str
    status: str | None = None
    vendor: str | None = None
    product_type: str | None = Field(default=None, serialization_alias="productType")
    featured_image_url: str | None = Field(default=None, serialization_alias="featuredImageUrl")
    has_knowledge_item: bool = Field(default=False, serialization_alias="hasKnowledgeItem")


class BrandProductKnowledgeShopifyProductsResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    shopify_connected: bool = Field(serialization_alias="shopifyConnected")
    message: str | None = None
    products: list[BrandProductKnowledgeShopifyProductOption] = Field(default_factory=list)


class BrandProductKnowledgeGeneralRulesContext(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    general_principles: list[str] = Field(
        default_factory=list, serialization_alias="generalPrinciples"
    )
    common_strengths: list[str] = Field(default_factory=list, serialization_alias="commonStrengths")
    quality_rules: list[str] = Field(default_factory=list, serialization_alias="qualityRules")
    production_notes: list[str] = Field(default_factory=list, serialization_alias="productionNotes")
    usage_notes: list[str] = Field(default_factory=list, serialization_alias="usageNotes")
    common_objections: list[str] = Field(
        default_factory=list, serialization_alias="commonObjections"
    )
    common_faq: list[dict[str, Any]] = Field(default_factory=list, serialization_alias="commonFaq")
    communication_rules: list[str] = Field(
        default_factory=list, serialization_alias="communicationRules"
    )
    storytelling_rules: list[str] = Field(
        default_factory=list, serialization_alias="storytellingRules"
    )


class BrandProductKnowledgeSpecificProductContext(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    shopify_product_id: str | None = Field(default=None, serialization_alias="shopifyProductId")
    shopify_gid: str | None = Field(default=None, serialization_alias="shopifyGid")
    title: str | None = None
    handle: str | None = None
    product_line: str | None = Field(default=None, serialization_alias="productLine")
    strategic_description: str | None = Field(
        default=None, serialization_alias="strategicDescription"
    )
    origin: str | None = None
    ingredients: str | None = None
    usage_suggestions: str | None = Field(default=None, serialization_alias="usageSuggestions")
    faq: list[dict[str, Any]] = Field(default_factory=list)
    allowed_claims: list[str] = Field(default_factory=list, serialization_alias="allowedClaims")
    forbidden_claims: list[str] = Field(default_factory=list, serialization_alias="forbiddenClaims")
    seo_notes: str | None = Field(default=None, serialization_alias="seoNotes")


class BrandProductKnowledgeContext(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    general_rules: BrandProductKnowledgeGeneralRulesContext | None = Field(
        default=None, serialization_alias="generalRules"
    )
    specific_products: list[BrandProductKnowledgeSpecificProductContext] = Field(
        default_factory=list, serialization_alias="specificProducts"
    )


class BrandProductKnowledgeItemProposal(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    product_name: str = Field(validation_alias="productName", serialization_alias="productName")
    product_line: str | None = Field(default=None, validation_alias="productLine", serialization_alias="productLine")
    priority: str | None = None
    strategic_description: str | None = Field(
        default=None, validation_alias="strategicDescription", serialization_alias="strategicDescription"
    )
    origin: str | None = None
    ingredients: str | None = None
    production_process: str | None = Field(
        default=None, validation_alias="productionProcess", serialization_alias="productionProcess"
    )
    taste_notes: str | None = Field(default=None, validation_alias="tasteNotes", serialization_alias="tasteNotes")
    color_notes: str | None = Field(default=None, validation_alias="colorNotes", serialization_alias="colorNotes")
    texture_notes: str | None = Field(
        default=None, validation_alias="textureNotes", serialization_alias="textureNotes"
    )
    usage_suggestions: str | None = Field(
        default=None, validation_alias="usageSuggestions", serialization_alias="usageSuggestions"
    )
    conservation: str | None = None
    target_audience: str | None = Field(
        default=None, validation_alias="targetAudience", serialization_alias="targetAudience"
    )
    objections: list[str] | None = None
    faq: list[dict[str, Any]] | None = None
    allowed_claims: list[str] | None = Field(
        default=None, validation_alias="allowedClaims", serialization_alias="allowedClaims"
    )
    forbidden_claims: list[str] | None = Field(
        default=None, validation_alias="forbiddenClaims", serialization_alias="forbiddenClaims"
    )
    seo_notes: str | None = Field(default=None, validation_alias="seoNotes", serialization_alias="seoNotes")
    ads_social_notes: str | None = Field(
        default=None, validation_alias="adsSocialNotes", serialization_alias="adsSocialNotes"
    )
    related_products: list[str] | None = Field(
        default=None, validation_alias="relatedProducts", serialization_alias="relatedProducts"
    )
    missing_fields: list[str] = Field(
        default_factory=list, validation_alias="missingFields", serialization_alias="missingFields"
    )
    confidence: float = 0.0
    warnings: list[str] = Field(default_factory=list)
    suggested_shopify_product_id: UUID | None = Field(
        default=None,
        validation_alias="suggestedShopifyProductId",
        serialization_alias="suggestedShopifyProductId",
    )
    suggested_shopify_title: str | None = Field(
        default=None,
        validation_alias="suggestedShopifyTitle",
        serialization_alias="suggestedShopifyTitle",
    )
    suggested_shopify_handle: str | None = Field(
        default=None,
        validation_alias="suggestedShopifyHandle",
        serialization_alias="suggestedShopifyHandle",
    )
    shopify_match_confidence: float | None = Field(
        default=None,
        validation_alias="shopifyMatchConfidence",
        serialization_alias="shopifyMatchConfidence",
    )
    shopify_product_id: UUID | None = Field(
        default=None, validation_alias="shopifyProductId", serialization_alias="shopifyProductId"
    )
    client_key: str | None = Field(default=None, validation_alias="clientKey", serialization_alias="clientKey")


class BrandProductKnowledgeItemsProposal(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: list[BrandProductKnowledgeItemProposal] = Field(default_factory=list)


class BrandProductKnowledgeItemsImportResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    proposal: BrandProductKnowledgeItemsProposal
    source_summary: str = Field(default="", serialization_alias="sourceSummary")
    warnings: list[str] = Field(default_factory=list)


class BrandProductKnowledgeItemsApplyImportRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: list[BrandProductKnowledgeItemProposal]


class BrandProductKnowledgeDuplicateCandidate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    existing_item_id: UUID = Field(serialization_alias="existingItemId")
    product_name: str = Field(serialization_alias="productName")
    shopify_handle: str | None = Field(default=None, serialization_alias="shopifyHandle")
    reason: str
    completion_status: ModuleCompletionStatus | None = Field(
        default=None, serialization_alias="completionStatus"
    )


class BrandProductKnowledgeSkippedItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    product_name: str = Field(serialization_alias="productName")
    reason: str
    duplicate_candidates: list[BrandProductKnowledgeDuplicateCandidate] = Field(
        default_factory=list, serialization_alias="duplicateCandidates"
    )


class BrandProductKnowledgeItemsApplyImportResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    saved: list[BrandProductKnowledgeItemRead] = Field(default_factory=list)
    skipped: list[BrandProductKnowledgeSkippedItem] = Field(default_factory=list)
    message: str = "Schede prodotto salvate."
