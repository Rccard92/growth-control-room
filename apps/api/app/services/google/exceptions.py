"""Google API service-layer exceptions."""


class GoogleIntegrationNotConfiguredError(Exception):
    """Raised when required Google API credentials are missing."""

    def __init__(self, message: str, *, integration: str | None = None) -> None:
        super().__init__(message)
        self.integration = integration


class GoogleApiRequestError(Exception):
    """Raised when a Google API request fails."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        error_code: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code
