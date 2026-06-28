"""Pydantic schemas for Content SEO editorial calendar."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ContentSeoEditorialStatus = Literal[
    "idea",
    "brief_pending",
    "brief_approved",
    "draft_pending",
    "draft_review",
    "ready_to_publish",
    "scheduled",
    "published",
    "publish_error",
]

ContentSeoEditorialContentType = Literal[
    "educational_article",
    "product_guide",
    "recipe",
    "faq_objection_article",
    "product_comparison",
    "seasonal_article",
    "brand_storytelling",
]

ContentSeoEditorialObjective = Literal[
    "seo_traffic",
    "education",
    "push_products",
    "answer_objections",
    "support_ads",
    "support_email",
    "seasonal_content",
]

ContentSeoEditorialCommercialIntensity = Literal["soft", "balanced", "sales_oriented"]

ContentSeoEditorialFrequency = Literal[
    "daily",
    "every_2_days",
    "every_3_days",
    "every_4_days",
    "weekly",
    "twice_weekly",
    "custom",
]

EditorialWeekday = Literal[
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]


class ContentSeoEditorialItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    project_id: UUID = Field(serialization_alias="projectId")
    title: str
    content_type: str = Field(serialization_alias="contentType")
    planned_date: date = Field(serialization_alias="plannedDate")
    status: ContentSeoEditorialStatus
    objective: str | None = None
    primary_keyword: str | None = Field(default=None, serialization_alias="primaryKeyword")
    secondary_keywords: list[str] | None = Field(
        default=None, serialization_alias="secondaryKeywords"
    )
    target_audience: str | None = Field(default=None, serialization_alias="targetAudience")
    search_intent: str | None = Field(default=None, serialization_alias="searchIntent")
    commercial_intensity: str | None = Field(
        default=None, serialization_alias="commercialIntensity"
    )
    linked_shopify_product_id: UUID | None = Field(
        default=None, serialization_alias="linkedShopifyProductId"
    )
    linked_shopify_product_gid: str | None = Field(
        default=None, serialization_alias="linkedShopifyProductGid"
    )
    linked_shopify_product_title: str | None = Field(
        default=None, serialization_alias="linkedShopifyProductTitle"
    )
    linked_shopify_product_handle: str | None = Field(
        default=None, serialization_alias="linkedShopifyProductHandle"
    )
    linked_collection_id: UUID | None = Field(
        default=None, serialization_alias="linkedCollectionId"
    )
    linked_collection_title: str | None = Field(
        default=None, serialization_alias="linkedCollectionTitle"
    )
    notes: str | None = None
    brief_payload: dict | None = Field(default=None, serialization_alias="briefPayload")
    article_payload: dict | None = Field(default=None, serialization_alias="articlePayload")
    publishing_payload: dict | None = Field(default=None, serialization_alias="publishingPayload")
    image_payload: dict | None = Field(default=None, serialization_alias="imagePayload")
    shopify_blog_id: str | None = Field(default=None, serialization_alias="shopifyBlogId")
    shopify_article_id: str | None = Field(default=None, serialization_alias="shopifyArticleId")
    shopify_article_gid: str | None = Field(default=None, serialization_alias="shopifyArticleGid")
    shopify_article_admin_url: str | None = Field(
        default=None, serialization_alias="shopifyArticleAdminUrl"
    )
    shopify_article_public_url: str | None = Field(
        default=None, serialization_alias="shopifyArticlePublicUrl"
    )
    shopify_status: str | None = Field(default=None, serialization_alias="shopifyStatus")
    publish_status: str = Field(default="not_published", serialization_alias="publishStatus")
    publish_mode: str | None = Field(default=None, serialization_alias="publishMode")
    scheduled_publish_at: datetime | None = Field(
        default=None, serialization_alias="scheduledPublishAt"
    )
    published_at: datetime | None = Field(default=None, serialization_alias="publishedAt")
    last_publish_error: str | None = Field(default=None, serialization_alias="lastPublishError")
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")
    publishing_is_stale: bool = Field(default=False, serialization_alias="publishingIsStale")
    image_is_stale: bool = Field(default=False, serialization_alias="imageIsStale")


class ContentSeoEditorialItemCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: str
    content_type: ContentSeoEditorialContentType = Field(validation_alias="contentType")
    planned_date: date = Field(validation_alias="plannedDate")
    status: ContentSeoEditorialStatus = "idea"
    objective: ContentSeoEditorialObjective | None = None
    primary_keyword: str | None = Field(default=None, validation_alias="primaryKeyword")
    secondary_keywords: list[str] | None = Field(
        default=None, validation_alias="secondaryKeywords"
    )
    target_audience: str | None = Field(default=None, validation_alias="targetAudience")
    search_intent: str | None = Field(default=None, validation_alias="searchIntent")
    commercial_intensity: ContentSeoEditorialCommercialIntensity | None = Field(
        default=None, validation_alias="commercialIntensity"
    )
    linked_shopify_product_id: UUID | None = Field(
        default=None, validation_alias="linkedShopifyProductId"
    )
    linked_shopify_product_gid: str | None = Field(
        default=None, validation_alias="linkedShopifyProductGid"
    )
    linked_shopify_product_title: str | None = Field(
        default=None, validation_alias="linkedShopifyProductTitle"
    )
    linked_shopify_product_handle: str | None = Field(
        default=None, validation_alias="linkedShopifyProductHandle"
    )
    linked_collection_id: UUID | None = Field(
        default=None, validation_alias="linkedCollectionId"
    )
    linked_collection_title: str | None = Field(
        default=None, validation_alias="linkedCollectionTitle"
    )
    notes: str | None = None


class ContentSeoEditorialItemUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: str | None = None
    content_type: ContentSeoEditorialContentType | None = Field(
        default=None, validation_alias="contentType"
    )
    planned_date: date | None = Field(default=None, validation_alias="plannedDate")
    status: ContentSeoEditorialStatus | None = None
    objective: ContentSeoEditorialObjective | None = None
    primary_keyword: str | None = Field(default=None, validation_alias="primaryKeyword")
    secondary_keywords: list[str] | None = Field(
        default=None, validation_alias="secondaryKeywords"
    )
    target_audience: str | None = Field(default=None, validation_alias="targetAudience")
    search_intent: str | None = Field(default=None, validation_alias="searchIntent")
    commercial_intensity: ContentSeoEditorialCommercialIntensity | None = Field(
        default=None, validation_alias="commercialIntensity"
    )
    linked_shopify_product_id: UUID | None = Field(
        default=None, validation_alias="linkedShopifyProductId"
    )
    linked_shopify_product_gid: str | None = Field(
        default=None, validation_alias="linkedShopifyProductGid"
    )
    linked_shopify_product_title: str | None = Field(
        default=None, validation_alias="linkedShopifyProductTitle"
    )
    linked_shopify_product_handle: str | None = Field(
        default=None, validation_alias="linkedShopifyProductHandle"
    )
    linked_collection_id: UUID | None = Field(
        default=None, validation_alias="linkedCollectionId"
    )
    linked_collection_title: str | None = Field(
        default=None, validation_alias="linkedCollectionTitle"
    )
    notes: str | None = None


class ContentSeoEditorialItemListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: list[ContentSeoEditorialItemRead]
    month: str | None = None


class EditorialPlanGenerateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    start_date: date = Field(validation_alias="startDate")
    end_date: date = Field(validation_alias="endDate")
    frequency: ContentSeoEditorialFrequency
    preferred_weekdays: list[EditorialWeekday] | None = Field(
        default=None, validation_alias="preferredWeekdays"
    )
    content_types: list[ContentSeoEditorialContentType] = Field(
        validation_alias="contentTypes"
    )
    objectives: list[ContentSeoEditorialObjective] = Field(
        default_factory=list, validation_alias="objectives"
    )
    objective: ContentSeoEditorialObjective | None = None
    commercial_intensity: ContentSeoEditorialCommercialIntensity = Field(
        validation_alias="commercialIntensity"
    )
    linked_product_ids: list[UUID] = Field(
        default_factory=list, validation_alias="linkedProductIds"
    )
    avoid_product_ids: list[UUID] = Field(
        default_factory=list, validation_alias="avoidProductIds"
    )
    primary_keywords: list[str] = Field(
        default_factory=list, validation_alias="primaryKeywords"
    )
    notes: str = ""

    @model_validator(mode="after")
    def validate_plan(self) -> EditorialPlanGenerateRequest:
        if self.end_date < self.start_date:
            raise ValueError("La data fine deve essere successiva o uguale alla data inizio.")
        if not self.content_types:
            raise ValueError("Seleziona almeno una tipologia di contenuto.")
        if self.frequency in ("custom", "twice_weekly") and not self.preferred_weekdays:
            raise ValueError("Seleziona almeno un giorno preferito per questa frequenza.")
        if not self.objectives and self.objective:
            self.objectives = [self.objective]
        elif not self.objectives:
            self.objectives = ["education"]
        return self


class EditorialPlanGenerateResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: list[ContentSeoEditorialItemRead]
    dry_run: bool = Field(serialization_alias="dryRun")
    message: str = "Piano editoriale generato."


class EditorialItemRescheduleRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    planned_date: date = Field(validation_alias="plannedDate")
    cascade: bool = False


class EditorialItemRescheduleResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: list[ContentSeoEditorialItemRead]
    delta_days: int = Field(serialization_alias="deltaDays")
    warning: str | None = None


class EditorialBriefBatchStartRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    month: str
    only_status: str = Field(default="idea", validation_alias="onlyStatus")


class EditorialBriefBatchJobError(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    item_id: UUID = Field(serialization_alias="itemId")
    title: str
    message: str


class EditorialBriefBatchJobResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    job_id: UUID = Field(serialization_alias="jobId")
    status: str
    total_items: int = Field(serialization_alias="totalItems")
    completed_items: int = Field(serialization_alias="completedItems")
    failed_items: int = Field(serialization_alias="failedItems")
    current_item_title: str | None = Field(
        default=None, serialization_alias="currentItemTitle"
    )
    progress_percent: int = Field(serialization_alias="progressPercent")
    errors: list[EditorialBriefBatchJobError] = Field(default_factory=list)


BriefUpdateStatus = Literal["brief_pending", "brief_approved"]


def _coerce_str_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [line.strip() for line in value.splitlines() if line.strip()]
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            if item is None:
                continue
            text = str(item).strip()
            if text:
                out.append(text)
        return out
    return []


class EditorialAiGenerationSnapshot(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    model: str = ""
    model_tier: str = Field(default="", serialization_alias="modelTier")
    operation_key: str = Field(default="", serialization_alias="operationKey")
    context_profile: str = Field(default="", serialization_alias="contextProfile")
    estimated_total_cost: float | None = Field(
        default=None, serialization_alias="estimatedTotalCost"
    )
    input_tokens: int = Field(default=0, serialization_alias="inputTokens")
    output_tokens: int = Field(default=0, serialization_alias="outputTokens")
    generated_at: str = Field(default="", serialization_alias="generatedAt")
    generator_version: str = Field(default="", serialization_alias="generatorVersion")
    log_id: str = Field(default="", serialization_alias="logId")
    status: str = ""
    context_hash: str = Field(default="", serialization_alias="contextHash")
    prompt_hash: str = Field(default="", serialization_alias="promptHash")


class EditorialAiGenerationInfo(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    generated: bool = False
    model: str | None = None
    model_tier: str | None = Field(default=None, serialization_alias="modelTier")
    operation_key: str | None = Field(default=None, serialization_alias="operationKey")
    context_profile: str | None = Field(default=None, serialization_alias="contextProfile")
    estimated_total_cost: float | None = Field(
        default=None, serialization_alias="estimatedTotalCost"
    )
    input_tokens: int | None = Field(default=None, serialization_alias="inputTokens")
    output_tokens: int | None = Field(default=None, serialization_alias="outputTokens")
    created_at: str | None = Field(default=None, serialization_alias="createdAt")
    status: str | None = None
    error_message: str | None = Field(default=None, serialization_alias="errorMessage")
    generator_version: str | None = Field(default=None, serialization_alias="generatorVersion")
    log_id: str | None = Field(default=None, serialization_alias="logId")
    context_hash: str | None = Field(default=None, serialization_alias="contextHash")
    prompt_hash: str | None = Field(default=None, serialization_alias="promptHash")


class EditorialItemAiUsageResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    brief: EditorialAiGenerationInfo | None = None
    article: EditorialAiGenerationInfo | None = None
    image: EditorialAiGenerationInfo | None = None
    logs: list[EditorialAiGenerationInfo] = Field(default_factory=list)


class BriefH2Section(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    h2: str = ""
    h3: list[str] = Field(default_factory=list)


class EditorialBriefPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    proposed_title: str = Field(default="", serialization_alias="proposedTitle")
    search_intent: str = Field(default="", serialization_alias="searchIntent")
    target_audience: str = Field(default="", serialization_alias="targetAudience")
    primary_keyword: str = Field(default="", serialization_alias="primaryKeyword")
    secondary_keywords: list[str] = Field(
        default_factory=list, serialization_alias="secondaryKeywords"
    )
    content_angle: str = Field(default="", serialization_alias="contentAngle")
    h2_h3_structure: list[BriefH2Section] = Field(
        default_factory=list, serialization_alias="h2H3Structure"
    )
    products_to_link: list[str] = Field(default_factory=list, serialization_alias="productsToLink")
    faq_to_include: list[str] = Field(default_factory=list, serialization_alias="faqToInclude")
    claims_to_avoid: list[str] = Field(default_factory=list, serialization_alias="claimsToAvoid")
    safe_claims_to_use: list[str] = Field(
        default_factory=list, serialization_alias="safeClaimsToUse"
    )
    recommended_cta: str = Field(default="", serialization_alias="recommendedCta")
    meta_title: str = Field(default="", serialization_alias="metaTitle")
    meta_description: str = Field(default="", serialization_alias="metaDescription")
    internal_links_suggestions: list[str] = Field(
        default_factory=list, serialization_alias="internalLinksSuggestions"
    )
    notes: str = ""
    brand_context_used: list[str] = Field(
        default_factory=list, serialization_alias="brandContextUsed"
    )
    warnings: list[str] = Field(default_factory=list)
    author_suggestion: str = Field(default="", serialization_alias="authorSuggestion")
    author_reason: str = Field(default="", serialization_alias="authorReason")
    content_length_profile: str = Field(default="", serialization_alias="contentLengthProfile")
    community_cta_suggestion: str = Field(
        default="", serialization_alias="communityCtaSuggestion"
    )
    editorial_tone_notes: list[str] = Field(
        default_factory=list, serialization_alias="editorialToneNotes"
    )
    recommended_word_count_min: int | None = Field(
        default=None, serialization_alias="recommendedWordCountMin"
    )
    recommended_word_count_max: int | None = Field(
        default=None, serialization_alias="recommendedWordCountMax"
    )
    structure_complexity: str = Field(default="", serialization_alias="structureComplexity")
    max_h2: int | None = Field(default=None, serialization_alias="maxH2")
    max_h3: int | None = Field(default=None, serialization_alias="maxH3")
    avoid_repetitions: list[str] = Field(
        default_factory=list, serialization_alias="avoidRepetitions"
    )
    editorial_skill_checklist: list[str] = Field(
        default_factory=list, serialization_alias="editorialSkillChecklist"
    )
    suggested_html_blocks: list[str] = Field(
        default_factory=list, serialization_alias="suggestedHtmlBlocks"
    )
    internal_linking_plan: list[str] = Field(
        default_factory=list, serialization_alias="internalLinkingPlan"
    )
    readability_notes: list[str] = Field(
        default_factory=list, serialization_alias="readabilityNotes"
    )
    ai_generation: EditorialAiGenerationSnapshot | None = Field(
        default=None, serialization_alias="aiGeneration"
    )


_VALID_AUTHOR_SUGGESTIONS = frozenset({"", "Davide", "Filippo Leonardi", "Salvo Leonardi"})
_VALID_CONTENT_LENGTH_PROFILES = frozenset({"", "breve", "medio", "approfondito"})
_VALID_STRUCTURE_COMPLEXITY = frozenset({"", "snella", "media", "approfondita"})


def normalize_editorial_brief_payload(raw: dict) -> EditorialBriefPayload:
    """Sanitize AI or client brief JSON into a typed payload."""
    from app.services.content.editorial_structure_utils import coerce_h2_h3_structure

    data = dict(raw)
    list_fields = {
        "secondaryKeywords": "secondary_keywords",
        "productsToLink": "products_to_link",
        "faqToInclude": "faq_to_include",
        "claimsToAvoid": "claims_to_avoid",
        "safeClaimsToUse": "safe_claims_to_use",
        "internalLinksSuggestions": "internal_links_suggestions",
        "brandContextUsed": "brand_context_used",
        "warnings": "warnings",
        "editorialToneNotes": "editorial_tone_notes",
        "avoidRepetitions": "avoid_repetitions",
        "editorialSkillChecklist": "editorial_skill_checklist",
        "suggestedHtmlBlocks": "suggested_html_blocks",
        "internalLinkingPlan": "internal_linking_plan",
        "readabilityNotes": "readability_notes",
    }
    for alias, field in list_fields.items():
        if alias in data:
            data[field] = _coerce_str_list(data.pop(alias))
        elif field in data:
            data[field] = _coerce_str_list(data[field])

    h2_raw = data.pop("h2H3Structure", None)
    if h2_raw is None:
        h2_raw = data.get("h2_h3_structure")
    data["h2_h3_structure"] = coerce_h2_h3_structure(h2_raw)
    str_aliases = {
        "proposedTitle": "proposed_title",
        "searchIntent": "search_intent",
        "targetAudience": "target_audience",
        "primaryKeyword": "primary_keyword",
        "contentAngle": "content_angle",
        "recommendedCta": "recommended_cta",
        "metaTitle": "meta_title",
        "metaDescription": "meta_description",
        "authorSuggestion": "author_suggestion",
        "authorReason": "author_reason",
        "communityCtaSuggestion": "community_cta_suggestion",
    }
    for alias, field in str_aliases.items():
        if alias in data and field not in data:
            data[field] = str(data.pop(alias) or "")
        elif field in data and data[field] is not None:
            data[field] = str(data[field])
        else:
            data.setdefault(field, "")
    data.setdefault("notes", str(data.get("notes") or ""))
    if "contentLengthProfile" in data and "content_length_profile" not in data:
        data["content_length_profile"] = data.pop("contentLengthProfile")
    author = str(data.get("author_suggestion") or "").strip()
    data["author_suggestion"] = author if author in _VALID_AUTHOR_SUGGESTIONS else ""
    profile = str(data.get("content_length_profile") or "").strip()
    data["content_length_profile"] = (
        profile if profile in _VALID_CONTENT_LENGTH_PROFILES else ""
    )
    complexity = str(data.get("structure_complexity") or "").strip()
    if "structureComplexity" in data and "structure_complexity" not in data:
        complexity = str(data.pop("structureComplexity") or "").strip()
    data["structure_complexity"] = (
        complexity if complexity in _VALID_STRUCTURE_COMPLEXITY else ""
    )
    for int_alias, int_field in (
        ("recommendedWordCountMin", "recommended_word_count_min"),
        ("recommendedWordCountMax", "recommended_word_count_max"),
        ("maxH2", "max_h2"),
        ("maxH3", "max_h3"),
    ):
        if int_alias in data and int_field not in data:
            data[int_field] = data.pop(int_alias)
        val = data.get(int_field)
        if val is None or val == "":
            data[int_field] = None
        else:
            try:
                data[int_field] = int(val)
            except (TypeError, ValueError):
                data[int_field] = None
    if "aiGeneration" in data and "ai_generation" not in data:
        raw_ai = data.pop("aiGeneration")
        data["ai_generation"] = raw_ai if isinstance(raw_ai, dict) else None
    elif data.get("ai_generation") is not None and not isinstance(data.get("ai_generation"), dict):
        data["ai_generation"] = None
    return EditorialBriefPayload.model_validate(data)


class EditorialBriefUpdateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    brief_payload: dict = Field(validation_alias="briefPayload")
    status: BriefUpdateStatus | None = None

    @field_validator("brief_payload")
    @classmethod
    def validate_brief_object(cls, value: dict) -> dict:
        if not isinstance(value, dict):
            raise ValueError("briefPayload deve essere un oggetto JSON.")
        return value

    @model_validator(mode="after")
    def validate_approve(self) -> EditorialBriefUpdateRequest:
        if self.status == "brief_approved" and not self.brief_payload:
            raise ValueError("Il brief non può essere vuoto per l'approvazione.")
        return self


ArticleUpdateStatus = Literal["draft_pending", "draft_review", "ready_to_publish"]

SafeClaimSeverity = Literal["low", "medium", "high"]


class EditorialSafeClaimFlag(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    severity: SafeClaimSeverity = "medium"
    phrase: str = ""
    reason: str = ""
    suggestion: str = ""


class EditorialArticlePayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: str = ""
    handle: str = ""
    excerpt: str = ""
    body_html: str = Field(default="", serialization_alias="bodyHtml")
    body_markdown: str = Field(default="", serialization_alias="bodyMarkdown")
    seo_title: str = Field(default="", serialization_alias="seoTitle")
    meta_description: str = Field(default="", serialization_alias="metaDescription")
    tags: list[str] = Field(default_factory=list)
    linked_products: list[str] = Field(
        default_factory=list, serialization_alias="linkedProducts"
    )
    linked_collections: list[str] = Field(
        default_factory=list, serialization_alias="linkedCollections"
    )
    cta: str = ""
    author_name: str = Field(default="", serialization_alias="authorName")
    author_role: str = Field(default="", serialization_alias="authorRole")
    community_cta: str = Field(default="", serialization_alias="communityCta")
    estimated_reading_time: str = Field(
        default="", serialization_alias="estimatedReadingTime"
    )
    content_length_profile: Literal["breve", "medio", "approfondito"] | None = Field(
        default=None, serialization_alias="contentLengthProfile"
    )
    status: Literal["draft"] = "draft"
    warnings: list[str] = Field(default_factory=list)
    brand_context_used: list[str] = Field(
        default_factory=list, serialization_alias="brandContextUsed"
    )
    generated_at: str = Field(default="", serialization_alias="generatedAt")
    updated_at: str = Field(default="", serialization_alias="updatedAt")
    article_hash: str = Field(default="", serialization_alias="articleHash")
    readability_checklist: list[str] = Field(
        default_factory=list, serialization_alias="readabilityChecklist"
    )
    neuromarketing_elements: list[str] = Field(
        default_factory=list, serialization_alias="neuromarketingElements"
    )
    internal_link_suggestions: list[str] = Field(
        default_factory=list, serialization_alias="internalLinkSuggestions"
    )
    html_blocks_used: list[str] = Field(
        default_factory=list, serialization_alias="htmlBlocksUsed"
    )
    skill_pack_used: str = Field(default="", serialization_alias="skillPackUsed")
    skill_pack_version: str = Field(default="", serialization_alias="skillPackVersion")
    safe_claim_flags: list[EditorialSafeClaimFlag] = Field(
        default_factory=list, serialization_alias="safeClaimFlags"
    )
    ai_generation: EditorialAiGenerationSnapshot | None = Field(
        default=None, serialization_alias="aiGeneration"
    )


def normalize_editorial_article_payload(raw: dict) -> EditorialArticlePayload:
    """Sanitize AI or client article JSON into a typed payload."""
    from app.utils.html_sanitize import sanitize_editorial_article_html

    data = dict(raw)
    list_fields = {
        "tags": "tags",
        "linkedProducts": "linked_products",
        "linkedCollections": "linked_collections",
        "warnings": "warnings",
        "brandContextUsed": "brand_context_used",
        "readabilityChecklist": "readability_checklist",
        "neuromarketingElements": "neuromarketing_elements",
        "internalLinkSuggestions": "internal_link_suggestions",
        "htmlBlocksUsed": "html_blocks_used",
    }
    for alias, field in list_fields.items():
        if alias in data:
            data[field] = _coerce_str_list(data.pop(alias))
        elif field in data:
            data[field] = _coerce_str_list(data[field])
    str_aliases = {
        "title": "title",
        "handle": "handle",
        "excerpt": "excerpt",
        "bodyHtml": "body_html",
        "bodyMarkdown": "body_markdown",
        "seoTitle": "seo_title",
        "metaDescription": "meta_description",
        "cta": "cta",
        "authorName": "author_name",
        "authorRole": "author_role",
        "communityCta": "community_cta",
        "estimatedReadingTime": "estimated_reading_time",
        "generatedAt": "generated_at",
        "updatedAt": "updated_at",
        "articleHash": "article_hash",
        "skillPackUsed": "skill_pack_used",
        "skillPackVersion": "skill_pack_version",
    }
    for alias, field in str_aliases.items():
        if alias in data and field not in data:
            data[field] = str(data.pop(alias) or "")
        elif field in data and data[field] is not None:
            data[field] = str(data[field])
        else:
            data.setdefault(field, "")
    if "contentLengthProfile" in data and "content_length_profile" not in data:
        data["content_length_profile"] = data.pop("contentLengthProfile")
    if "aiGeneration" in data and "ai_generation" not in data:
        raw_ai = data.pop("aiGeneration")
        data["ai_generation"] = raw_ai if isinstance(raw_ai, dict) else None
    elif data.get("ai_generation") is not None and not isinstance(data.get("ai_generation"), dict):
        data["ai_generation"] = None
    profile = data.get("content_length_profile")
    if profile not in (None, "breve", "medio", "approfondito"):
        data["content_length_profile"] = None
    if "safeClaimFlags" in data and "safe_claim_flags" not in data:
        raw_flags = data.pop("safeClaimFlags")
        if isinstance(raw_flags, list):
            data["safe_claim_flags"] = [
                EditorialSafeClaimFlag.model_validate(f) if isinstance(f, dict) else f
                for f in raw_flags
            ]
        else:
            data["safe_claim_flags"] = []
    data.setdefault("status", "draft")
    payload = EditorialArticlePayload.model_validate(data)
    sanitized_html = sanitize_editorial_article_html(payload.body_html)
    return payload.model_copy(update={"body_html": sanitized_html})


class EditorialArticleUpdateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    article_payload: dict = Field(validation_alias="articlePayload")
    status: ArticleUpdateStatus | None = None

    @field_validator("article_payload")
    @classmethod
    def validate_article_object(cls, value: dict) -> dict:
        if not isinstance(value, dict):
            raise ValueError("articlePayload deve essere un oggetto JSON.")
        return value


EditorialPublishMode = Literal["draft", "publish_now", "schedule"]

EditorialPublishStatus = Literal[
    "not_published",
    "draft_created",
    "published",
    "publish_error",
    "scheduled",
]

EditorialScheduledPublishSource = Literal["ped_planned_date", "manual"]


class EditorialPublishingPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: str = ""
    handle: str = ""
    body_html: str = Field(default="", serialization_alias="bodyHtml")
    excerpt: str = ""
    seo_title: str = Field(default="", serialization_alias="seoTitle")
    meta_description: str = Field(default="", serialization_alias="metaDescription")
    author: str = ""
    blog_id: str | None = Field(default=None, serialization_alias="blogId")
    blog_gid: str | None = Field(default=None, serialization_alias="blogGid")
    tags: list[str] = Field(default_factory=list)
    image_url: str | None = Field(default=None, serialization_alias="imageUrl")
    image_alt: str | None = Field(default=None, serialization_alias="imageAlt")
    mode: EditorialPublishMode = "draft"
    is_published: bool = Field(default=False, serialization_alias="isPublished")
    publish_date: str | None = Field(default=None, serialization_alias="publishDate")
    template_suffix: str | None = Field(default=None, serialization_alias="templateSuffix")
    source_article_hash: str | None = Field(
        default=None, serialization_alias="sourceArticleHash"
    )
    source_article_updated_at: str | None = Field(
        default=None, serialization_alias="sourceArticleUpdatedAt"
    )
    synced_from_article_at: str | None = Field(
        default=None, serialization_alias="syncedFromArticleAt"
    )
    shopify_seo_synced: bool | None = Field(default=None, serialization_alias="shopifySeoSynced")
    shopify_seo_synced_at: str | None = Field(
        default=None, serialization_alias="shopifySeoSyncedAt"
    )
    shopify_seo_error: str | None = Field(default=None, serialization_alias="shopifySeoError")
    scheduled_publish_at: str | None = Field(
        default=None, serialization_alias="scheduledPublishAt"
    )
    scheduled_publish_timezone: str | None = Field(
        default=None, serialization_alias="scheduledPublishTimezone"
    )
    scheduled_publish_source: EditorialScheduledPublishSource | None = Field(
        default=None, serialization_alias="scheduledPublishSource"
    )
    source_planned_date: str | None = Field(
        default=None, serialization_alias="sourcePlannedDate"
    )
    scheduled_publish_time: str | None = Field(
        default=None, serialization_alias="scheduledPublishTime"
    )


class EditorialPublishingUpdateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    publishing_payload: dict = Field(validation_alias="publishingPayload")
    publish_mode: EditorialPublishMode | None = Field(default=None, validation_alias="publishMode")
    scheduled_publish_at: datetime | None = Field(
        default=None, validation_alias="scheduledPublishAt"
    )

    @field_validator("publishing_payload")
    @classmethod
    def validate_publishing_object(cls, value: dict) -> dict:
        if not isinstance(value, dict):
            raise ValueError("publishingPayload deve essere un oggetto JSON.")
        return value


EditorialImageStatus = Literal["not_generated", "generated", "uploaded", "upload_error", "approved"]


class EditorialApprovedImageBackup(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    image_url: str | None = Field(default=None, serialization_alias="imageUrl")
    image_storage_path: str | None = Field(default=None, serialization_alias="imageStoragePath")
    image_filename: str | None = Field(default=None, serialization_alias="imageFilename")
    image_alt: str | None = Field(default=None, serialization_alias="imageAlt")
    image_hash: str | None = Field(default=None, serialization_alias="imageHash")
    image_approved_at: str | None = Field(default=None, serialization_alias="imageApprovedAt")
    shopify_image_ready: bool = Field(default=False, serialization_alias="shopifyImageReady")
    image_width: int | None = Field(default=None, serialization_alias="imageWidth")
    image_height: int | None = Field(default=None, serialization_alias="imageHeight")
    image_mime_type: str | None = Field(default=None, serialization_alias="imageMimeType")


class EditorialImagePayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    image_status: EditorialImageStatus = Field(
        default="not_generated", serialization_alias="imageStatus"
    )
    image_prompt: str = Field(default="", serialization_alias="imagePrompt")
    image_revision_note: str | None = Field(default=None, serialization_alias="imageRevisionNote")
    image_model: str | None = Field(default=None, serialization_alias="imageModel")
    image_alt: str | None = Field(default=None, serialization_alias="imageAlt")
    image_url: str | None = Field(default=None, serialization_alias="imageUrl")
    image_storage_path: str | None = Field(default=None, serialization_alias="imageStoragePath")
    image_filename: str | None = Field(default=None, serialization_alias="imageFilename")
    image_original_provider_filename: str | None = Field(
        default=None, serialization_alias="imageOriginalProviderFilename"
    )
    image_width: int | None = Field(default=None, serialization_alias="imageWidth")
    image_height: int | None = Field(default=None, serialization_alias="imageHeight")
    image_aspect_ratio: str | None = Field(default=None, serialization_alias="imageAspectRatio")
    image_mime_type: str | None = Field(default=None, serialization_alias="imageMimeType")
    image_file_extension: str | None = Field(default=None, serialization_alias="imageFileExtension")
    image_provider_size: str | None = Field(default=None, serialization_alias="imageProviderSize")
    image_final_size: str | None = Field(default=None, serialization_alias="imageFinalSize")
    image_provider_requested_size: str | None = Field(
        default=None, serialization_alias="imageProviderRequestedSize"
    )
    image_provider_returned_size: str | None = Field(
        default=None, serialization_alias="imageProviderReturnedSize"
    )
    image_post_processing_applied: str | None = Field(
        default=None, serialization_alias="imagePostProcessingApplied"
    )
    image_revised_prompt: str | None = Field(default=None, serialization_alias="imageRevisedPrompt")
    generated_from_article_hash: str | None = Field(
        default=None, serialization_alias="generatedFromArticleHash"
    )
    approved_image_hash: str | None = Field(default=None, serialization_alias="approvedImageHash")
    image_generation_cost: float | None = Field(
        default=None, serialization_alias="imageGenerationCost"
    )
    image_generation_log_id: str | None = Field(
        default=None, serialization_alias="imageGenerationLogId"
    )
    image_approved_at: str | None = Field(default=None, serialization_alias="imageApprovedAt")
    image_hash: str | None = Field(default=None, serialization_alias="imageHash")
    source_article_hash: str | None = Field(
        default=None, serialization_alias="sourceArticleHash"
    )
    access_token: str | None = Field(default=None, serialization_alias="accessToken")
    updated_at: str | None = Field(default=None, serialization_alias="updatedAt")
    skill_pack_used: str = Field(default="", serialization_alias="skillPackUsed")
    skill_pack_version: str = Field(default="", serialization_alias="skillPackVersion")
    shopify_image_ready: bool = Field(default=False, serialization_alias="shopifyImageReady")
    image_storage_provider: str | None = Field(
        default=None, serialization_alias="imageStorageProvider"
    )
    shopify_file_id: str | None = Field(default=None, serialization_alias="shopifyFileId")
    shopify_media_gid: str | None = Field(default=None, serialization_alias="shopifyMediaGid")
    shopify_file_status: str | None = Field(default=None, serialization_alias="shopifyFileStatus")
    shopify_uploaded_at: str | None = Field(default=None, serialization_alias="shopifyUploadedAt")
    image_upload_error: str | None = Field(default=None, serialization_alias="imageUploadError")
    image_public_url: str | None = Field(default=None, serialization_alias="imagePublicUrl")
    shopify_image_synced_at: str | None = Field(
        default=None, serialization_alias="shopifyImageSyncedAt"
    )
    shopify_image_alt_synced: str | None = Field(
        default=None, serialization_alias="shopifyImageAltSynced"
    )
    shopify_image_filename_synced: str | None = Field(
        default=None, serialization_alias="shopifyImageFilenameSynced"
    )
    approved_image_backup: EditorialApprovedImageBackup | None = Field(
        default=None, serialization_alias="approvedImageBackup"
    )
    ai_generation: EditorialAiGenerationSnapshot | None = Field(
        default=None, serialization_alias="aiGeneration"
    )


def normalize_editorial_image_payload(raw: dict) -> EditorialImagePayload:
    data = dict(raw)
    str_aliases = {
        "imageStatus": "image_status",
        "imagePrompt": "image_prompt",
        "imageRevisionNote": "image_revision_note",
        "imageModel": "image_model",
        "imageAlt": "image_alt",
        "imageUrl": "image_url",
        "imageStoragePath": "image_storage_path",
        "imageFilename": "image_filename",
        "imageOriginalProviderFilename": "image_original_provider_filename",
        "imageWidth": "image_width",
        "imageHeight": "image_height",
        "imageAspectRatio": "image_aspect_ratio",
        "imageMimeType": "image_mime_type",
        "imageFileExtension": "image_file_extension",
        "imageProviderSize": "image_provider_size",
        "imageFinalSize": "image_final_size",
        "imageProviderRequestedSize": "image_provider_requested_size",
        "imageProviderReturnedSize": "image_provider_returned_size",
        "imagePostProcessingApplied": "image_post_processing_applied",
        "imageRevisedPrompt": "image_revised_prompt",
        "generatedFromArticleHash": "generated_from_article_hash",
        "approvedImageHash": "approved_image_hash",
        "imageGenerationCost": "image_generation_cost",
        "imageGenerationLogId": "image_generation_log_id",
        "imageApprovedAt": "image_approved_at",
        "imageHash": "image_hash",
        "sourceArticleHash": "source_article_hash",
        "accessToken": "access_token",
        "updatedAt": "updated_at",
        "skillPackUsed": "skill_pack_used",
        "skillPackVersion": "skill_pack_version",
        "shopifyImageReady": "shopify_image_ready",
        "imageStorageProvider": "image_storage_provider",
        "shopifyFileId": "shopify_file_id",
        "shopifyMediaGid": "shopify_media_gid",
        "shopifyFileStatus": "shopify_file_status",
        "shopifyUploadedAt": "shopify_uploaded_at",
        "imageUploadError": "image_upload_error",
        "imagePublicUrl": "image_public_url",
        "shopifyImageSyncedAt": "shopify_image_synced_at",
        "shopifyImageAltSynced": "shopify_image_alt_synced",
        "shopifyImageFilenameSynced": "shopify_image_filename_synced",
        "approvedImageBackup": "approved_image_backup",
        "aiGeneration": "ai_generation",
    }
    for alias, field in str_aliases.items():
        if alias in data and field not in data:
            data[field] = data.pop(alias)
    status = str(data.get("image_status") or "not_generated").strip()
    if status not in ("not_generated", "generated", "uploaded", "upload_error", "approved"):
        status = "not_generated"
    data["image_status"] = status
    if data.get("generated_from_article_hash") and not data.get("source_article_hash"):
        data["source_article_hash"] = data["generated_from_article_hash"]
    if data.get("source_article_hash") and not data.get("generated_from_article_hash"):
        data["generated_from_article_hash"] = data["source_article_hash"]
    cost = data.get("image_generation_cost")
    if cost is not None:
        try:
            data["image_generation_cost"] = float(cost)
        except (TypeError, ValueError):
            data["image_generation_cost"] = None
    for int_field in ("image_width", "image_height"):
        value = data.get(int_field)
        if value is not None:
            try:
                data[int_field] = int(value)
            except (TypeError, ValueError):
                data[int_field] = None
    ready = data.get("shopify_image_ready")
    if ready is not None:
        data["shopify_image_ready"] = bool(ready)
    backup = data.get("approved_image_backup")
    if backup and isinstance(backup, dict):
        backup_aliases = {
            "imageUrl": "image_url",
            "imageStoragePath": "image_storage_path",
            "imageFilename": "image_filename",
            "imageAlt": "image_alt",
            "imageHash": "image_hash",
            "imageApprovedAt": "image_approved_at",
            "shopifyImageReady": "shopify_image_ready",
            "imageWidth": "image_width",
            "imageHeight": "image_height",
            "imageMimeType": "image_mime_type",
        }
        for alias, field in backup_aliases.items():
            if alias in backup and field not in backup:
                backup[field] = backup.pop(alias)
        data["approved_image_backup"] = backup
    return EditorialImagePayload.model_validate(data)


class EditorialImageEditRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    revision_note: str = Field(min_length=1, validation_alias="revisionNote")


class EditorialImageActionResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    item: ContentSeoEditorialItemRead
    warnings: list[str] = Field(default_factory=list)


class EditorialPublishShopifyRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    mode: EditorialPublishMode = "draft"


class EditorialPublishShopifyErrorDetail(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    message: str
    code: str
    details: dict[str, Any] = Field(default_factory=dict)


class EditorialPublishShopifyResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    item: ContentSeoEditorialItemRead
    warnings: list[str] = Field(default_factory=list)


class ShopifyBlogListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    shopify_blog_id: str = Field(serialization_alias="shopifyBlogId")
    gid: str
    title: str
    handle: str | None = None


class ShopifyBlogsListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    blogs: list[ShopifyBlogListItem] = Field(default_factory=list)
    sync_required: bool = Field(default=False, serialization_alias="syncRequired")
