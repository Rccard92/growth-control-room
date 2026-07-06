"""DataForSEO domain exceptions."""


class DataForSeoError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class DataForSeoNotConfiguredError(DataForSeoError):
    pass


class DataForSeoRealCallsDisabledError(DataForSeoError):
    pass


class DataForSeoBudgetExceededError(DataForSeoError):
    pass


class DataForSeoApiError(DataForSeoError):
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
