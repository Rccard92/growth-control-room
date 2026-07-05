from pydantic import BaseModel, ConfigDict, Field


class GoogleServiceStatus(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    status: str
    configured: bool | None = None
    message: str | None = None


class GoogleIntegrationStatusResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pagespeed: GoogleServiceStatus
    crux: GoogleServiceStatus
    oauth: GoogleServiceStatus
    search_console: GoogleServiceStatus = Field(serialization_alias="searchConsole")
    analytics: GoogleServiceStatus
    google_ads: GoogleServiceStatus = Field(serialization_alias="googleAds")


class GoogleOAuthStartRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    services: list[str] | None = None


class GoogleOAuthStartResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    authorization_url: str = Field(serialization_alias="authorizationUrl")
