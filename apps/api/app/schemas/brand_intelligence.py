from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


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
    source_documents_count: int = Field(default=0, serialization_alias="sourceDocumentsCount")
    pending_facts_count: int = Field(default=0, serialization_alias="pendingFactsCount")
    pending_section_drafts_count: int = Field(
        default=0, serialization_alias="pendingSectionDraftsCount"
    )
    latest_batch_id: UUID | None = Field(default=None, serialization_alias="latestBatchId")


class BrandSectionDraftRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    project_id: UUID = Field(serialization_alias="projectId")
    batch_id: UUID | None = Field(default=None, serialization_alias="batchId")
    section_key: str = Field(serialization_alias="sectionKey")
    title: str
    draft_payload: Any = Field(serialization_alias="draftPayload")
    summary: str | None = None
    source_fact_ids: list[str] = Field(default_factory=list, serialization_alias="sourceFactIds")
    source_document_ids: list[str] = Field(
        default_factory=list, serialization_alias="sourceDocumentIds"
    )
    confidence: float | None = None
    status: str
    ai_reasoning: str | None = Field(default=None, serialization_alias="aiReasoning")
    warnings: Any | None = None
    previous_official_snapshot: Any | None = Field(
        default=None, serialization_alias="previousOfficialSnapshot"
    )
    approved_at: datetime | None = Field(default=None, serialization_alias="approvedAt")
    applied_at: datetime | None = Field(default=None, serialization_alias="appliedAt")
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")

    @field_validator("source_fact_ids", "source_document_ids", mode="before")
    @classmethod
    def _coerce_id_lists(cls, v: object) -> list[str]:
        if v is None:
            return []
        if isinstance(v, list):
            return [str(x) for x in v]
        return []


class BrandSectionDraftListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    batch_id: UUID | None = Field(default=None, serialization_alias="batchId")
    section_key: str = Field(serialization_alias="sectionKey")
    title: str
    summary: str | None = None
    confidence: float | None = None
    status: str
    source_fact_ids: list[str] = Field(default_factory=list, serialization_alias="sourceFactIds")
    warnings: Any | None = None
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")

    @field_validator("source_fact_ids", mode="before")
    @classmethod
    def _coerce_fact_ids(cls, v: object) -> list[str]:
        if v is None:
            return []
        if isinstance(v, list):
            return [str(x) for x in v]
        return []


class BrandSectionDraftUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    draft_payload: Any | None = Field(default=None, validation_alias="draftPayload")
    status: str | None = None
    warnings: Any | None = None


class BrandSectionDraftSynthesizeSectionItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    section_key: str = Field(serialization_alias="sectionKey")
    status: str
    confidence: float | None = None


class BrandSectionDraftSynthesizeResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    batch_id: UUID = Field(serialization_alias="batchId")
    drafts_created: int = Field(serialization_alias="draftsCreated")
    sections: list[BrandSectionDraftSynthesizeSectionItem] = Field(default_factory=list)


class BrandSectionDraftRegenerateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    instructions: str | None = None
    include_fact_ids: list[UUID] | None = Field(default=None, validation_alias="includeFactIds")


class BrandSectionDraftApplyBatchRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    draft_ids: list[UUID] = Field(validation_alias="draftIds")


class BrandSectionDraftApplyResultItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    draft_id: UUID = Field(serialization_alias="draftId")
    section_key: str = Field(serialization_alias="sectionKey")
    status: str
    message: str


class BrandSectionDraftApplyResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    applied: list[BrandSectionDraftApplyResultItem] = Field(default_factory=list)
    skipped: list[BrandSectionDraftApplyResultItem] = Field(default_factory=list)
    conflicts: list[BrandSectionDraftApplyResultItem] = Field(default_factory=list)


class BrandSourceDocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    project_id: UUID = Field(serialization_alias="projectId")
    batch_id: UUID | None = Field(default=None, serialization_alias="batchId")
    filename: str
    content_type: str = Field(serialization_alias="contentType")
    file_size: int = Field(serialization_alias="fileSize")
    storage_mode: str = Field(serialization_alias="storageMode")
    document_type: str | None = Field(default=None, serialization_alias="documentType")
    document_summary: str | None = Field(default=None, serialization_alias="documentSummary")
    extraction_status: str = Field(serialization_alias="extractionStatus")
    extraction_error: str | None = Field(default=None, serialization_alias="extractionError")
    processing_order: int | None = Field(default=None, serialization_alias="processingOrder")
    progress_percent: int = Field(default=0, serialization_alias="progressPercent")
    current_step: str | None = Field(default=None, serialization_alias="currentStep")
    extracted_facts_count: int = Field(default=0, serialization_alias="extractedFactsCount")
    needs_review_count: int = Field(default=0, serialization_alias="needsReviewCount")
    approved_count: int = Field(default=0, serialization_alias="approvedCount")
    rejected_count: int = Field(default=0, serialization_alias="rejectedCount")
    uploaded_at: datetime = Field(serialization_alias="uploadedAt")
    processed_at: datetime | None = Field(default=None, serialization_alias="processedAt")
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class BrandSourceDocumentUploadItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: UUID
    filename: str
    status: str


class BrandSourceDocumentsUploadResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    batch_id: UUID = Field(serialization_alias="batchId")
    status: str
    documents: list[BrandSourceDocumentUploadItem]


class BrandImportBatchDocumentStatus(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    filename: str
    extraction_status: str = Field(serialization_alias="extractionStatus")
    progress_percent: int = Field(serialization_alias="progressPercent")
    current_step: str | None = Field(default=None, serialization_alias="currentStep")
    extracted_facts_count: int = Field(serialization_alias="extractedFactsCount")
    extraction_error: str | None = Field(default=None, serialization_alias="extractionError")


class BrandImportBatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    project_id: UUID = Field(serialization_alias="projectId")
    name: str | None = None
    source_type: str = Field(serialization_alias="sourceType")
    notes: str | None = None
    status: str
    progress_percent: int = Field(serialization_alias="progressPercent")
    current_step: str | None = Field(default=None, serialization_alias="currentStep")
    total_files: int = Field(serialization_alias="totalFiles")
    processed_files: int = Field(serialization_alias="processedFiles")
    total_facts: int = Field(serialization_alias="totalFacts")
    approved_facts: int = Field(serialization_alias="approvedFacts")
    rejected_facts: int = Field(serialization_alias="rejectedFacts")
    needs_review_facts: int = Field(serialization_alias="needsReviewFacts")
    error_message: str | None = Field(default=None, serialization_alias="errorMessage")
    warnings: list[str] = Field(default_factory=list)
    started_at: datetime | None = Field(default=None, serialization_alias="startedAt")
    completed_at: datetime | None = Field(default=None, serialization_alias="completedAt")
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class BrandImportBatchStatusResponse(BrandImportBatchRead):
    documents: list[BrandImportBatchDocumentStatus] = Field(default_factory=list)


class BrandImportBatchListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    name: str | None = None
    source_type: str = Field(serialization_alias="sourceType")
    status: str
    progress_percent: int = Field(serialization_alias="progressPercent")
    total_files: int = Field(serialization_alias="totalFiles")
    total_facts: int = Field(serialization_alias="totalFacts")
    needs_review_facts: int = Field(serialization_alias="needsReviewFacts")
    created_at: datetime = Field(serialization_alias="createdAt")
    completed_at: datetime | None = Field(default=None, serialization_alias="completedAt")


class BrandImportBatchStartResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    batch_id: UUID = Field(serialization_alias="batchId")
    status: str


class BrandExtractedFactRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    project_id: UUID = Field(serialization_alias="projectId")
    source_document_id: UUID | None = Field(default=None, serialization_alias="sourceDocumentId")
    batch_id: UUID | None = Field(default=None, serialization_alias="batchId")
    target_section: str = Field(serialization_alias="targetSection")
    target_entity_type: str | None = Field(default=None, serialization_alias="targetEntityType")
    field_name: str | None = Field(default=None, serialization_alias="fieldName")
    extracted_value: Any = Field(default=None, serialization_alias="extractedValue")
    source_excerpt: str | None = Field(default=None, serialization_alias="sourceExcerpt")
    confidence: float
    status: str
    ai_reasoning: str | None = Field(default=None, serialization_alias="aiReasoning")
    is_update_suggestion: bool = Field(default=False, serialization_alias="isUpdateSuggestion")
    existing_target_id: UUID | None = Field(default=None, serialization_alias="existingTargetId")
    update_mode: str = Field(default="create", serialization_alias="updateMode")
    previous_value: Any | None = Field(default=None, serialization_alias="previousValue")
    conflict_status: str = Field(default="none", serialization_alias="conflictStatus")
    source_created_at: datetime | None = Field(default=None, serialization_alias="sourceCreatedAt")
    import_round: int | None = Field(default=None, serialization_alias="importRound")
    reviewed_at: datetime | None = Field(default=None, serialization_alias="reviewedAt")
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class BrandExtractedFactUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    target_section: str | None = Field(default=None, validation_alias="targetSection")
    target_entity_type: str | None = Field(default=None, validation_alias="targetEntityType")
    field_name: str | None = Field(default=None, validation_alias="fieldName")
    extracted_value: Any | None = Field(default=None, validation_alias="extractedValue")
    status: str | None = None


class BrandExtractBatchRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    document_ids: list[UUID] = Field(validation_alias="documentIds")


class BrandApplyFactsRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    fact_ids: list[UUID] = Field(validation_alias="factIds")
    batch_id: UUID | None = Field(default=None, validation_alias="batchId")


class BrandApplyFactsResultItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    fact_id: UUID = Field(serialization_alias="factId")
    target_section: str = Field(serialization_alias="targetSection")
    field_name: str | None = Field(default=None, serialization_alias="fieldName")
    message: str


class BrandApplyFactsCounts(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    saved: int
    skipped: int
    needs_review: int = Field(serialization_alias="needsReview")
    rejected: int


class BrandApplyFactsResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    saved: list[BrandApplyFactsResultItem]
    skipped: list[BrandApplyFactsResultItem]
    counts: BrandApplyFactsCounts


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
