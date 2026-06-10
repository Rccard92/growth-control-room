from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SkillContext:
    project_id: str
    user_id: str | None = None
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class SkillResult:
    success: bool
    output: dict[str, Any] = field(default_factory=dict)
    message: str = ""


class BaseSkill(ABC):
    """Contratto base per tutte le skill AI."""

    name: str

    @abstractmethod
    async def run(self, context: SkillContext) -> SkillResult:
        """Esegue la skill nel contesto di un progetto."""
