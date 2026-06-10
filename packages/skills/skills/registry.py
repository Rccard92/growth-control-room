from skills.base import BaseSkill

SKILL_REGISTRY: dict[str, type[BaseSkill]] = {}


def register_skill(skill_cls: type[BaseSkill]) -> type[BaseSkill]:
    SKILL_REGISTRY[skill_cls.name] = skill_cls
    return skill_cls


def get_skill(name: str) -> BaseSkill:
    skill_cls = SKILL_REGISTRY.get(name)
    if skill_cls is None:
        raise ValueError(f"Skill non registrata: {name}")
    return skill_cls()


def list_skills() -> list[str]:
    return list(SKILL_REGISTRY.keys())
