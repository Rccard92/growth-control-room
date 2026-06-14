from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.services.brand_intelligence.faq_objections_normalize import normalize_to_string_list

DefaultArticleLength = Literal["breve", "medio", "approfondito"]


def _coerce_string_list(value: object | None) -> list[str] | None:
    if value is None:
        return None
    return normalize_to_string_list(value)


class BrandPersonEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = ""
    role: str = ""
    when_to_use: str = Field(default="", validation_alias="whenToUse", serialization_alias="whenToUse")
    tone: str = ""


def _coerce_brand_people(value: object | None) -> list[BrandPersonEntry] | None:
    if value is None:
        return None
    if not isinstance(value, list):
        return None
    out: list[BrandPersonEntry] = []
    for item in value:
        if isinstance(item, dict):
            out.append(BrandPersonEntry.model_validate(item))
        elif isinstance(item, BrandPersonEntry):
            out.append(item)
    return out


class BrandEditorialGuidelinesRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    project_id: UUID = Field(serialization_alias="projectId")
    content_philosophy: str | None = Field(
        default=None, serialization_alias="contentPhilosophy"
    )
    article_length_policy: str | None = Field(
        default=None, serialization_alias="articleLengthPolicy"
    )
    reading_style: str | None = Field(default=None, serialization_alias="readingStyle")
    storytelling_rules: list[str] | None = Field(
        default=None, serialization_alias="storytellingRules"
    )
    brand_people: list[BrandPersonEntry] | None = Field(
        default=None, serialization_alias="brandPeople"
    )
    author_voice_rules: list[str] | None = Field(
        default=None, serialization_alias="authorVoiceRules"
    )
    community_cta_rules: list[str] | None = Field(
        default=None, serialization_alias="communityCtaRules"
    )
    article_dos: list[str] | None = Field(default=None, serialization_alias="articleDos")
    article_donts: list[str] | None = Field(default=None, serialization_alias="articleDonts")
    default_article_length: DefaultArticleLength | None = Field(
        default=None, serialization_alias="defaultArticleLength"
    )
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")

    @field_validator(
        "storytelling_rules",
        "author_voice_rules",
        "community_cta_rules",
        "article_dos",
        "article_donts",
        mode="before",
    )
    @classmethod
    def _normalize_list_fields(cls, value: object | None) -> list[str] | None:
        return _coerce_string_list(value)

    @field_validator("brand_people", mode="before")
    @classmethod
    def _normalize_brand_people(cls, value: object | None) -> list[BrandPersonEntry] | None:
        return _coerce_brand_people(value)


class BrandEditorialGuidelinesUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    content_philosophy: str | None = Field(
        default=None, validation_alias="contentPhilosophy"
    )
    article_length_policy: str | None = Field(
        default=None, validation_alias="articleLengthPolicy"
    )
    reading_style: str | None = Field(default=None, validation_alias="readingStyle")
    storytelling_rules: list[str] | None = Field(
        default=None, validation_alias="storytellingRules"
    )
    brand_people: list[BrandPersonEntry] | None = Field(
        default=None, validation_alias="brandPeople"
    )
    author_voice_rules: list[str] | None = Field(
        default=None, validation_alias="authorVoiceRules"
    )
    community_cta_rules: list[str] | None = Field(
        default=None, validation_alias="communityCtaRules"
    )
    article_dos: list[str] | None = Field(default=None, validation_alias="articleDos")
    article_donts: list[str] | None = Field(default=None, validation_alias="articleDonts")
    default_article_length: DefaultArticleLength | None = Field(
        default=None, validation_alias="defaultArticleLength"
    )

    @field_validator(
        "storytelling_rules",
        "author_voice_rules",
        "community_cta_rules",
        "article_dos",
        "article_donts",
        mode="before",
    )
    @classmethod
    def _normalize_list_fields(cls, value: object | None) -> list[str] | None:
        return _coerce_string_list(value)

    @field_validator("brand_people", mode="before")
    @classmethod
    def _normalize_brand_people(cls, value: object | None) -> list[BrandPersonEntry] | None:
        return _coerce_brand_people(value)
