"""Pydantic schemas for BrandSectionDraft payloads."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.brand_intelligence import (
    BrandProfileUpdate,
    BrandSeoStrategyUpdate,
    BrandVoiceUpdate,
)

SECTION_DRAFT_KEYS = frozenset(
    {
        "brand_profile",
        "voice_tone",
        "products_categories",
        "audience",
        "claims_compliance",
        "seo_strategy",
        "content_pillars",
        "ai_guardrails",
        "assets",
    }
)

SECTION_DRAFT_LABELS: dict[str, str] = {
    "brand_profile": "Brand Profile",
    "voice_tone": "Voice & Tone",
    "products_categories": "Products & Categories",
    "audience": "Audience",
    "claims_compliance": "Claims & Compliance",
    "seo_strategy": "SEO Strategy",
    "content_pillars": "Content Pillars",
    "ai_guardrails": "AI Guardrails",
    "assets": "Assets",
}

FACT_SECTION_TO_DRAFT: dict[str, str] = {
    "brand_profile": "brand_profile",
    "voice_tone": "voice_tone",
    "product_knowledge": "products_categories",
    "category_knowledge": "products_categories",
    "audience": "audience",
    "claims_compliance": "claims_compliance",
    "seo_strategy": "seo_strategy",
    "content_pillars": "content_pillars",
    "ai_guardrails": "ai_guardrails",
    "assets": "assets",
}


class ProductDraftItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    description: str | None = None
    entity_type: str = Field(default="product", validation_alias="entityType")


class AudienceDraftItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    segment_name: str = Field(validation_alias="segmentName")
    description: str | None = None


class ClaimDraftItem(BaseModel):
    title: str
    description: str | None = None


class PillarDraftItem(BaseModel):
    name: str
    description: str | None = None


class GuardrailDraftItem(BaseModel):
    title: str
    description: str | None = None
    rule_type: str = Field(default="must_not", validation_alias="ruleType")


class AssetDraftItem(BaseModel):
    name: str
    value: str | None = None
    asset_type: str = Field(default="other", validation_alias="assetType")


class ProductsCategoriesDraftPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    products: list[ProductDraftItem] = Field(default_factory=list)
    categories: list[ProductDraftItem] = Field(default_factory=list)


class AudienceDraftPayload(BaseModel):
    segments: list[AudienceDraftItem] = Field(default_factory=list)


class ClaimsDraftPayload(BaseModel):
    allowed: list[ClaimDraftItem] = Field(default_factory=list)
    forbidden: list[ClaimDraftItem] = Field(default_factory=list)
    caution: list[ClaimDraftItem] = Field(default_factory=list)
    disclaimers: list[ClaimDraftItem] = Field(default_factory=list)


class ContentPillarsDraftPayload(BaseModel):
    pillars: list[PillarDraftItem] = Field(default_factory=list)


class GuardrailsDraftPayload(BaseModel):
    guardrails: list[GuardrailDraftItem] = Field(default_factory=list)


class AssetsDraftPayload(BaseModel):
    assets: list[AssetDraftItem] = Field(default_factory=list)


class SectionDraftWarnings(BaseModel):
    messages: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list, validation_alias="missingInformation")

    model_config = ConfigDict(populate_by_name=True)


def validate_draft_payload(section_key: str, payload: Any) -> dict[str, Any]:
    if section_key == "brand_profile":
        return BrandProfileUpdate.model_validate(payload or {}).model_dump(exclude_unset=True)
    if section_key == "voice_tone":
        return BrandVoiceUpdate.model_validate(payload or {}).model_dump(exclude_unset=True)
    if section_key == "seo_strategy":
        return BrandSeoStrategyUpdate.model_validate(payload or {}).model_dump(exclude_unset=True)
    if section_key == "products_categories":
        return ProductsCategoriesDraftPayload.model_validate(payload or {}).model_dump()
    if section_key == "audience":
        return AudienceDraftPayload.model_validate(payload or {}).model_dump()
    if section_key == "claims_compliance":
        return ClaimsDraftPayload.model_validate(payload or {}).model_dump()
    if section_key == "content_pillars":
        return ContentPillarsDraftPayload.model_validate(payload or {}).model_dump()
    if section_key == "ai_guardrails":
        return GuardrailsDraftPayload.model_validate(payload or {}).model_dump()
    if section_key == "assets":
        return AssetsDraftPayload.model_validate(payload or {}).model_dump()
    raise ValueError(f"Sezione draft non valida: {section_key}")
