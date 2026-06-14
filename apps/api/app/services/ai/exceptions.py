"""AI client exceptions."""


class OpenAINotConfiguredError(Exception):
    pass


class OpenAIRequestError(Exception):
    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class AiBudgetExceededError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class AiSingleRequestBlockedError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
