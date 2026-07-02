"""SEO Skill service exceptions."""


class UnsupportedSkillTargetError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class SkillInputCollectionError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class SeoSkillRunnerError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class SeoSkillNotAvailableError(SeoSkillRunnerError):
    pass


class SeoSkillProviderError(SeoSkillRunnerError):
    pass


class SeoSkillRunError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class SeoSkillRunValidationError(SeoSkillRunError):
    pass


class SeoSkillRunNotFoundError(SeoSkillRunError):
    pass
