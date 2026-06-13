from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

ModuleCompletionStatus = Literal["complete", "partial", "empty"]


class BrandIdentityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    project_id: UUID = Field(serialization_alias="projectId")
    positioning: str | None = None
    brand_values: list[str] | None = Field(default=None, serialization_alias="brandValues")
    differentiators: list[str] | None = None
    production_principles: list[str] | None = Field(
        default=None, serialization_alias="productionPrinciples"
    )
    quality_principles: list[str] | None = Field(
        default=None, serialization_alias="qualityPrinciples"
    )
    trust_elements: list[str] | None = Field(default=None, serialization_alias="trustElements")
    what_brand_is: str | None = Field(default=None, serialization_alias="whatBrandIs")
    what_brand_is_not: str | None = Field(default=None, serialization_alias="whatBrandIsNot")
    storytelling_notes: str | None = Field(default=None, serialization_alias="storytellingNotes")
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class BrandIdentityUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    positioning: str | None = None
    brand_values: list[str] | None = Field(default=None, validation_alias="brandValues")
    differentiators: list[str] | None = None
    production_principles: list[str] | None = Field(
        default=None, validation_alias="productionPrinciples"
    )
    quality_principles: list[str] | None = Field(default=None, validation_alias="qualityPrinciples")
    trust_elements: list[str] | None = Field(default=None, validation_alias="trustElements")
    what_brand_is: str | None = Field(default=None, validation_alias="whatBrandIs")
    what_brand_is_not: str | None = Field(default=None, validation_alias="whatBrandIsNot")
    storytelling_notes: str | None = Field(default=None, validation_alias="storytellingNotes")


class VisualColorSwatch(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    hex: str
    role: str | None = None
    label: str | None = None
    confidence: float | None = None


class VisualFontEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    role: str | None = None
    usage: str | None = None


class BrandVisualIdentityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    project_id: UUID = Field(serialization_alias="projectId")
    primary_logo_url: str | None = Field(default=None, serialization_alias="primaryLogoUrl")
    secondary_logo_url: str | None = Field(default=None, serialization_alias="secondaryLogoUrl")
    favicon_url: str | None = Field(default=None, serialization_alias="faviconUrl")
    primary_color: str | None = Field(default=None, serialization_alias="primaryColor")
    secondary_color: str | None = Field(default=None, serialization_alias="secondaryColor")
    accent_color: str | None = Field(default=None, serialization_alias="accentColor")
    background_color: str | None = Field(default=None, serialization_alias="backgroundColor")
    text_color: str | None = Field(default=None, serialization_alias="textColor")
    color_palette: list[dict[str, Any]] | None = Field(
        default=None, serialization_alias="colorPalette"
    )
    fonts: list[dict[str, Any]] | None = None
    visual_style_notes: str | None = Field(default=None, serialization_alias="visualStyleNotes")
    image_style_notes: str | None = Field(default=None, serialization_alias="imageStyleNotes")
    do_show: list[str] | None = Field(default=None, serialization_alias="doShow")
    do_not_show: list[str] | None = Field(default=None, serialization_alias="doNotShow")
    website_extracted_palette: list[dict[str, Any]] | None = Field(
        default=None, serialization_alias="websiteExtractedPalette"
    )
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class BrandVisualIdentityUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    primary_logo_url: str | None = Field(default=None, validation_alias="primaryLogoUrl")
    secondary_logo_url: str | None = Field(default=None, validation_alias="secondaryLogoUrl")
    favicon_url: str | None = Field(default=None, validation_alias="faviconUrl")
    primary_color: str | None = Field(default=None, validation_alias="primaryColor")
    secondary_color: str | None = Field(default=None, validation_alias="secondaryColor")
    accent_color: str | None = Field(default=None, validation_alias="accentColor")
    background_color: str | None = Field(default=None, validation_alias="backgroundColor")
    text_color: str | None = Field(default=None, validation_alias="textColor")
    color_palette: list[dict[str, Any]] | None = Field(default=None, validation_alias="colorPalette")
    fonts: list[dict[str, Any]] | None = None
    visual_style_notes: str | None = Field(default=None, validation_alias="visualStyleNotes")
    image_style_notes: str | None = Field(default=None, validation_alias="imageStyleNotes")
    do_show: list[str] | None = Field(default=None, validation_alias="doShow")
    do_not_show: list[str] | None = Field(default=None, validation_alias="doNotShow")


class VisualExtractRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    website_url: str = Field(validation_alias="websiteUrl")


class VisualExtractProposal(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    primary_logo_url: str | None = Field(default=None, serialization_alias="primaryLogoUrl")
    favicon_url: str | None = Field(default=None, serialization_alias="faviconUrl")
    color_palette: list[VisualColorSwatch] = Field(
        default_factory=list, serialization_alias="colorPalette"
    )
    fonts: list[VisualFontEntry] = Field(default_factory=list)
    visual_style_notes: str | None = Field(default=None, serialization_alias="visualStyleNotes")

    @field_validator("color_palette", mode="before")
    @classmethod
    def _coerce_palette(cls, value: Any) -> list:
        if value is None:
            return []
        return value

    @field_validator("fonts", mode="before")
    @classmethod
    def _coerce_fonts(cls, value: Any) -> list:
        if value is None:
            return []
        return value


class VisualExtractResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    proposal: VisualExtractProposal
    warnings: list[str] = Field(default_factory=list)


class VisualApplyProposalRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    proposal: VisualExtractProposal


class BrandModuleStatus(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    key: str
    label: str
    status: ModuleCompletionStatus
    missing_fields: list[str] = Field(default_factory=list, serialization_alias="missingFields")
    updated_at: datetime | None = Field(default=None, serialization_alias="updatedAt")
