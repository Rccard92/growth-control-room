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


class GoogleIntegrationNotConnectedError(Exception):
    """Raised when Google OAuth is not connected for the project."""

    def __init__(self, message: str, *, integration: str | None = None) -> None:
        super().__init__(message)
        self.integration = integration


class GoogleIntegrationPermissionError(Exception):
    """Raised when Google API rejects the request due to permissions."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        integration: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.integration = integration


class GoogleSearchConsolePropertyError(Exception):
    """Raised when a Search Console property is missing or invalid."""

    def __init__(self, message: str, *, site_url: str | None = None) -> None:
        super().__init__(message)
        self.site_url = site_url
