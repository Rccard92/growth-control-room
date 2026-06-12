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
    shopify_scopes: str = "read_products,read_orders,read_content,write_content,read_reports"
    shopify_redirect_uri: str | None = None
    frontend_url: str | None = None

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
