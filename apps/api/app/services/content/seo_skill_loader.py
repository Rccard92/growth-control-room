import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

SKILL_DIR = (
    Path(__file__).resolve().parents[5]
    / "packages"
    / "skills"
    / "seo"
    / "shopify-product-collection"
)

_SKILL_FILES: dict[str, str] = {
    "skill": "SKILL.md",
    "product_score_rules": "product-seo-score-rules.md",
    "collection_score_rules": "collection-seo-score-rules.md",
    "image_alt_rules": "image-alt-rules.md",
    "proposal_rules": "seo-proposal-rules.md",
    "approval_workflow_rules": "approval-workflow-rules.md",
    "brand_guardrails": "brand-guardrails.md",
}

_FALLBACK: dict[str, str] = {
    "skill": "Shopify product and collection SEO optimization skill.",
    "product_score_rules": "Score product title, seo title, meta, description, handle, tags, image alt.",
    "collection_score_rules": "Score collection title, seo title, meta, description, handle, image alt.",
    "image_alt_rules": "Image alt must describe product/collection without keyword stuffing.",
    "proposal_rules": "Fill missing fields, improve weak ones, output structured JSON.",
    "approval_workflow_rules": "Draft -> approve -> apply on Shopify only after user confirmation.",
    "brand_guardrails": "Do not invent claims. Do not change product meaning.",
}


@dataclass(frozen=True)
class SeoSkillContext:
    skill: str
    product_score_rules: str
    collection_score_rules: str
    image_alt_rules: str
    proposal_rules: str
    approval_workflow_rules: str
    brand_guardrails: str
    loaded_from_files: bool

    def as_prompt_context(self) -> str:
        return (
            f"# Skill\n{self.skill}\n\n"
            f"# Product score rules\n{self.product_score_rules}\n\n"
            f"# Collection score rules\n{self.collection_score_rules}\n\n"
            f"# Image alt rules\n{self.image_alt_rules}\n\n"
            f"# Proposal rules\n{self.proposal_rules}\n\n"
            f"# Approval workflow\n{self.approval_workflow_rules}\n\n"
            f"# Brand guardrails\n{self.brand_guardrails}"
        )


def _read_skill_file(key: str, filename: str) -> tuple[str, bool]:
    path = SKILL_DIR / filename
    if path.exists():
        try:
            return path.read_text(encoding="utf-8"), True
        except OSError:
            logger.warning("SEO skill file unreadable: %s", filename)
    else:
        logger.warning("SEO skill file missing: %s", filename)
    return _FALLBACK[key], False


@lru_cache(maxsize=1)
def load_seo_skill_context() -> SeoSkillContext:
    loaded_all = True
    values: dict[str, str] = {}
    for key, filename in _SKILL_FILES.items():
        content, ok = _read_skill_file(key, filename)
        values[key] = content
        loaded_all = loaded_all and ok
    return SeoSkillContext(
        skill=values["skill"],
        product_score_rules=values["product_score_rules"],
        collection_score_rules=values["collection_score_rules"],
        image_alt_rules=values["image_alt_rules"],
        proposal_rules=values["proposal_rules"],
        approval_workflow_rules=values["approval_workflow_rules"],
        brand_guardrails=values["brand_guardrails"],
        loaded_from_files=loaded_all,
    )
