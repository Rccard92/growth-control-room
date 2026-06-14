"""Pydantic schemas for Content SEO editorial calendar."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal
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
    shopify_blog_id: str | None = Field(default=None, serialization_alias="shopifyBlogId")
    shopify_article_id: str | None = Field(default=None, serialization_alias="shopifyArticleId")
    shopify_status: str | None = Field(default=None, serialization_alias="shopifyStatus")
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


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
    h2_h3_structure: list[str] = Field(default_factory=list, serialization_alias="h2H3Structure")
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


def normalize_editorial_brief_payload(raw: dict) -> EditorialBriefPayload:
    """Sanitize AI or client brief JSON into a typed payload."""
    data = dict(raw)
    list_fields = {
        "secondaryKeywords": "secondary_keywords",
        "h2H3Structure": "h2_h3_structure",
        "productsToLink": "products_to_link",
        "faqToInclude": "faq_to_include",
        "claimsToAvoid": "claims_to_avoid",
        "safeClaimsToUse": "safe_claims_to_use",
        "internalLinksSuggestions": "internal_links_suggestions",
        "brandContextUsed": "brand_context_used",
        "warnings": "warnings",
    }
    for alias, field in list_fields.items():
        if alias in data:
            data[field] = _coerce_str_list(data.pop(alias))
        elif field in data:
            data[field] = _coerce_str_list(data[field])
    str_aliases = {
        "proposedTitle": "proposed_title",
        "searchIntent": "search_intent",
        "targetAudience": "target_audience",
        "primaryKeyword": "primary_keyword",
        "contentAngle": "content_angle",
        "recommendedCta": "recommended_cta",
        "metaTitle": "meta_title",
        "metaDescription": "meta_description",
    }
    for alias, field in str_aliases.items():
        if alias in data and field not in data:
            data[field] = str(data.pop(alias) or "")
        elif field in data and data[field] is not None:
            data[field] = str(data[field])
        else:
            data.setdefault(field, "")
    data.setdefault("notes", str(data.get("notes") or ""))
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


def normalize_editorial_article_payload(raw: dict) -> EditorialArticlePayload:
    """Sanitize AI or client article JSON into a typed payload."""
    from app.utils.html_sanitize import sanitize_editorial_article_html

    data = dict(raw)
    list_fields = {
        "tags": "tags",
        "linkedProducts": "linked_products",
        "warnings": "warnings",
        "brandContextUsed": "brand_context_used",
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
    profile = data.get("content_length_profile")
    if profile not in (None, "breve", "medio", "approfondito"):
        data["content_length_profile"] = None
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
