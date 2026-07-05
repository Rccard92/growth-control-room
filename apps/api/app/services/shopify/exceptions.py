"""Shopify integration service-layer exceptions."""


class ShopifyIntegrationNotConnectedError(Exception):
    """Raised when Shopify is not connected for the project."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class ShopifyIntegrationPermissionError(Exception):
    """Raised when Shopify token lacks required scopes."""

    def __init__(self, message: str, *, missing_scopes: list[str] | None = None) -> None:
        super().__init__(message)
        self.missing_scopes = missing_scopes or []


class ShopifyCommerceApiError(Exception):
    """Raised when a Shopify commerce API request fails."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
