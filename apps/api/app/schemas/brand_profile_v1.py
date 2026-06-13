from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

SourceFetchStatus = Literal["fetched", "blocked", "failed"]
SourceQuality = Literal["high", "medium", "low"]


class BrandProfileEnrichRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    brand_name: str = Field(validation_alias="brandName")
    website_url: str | None = Field(default=None, validation_alias="websiteUrl")
    instagram_url: str | None = Field(default=None, validation_alias="instagramUrl")
    facebook_url: str | None = Field(default=None, validation_alias="facebookUrl")
    tiktok_url: str | None = Field(default=None, validation_alias="tiktokUrl")
    youtube_url: str | None = Field(default=None, validation_alias="youtubeUrl")
    linkedin_url: str | None = Field(default=None, validation_alias="linkedinUrl")
    trustpilot_url: str | None = Field(default=None, validation_alias="trustpilotUrl")
    google_business_url: str | None = Field(default=None, validation_alias="googleBusinessUrl")
    other_sources: list[dict[str, Any]] = Field(
        default_factory=list, validation_alias="otherSources"
    )


class BrandProfileProposal(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    brand_name: str | None = Field(default=None, validation_alias="brandName", serialization_alias="brandName")
    short_description: str | None = Field(
        default=None, validation_alias="shortDescription", serialization_alias="shortDescription"
    )
    story: str | None = None
    mission: str | None = None
    values: list[str] = Field(default_factory=list)
    differentiators: list[str] = Field(default_factory=list)
    origin_notes: str | None = Field(
        default=None, validation_alias="originNotes", serialization_alias="originNotes"
    )
    production_notes: str | None = Field(
        default=None, validation_alias="productionNotes", serialization_alias="productionNotes"
    )
    tone_notes: str | None = Field(
        default=None, validation_alias="toneNotes", serialization_alias="toneNotes"
    )
    customer_notes: str | None = Field(
        default=None, validation_alias="customerNotes", serialization_alias="customerNotes"
    )
    ai_summary: str | None = Field(
        default=None, validation_alias="aiSummary", serialization_alias="aiSummary"
    )

    @field_validator("values", "differentiators", mode="before")
    @classmethod
    def _coerce_lists(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(v) for v in value if v]
        return []


class BrandProfileSourceResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type: str
    url: str
    status: SourceFetchStatus
    quality: SourceQuality | None = None
    warning: str | None = None


class BrandProfileEnrichResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    proposal: BrandProfileProposal
    sources: list[BrandProfileSourceResult]
    confidence: float
    warnings: list[str] = Field(default_factory=list)


class BrandProfileApplyProposalRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    proposal: BrandProfileProposal
    confidence: float | None = None
    warnings: list[str] | None = None
