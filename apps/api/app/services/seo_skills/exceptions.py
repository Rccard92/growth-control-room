"""SEO Skill input collection exceptions."""


class UnsupportedSkillTargetError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class SkillInputCollectionError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
