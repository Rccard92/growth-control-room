from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

LOCAL_DATABASE_URL = (
    "postgresql+asyncpg://gcr:gcr_dev@localhost:5432/growth_control_room"
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str | None = None
    cors_origins: str = "*"
    app_env: str = "production"
    shopify_client_id: str | None = None
    shopify_client_secret: str | None = None
    shopify_scopes: str = (
        "read_products,read_orders,read_content,write_content,read_reports,read_files,write_files"
    )
    shopify_redirect_uri: str | None = None
    frontend_url: str | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    claude_model: str = "claude-3-5-sonnet-latest"
    claude_model_fast: str | None = None
    claude_model_deep: str | None = None
    claude_timeout_seconds: float = 90.0
    openai_model: str = "gpt-4o-mini"
    openai_model_cheap: str | None = None
    openai_model_standard: str | None = None
    openai_model_premium: str | None = "gpt-4o"
    openai_model_reasoning: str | None = None
    openai_model_fallback: str | None = None
    ai_allow_model_override: bool = False
    ai_enable_model_fallback_on_schema_error: bool = False
    ai_daily_budget_usd: float | None = None
    ai_monthly_budget_usd: float | None = None
    ai_single_request_warn_usd: float | None = None
    ai_single_request_block_usd: float | None = None
    ai_log_prompt_preview: bool = False
    editorial_images_dir: str = "data/editorial-images"
    public_api_base_url: str | None = None
    openai_image_model: str = "gpt-image-2"
    editorial_image_storage_provider: str = "shopify_files"
    editorial_image_public_base_url: str | None = None
    editorial_image_s3_bucket: str | None = None
    editorial_image_s3_region: str = "auto"
    editorial_image_s3_access_key: str | None = None
    editorial_image_s3_secret_key: str | None = None
    editorial_image_s3_endpoint_url: str | None = None
    google_pagespeed_api_key: str | None = None
    google_crux_api_key: str | None = None
    google_oauth_client_id: str | None = None
    google_oauth_client_secret: str | None = None
    google_oauth_redirect_uri: str | None = None
    google_ads_developer_token: str | None = None

    @model_validator(mode="after")
    def require_database_url(self) -> "Settings":
        if self.database_url:
            return self
        if self.app_env == "development":
            self.database_url = LOCAL_DATABASE_URL
            return self
        raise ValueError("DATABASE_URL environment variable is required")

    @staticmethod
    def _normalize_base_url(url: str) -> str:
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql://", 1)
        return url

    @property
    def shopify_oauth_configured(self) -> bool:
        return all(
            [
                self.shopify_client_id,
                self.shopify_client_secret,
                self.shopify_redirect_uri,
                self.frontend_url,
            ]
        )

    @property
    def shopify_oauth_missing_vars(self) -> list[str]:
        missing: list[str] = []
        if not self.shopify_client_id:
            missing.append("SHOPIFY_CLIENT_ID")
        if not self.shopify_client_secret:
            missing.append("SHOPIFY_CLIENT_SECRET")
        if not self.shopify_redirect_uri:
            missing.append("SHOPIFY_REDIRECT_URI")
        if not self.frontend_url:
            missing.append("FRONTEND_URL")
        return missing

    @property
    def google_oauth_configured(self) -> bool:
        return all(
            [
                self.google_oauth_client_id,
                self.google_oauth_client_secret,
                self.google_oauth_redirect_uri,
                self.frontend_url,
            ]
        )

    @property
    def google_oauth_missing_vars(self) -> list[str]:
        missing: list[str] = []
        if not self.google_oauth_client_id:
            missing.append("GOOGLE_OAUTH_CLIENT_ID")
        if not self.google_oauth_client_secret:
            missing.append("GOOGLE_OAUTH_CLIENT_SECRET")
        if not self.google_oauth_redirect_uri:
            missing.append("GOOGLE_OAUTH_REDIRECT_URI")
        if not self.frontend_url:
            missing.append("FRONTEND_URL")
        return missing

    @property
    def cors_origins_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def cors_allow_credentials(self) -> bool:
        return self.cors_origins_list != ["*"]

    @property
    def database_url_async(self) -> str:
        url = self._normalize_base_url(self.database_url or "")
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    @property
    def database_url_sync(self) -> str:
        url = self._normalize_base_url(self.database_url or "")
        if url.startswith("postgresql+asyncpg://"):
            return url.replace("+asyncpg", "+psycopg", 1)
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+psycopg://", 1)
        return url


settings = Settings()
