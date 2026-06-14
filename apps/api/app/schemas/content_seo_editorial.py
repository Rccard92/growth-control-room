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
    objective: ContentSeoEditorialObjective
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
        return self


class EditorialPlanGenerateResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: list[ContentSeoEditorialItemRead]
    dry_run: bool = Field(serialization_alias="dryRun")
    message: str = "Piano editoriale generato."
