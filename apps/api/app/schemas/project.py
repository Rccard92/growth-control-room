from datetime import datetime
from urllib.parse import urlparse, urlunparse
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


def normalize_public_site_url(value: str | None) -> str | None:
    if value is None:
        return None
    trimmed = value.strip()
    if not trimmed:
        return None

    candidate = trimmed
    parsed = urlparse(candidate)
    scheme = (parsed.scheme or "").lower()
    if scheme not in ("http", "https"):
        if "://" in candidate:
            raise ValueError("Il dominio pubblico deve usare http o https")
        candidate = f"https://{candidate.lstrip('/')}"
        parsed = urlparse(candidate)
        scheme = (parsed.scheme or "").lower()

    if scheme not in ("http", "https"):
        raise ValueError("Il dominio pubblico deve usare http o https")
    if not parsed.netloc:
        raise ValueError("Il dominio pubblico non è valido")

    path = parsed.path or ""
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")

    normalized = urlunparse(
        (
            scheme,
            parsed.netloc.lower(),
            path,
            "",
            "",
            "",
        )
    )
    if normalized.endswith("/") and parsed.path in ("", "/"):
        normalized = normalized.rstrip("/")
    return normalized


class ProjectCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    public_site_url: str | None = Field(default=None, validation_alias="publicSiteUrl")

    @field_validator("public_site_url", mode="before")
    @classmethod
    def validate_public_site_url_create(cls, value: object) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("Il dominio pubblico deve essere una stringa")
        return normalize_public_site_url(value)


class ProjectUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    public_site_url: str | None = Field(default=None, validation_alias="publicSiteUrl")
    search_console_site_url: str | None = Field(
        default=None,
        validation_alias="searchConsoleSiteUrl",
    )
    google_analytics_property_id: str | None = Field(
        default=None,
        validation_alias="googleAnalyticsPropertyId",
    )
    google_analytics_property_name: str | None = Field(
        default=None,
        validation_alias="googleAnalyticsPropertyName",
    )
    google_merchant_account_id: str | None = Field(
        default=None,
        validation_alias="googleMerchantAccountId",
    )
    google_merchant_account_name: str | None = Field(
        default=None,
        validation_alias="googleMerchantAccountName",
    )

    @field_validator("public_site_url", mode="before")
    @classmethod
    def validate_public_site_url_update(cls, value: object) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("Il dominio pubblico deve essere una stringa")
        return normalize_public_site_url(value)

    @field_validator("search_console_site_url", mode="before")
    @classmethod
    def validate_search_console_site_url_update(cls, value: object) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("La proprietà Search Console deve essere una stringa")
        trimmed = value.strip()
        return trimmed or None

    @field_validator("google_analytics_property_id", mode="before")
    @classmethod
    def validate_google_analytics_property_id_update(cls, value: object) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("L'ID proprietà GA4 deve essere una stringa")
        trimmed = value.strip()
        return trimmed or None

    @field_validator("google_analytics_property_name", mode="before")
    @classmethod
    def validate_google_analytics_property_name_update(cls, value: object) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("Il nome proprietà GA4 deve essere una stringa")
        trimmed = value.strip()
        return trimmed or None

    @field_validator("google_merchant_account_id", mode="before")
    @classmethod
    def validate_google_merchant_account_id_update(cls, value: object) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("L'ID account Merchant deve essere una stringa")
        trimmed = value.strip()
        return trimmed or None

    @field_validator("google_merchant_account_name", mode="before")
    @classmethod
    def validate_google_merchant_account_name_update(cls, value: object) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("Il nome account Merchant deve essere una stringa")
        trimmed = value.strip()
        return trimmed or None


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    name: str
    slug: str
    description: str | None = None
    public_site_url: str | None = Field(default=None, serialization_alias="publicSiteUrl")
    search_console_site_url: str | None = Field(
        default=None,
        serialization_alias="searchConsoleSiteUrl",
    )
    google_analytics_property_id: str | None = Field(
        default=None,
        serialization_alias="googleAnalyticsPropertyId",
    )
    google_analytics_property_name: str | None = Field(
        default=None,
        serialization_alias="googleAnalyticsPropertyName",
    )
    google_merchant_account_id: str | None = Field(
        default=None,
        serialization_alias="googleMerchantAccountId",
    )
    google_merchant_account_name: str | None = Field(
        default=None,
        serialization_alias="googleMerchantAccountName",
    )
    status: str
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value: object) -> str:
        if hasattr(value, "value"):
            return str(value.value)
        return str(value)
