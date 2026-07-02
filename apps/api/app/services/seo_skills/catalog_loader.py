import json
from functools import lru_cache
from pathlib import Path

from app.schemas.seo_skills import SeoSkillCatalogCounts, SeoSkillCatalogItem

_SKILLS_ROOT = Path(__file__).resolve().parents[5] / "packages" / "skills"
CATALOG_PATH = _SKILLS_ROOT / "external" / "claude-seo" / "skill-catalog.json"


def _build_counts(skills: list[SeoSkillCatalogItem]) -> SeoSkillCatalogCounts:
    return SeoSkillCatalogCounts(
        total=len(skills),
        available=sum(1 for skill in skills if skill.status == "available"),
        needs_config=sum(1 for skill in skills if skill.status == "needs_config"),
        external_required=sum(
            1 for skill in skills if skill.status == "external_required"
        ),
        planned=sum(1 for skill in skills if skill.status == "planned"),
    )


@lru_cache(maxsize=1)
def load_seo_skill_catalog() -> list[SeoSkillCatalogItem]:
    if not CATALOG_PATH.is_file():
        raise ValueError(f"SEO skill catalog not found: {CATALOG_PATH}")

    try:
        raw = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid SEO skill catalog JSON: {CATALOG_PATH}") from exc

    skills_raw = raw.get("skills")
    if not isinstance(skills_raw, list) or not skills_raw:
        raise ValueError(f"SEO skill catalog must contain a non-empty skills array: {CATALOG_PATH}")

    skills: list[SeoSkillCatalogItem] = []
    for index, item in enumerate(skills_raw):
        try:
            skills.append(SeoSkillCatalogItem.model_validate(item))
        except Exception as exc:
            raise ValueError(
                f"Invalid SEO skill catalog entry at index {index} in {CATALOG_PATH}"
            ) from exc

    return skills


def get_seo_skill_by_key(key: str) -> SeoSkillCatalogItem | None:
    for skill in load_seo_skill_catalog():
        if skill.key == key:
            return skill
    return None


def list_available_seo_skills() -> list[SeoSkillCatalogItem]:
    return [
        skill
        for skill in load_seo_skill_catalog()
        if skill.status == "available" and skill.enabled
    ]


def clear_seo_skill_catalog_cache() -> None:
    load_seo_skill_catalog.cache_clear()


__all__ = [
    "CATALOG_PATH",
    "_build_counts",
    "clear_seo_skill_catalog_cache",
    "get_seo_skill_by_key",
    "list_available_seo_skills",
    "load_seo_skill_catalog",
]
