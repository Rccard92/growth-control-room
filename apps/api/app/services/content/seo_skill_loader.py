import logging
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_SKILLS_ROOT = Path(__file__).resolve().parents[5] / "packages" / "skills"
GCR_SKILL_DIR = _SKILLS_ROOT / "seo" / "gcr-shopify-seo"
EXTERNAL_SKILL_DIR = _SKILLS_ROOT / "external" / "claude-seo" / "imported-skills"

_EXTERNAL_SKILL_NAMES = (
    "seo-ecommerce",
    "seo-images",
    "seo-content-brief",
    "seo-schema",
    "seo-cluster",
)

_SKILL_FILES: dict[str, str] = {
    "skill": "SKILL.md",
    "product_rules": "product-seo-rules.md",
    "collection_rules": "collection-seo-rules.md",
    "image_alt_rules": "image-alt-rules.md",
    "proposal_rules": "proposal-rules.md",
    "content_brief_rules": "content-brief-rules.md",
    "schema_rules": "schema-rules.md",
    "brand_guardrails": "brand-guardrails.md",
    "source_map": "source-map.md",
}

_FALLBACK: dict[str, str] = {
    "skill": "GCR Shopify SEO optimization skill.",
    "product_rules": "Score product title, seo title, meta, description, handle, tags, image alt.",
    "collection_rules": "Score collection title, seo title, meta, description, handle, image alt.",
    "image_alt_rules": "Image alt must describe product/collection without keyword stuffing (10-125 chars).",
    "proposal_rules": "Fill missing fields, improve weak ones, output structured JSON aligned to API.",
    "content_brief_rules": "Future blog brief rules (search intent, outline, E-E-A-T).",
    "schema_rules": "Future Product/BreadcrumbList schema rules.",
    "brand_guardrails": "Do not invent claims. Do not change product meaning.",
    "source_map": "GCR rules adapted from claude-seo (MIT) and Shopify custom rules.",
}

_SKILL_NAME = "GCR Shopify SEO Skill"
_ATTRIBUTION = "Inspired by claude-seo ecommerce/images/content-brief rules (MIT)"
_SCORE_RULE_CATEGORIES_PRODUCT = (
    "title",
    "seo_title",
    "meta_description",
    "description",
    "handle",
    "tags",
    "image_alt",
)

_SCORE_RULE_CATEGORIES_COLLECTION = (
    "title",
    "seo_title",
    "meta_description",
    "description",
    "handle",
    "image_alt",
)


@dataclass(frozen=True)
class SeoSkillContext:
    skill: str
    product_rules: str
    collection_rules: str
    image_alt_rules: str
    proposal_rules: str
    content_brief_rules: str
    schema_rules: str
    brand_guardrails: str
    source_map: str
    version: str
    loaded_from_files: bool
    external_references_loaded: bool

    def as_proposal_prompt_context(self) -> str:
        source_summary = _summarize_source_map(self.source_map)
        return (
            f"# Skill\n{self.skill}\n\n"
            f"# Product rules\n{self.product_rules}\n\n"
            f"# Collection rules\n{self.collection_rules}\n\n"
            f"# Image alt rules\n{self.image_alt_rules}\n\n"
            f"# Proposal rules\n{self.proposal_rules}\n\n"
            f"# Brand guardrails\n{self.brand_guardrails}\n\n"
            f"# Source map (summary)\n{source_summary}"
        )


@dataclass(frozen=True)
class SeoSkillMetadata:
    name: str
    version: str
    attribution: str
    score_rule_categories: tuple[str, ...]
    external_skills: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "attribution": self.attribution,
            "score_rule_categories": list(self.score_rule_categories),
            "external_skills": list(self.external_skills),
        }


def _read_skill_file(directory: Path, key: str, filename: str) -> tuple[str, bool]:
    path = directory / filename
    if path.exists():
        try:
            return path.read_text(encoding="utf-8"), True
        except OSError:
            logger.warning("SEO skill file unreadable: %s", filename)
    else:
        logger.warning("SEO skill file missing: %s", filename)
    return _FALLBACK[key], False


def _parse_version_from_skill_md(content: str) -> str:
    match = re.search(r'^version:\s*["\']?([^"\'\n]+)["\']?', content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return "1.0.0"


def _summarize_source_map(source_map: str, max_chars: int = 2000) -> str:
    lines = [line.strip() for line in source_map.splitlines() if line.strip()]
    if not lines:
        return _FALLBACK["source_map"]
    summary = "\n".join(lines[:40])
    if len(summary) > max_chars:
        return summary[: max_chars - 3] + "..."
    return summary


def _parse_external_skill_frontmatter(skill_dir: Path) -> str | None:
    skill_path = skill_dir / "SKILL.md"
    if not skill_path.exists():
        return None
    try:
        content = skill_path.read_text(encoding="utf-8")
    except OSError:
        return None
    name_match = re.search(r'^name:\s*([^\n]+)', content, re.MULTILINE)
    version_match = re.search(r'^version:\s*["\']?([^"\'\n]+)["\']?', content, re.MULTILINE)
    name = name_match.group(1).strip() if name_match else skill_dir.name
    version = version_match.group(1).strip() if version_match else "unknown"
    return f"{name}@{version}"


@lru_cache(maxsize=1)
def load_external_skill_references() -> tuple[str, ...]:
    refs: list[str] = []
    for skill_name in _EXTERNAL_SKILL_NAMES:
        ref = _parse_external_skill_frontmatter(EXTERNAL_SKILL_DIR / skill_name)
        if ref:
            refs.append(ref)
    if refs:
        logger.info("Loaded external claude-seo references (%d skills)", len(refs))
    else:
        logger.warning("No external claude-seo references found")
    return tuple(refs)


@lru_cache(maxsize=1)
def load_seo_skill_context() -> SeoSkillContext:
    loaded_all = True
    values: dict[str, str] = {}
    for key, filename in _SKILL_FILES.items():
        content, ok = _read_skill_file(GCR_SKILL_DIR, key, filename)
        values[key] = content
        loaded_all = loaded_all and ok

    version = _parse_version_from_skill_md(values["skill"])
    external_refs = load_external_skill_references()

    if loaded_all:
        logger.info("Loaded GCR Shopify SEO skill (version %s)", version)
    else:
        logger.warning("Loaded GCR Shopify SEO skill with fallbacks (version %s)", version)

    return SeoSkillContext(
        skill=values["skill"],
        product_rules=values["product_rules"],
        collection_rules=values["collection_rules"],
        image_alt_rules=values["image_alt_rules"],
        proposal_rules=values["proposal_rules"],
        content_brief_rules=values["content_brief_rules"],
        schema_rules=values["schema_rules"],
        brand_guardrails=values["brand_guardrails"],
        source_map=values["source_map"],
        version=version,
        loaded_from_files=loaded_all,
        external_references_loaded=len(external_refs) > 0,
    )


def get_seo_skill_metadata() -> SeoSkillMetadata:
    ctx = load_seo_skill_context()
    return SeoSkillMetadata(
        name=_SKILL_NAME,
        version=ctx.version,
        attribution=_ATTRIBUTION,
        score_rule_categories=_SCORE_RULE_CATEGORIES_PRODUCT,
        external_skills=load_external_skill_references(),
    )


def skill_meta_for_detail_response(entity_type: str):
    """Build validated SeoSkillMetaRead for product/collection detail endpoints."""
    from app.schemas.seo_optimizer import SeoSkillMetaRead

    meta = get_seo_skill_metadata()
    categories = (
        list(_SCORE_RULE_CATEGORIES_PRODUCT)
        if entity_type == "product"
        else list(_SCORE_RULE_CATEGORIES_COLLECTION)
    )
    return SeoSkillMetaRead(
        name=meta.name,
        version=meta.version,
        attribution=meta.attribution,
        score_rule_categories=categories,
        external_skills=list(meta.external_skills),
    )


def skill_recommendation_metadata() -> dict[str, str]:
    ctx = load_seo_skill_context()
    return {
        "skill_pack": "gcr-shopify-seo",
        "skill_version": ctx.version,
    }


def clear_seo_skill_cache() -> None:
    load_seo_skill_context.cache_clear()
    load_external_skill_references.cache_clear()
