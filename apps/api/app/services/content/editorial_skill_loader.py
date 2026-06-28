"""Runtime loader for gcr-editorial-article skill pack."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

_SKILLS_ROOT = Path(__file__).resolve().parents[5] / "packages" / "skills"
EDITORIAL_SKILL_DIR = _SKILLS_ROOT / "seo" / "gcr-editorial-article"
EDITORIAL_SKILL_NAME = "gcr-editorial-article"
EDITORIAL_SKILL_VERSION_FALLBACK = "v1"

_SKILL_FILES: dict[str, str] = {
    "readme": "README.md",
    "article_structure_rules": "article-structure-rules.md",
    "readability_rules": "readability-rules.md",
    "neuromarketing_rules": "neuromarketing-rules.md",
    "shopify_html_rules": "shopify-html-rules.md",
    "internal_linking_rules": "internal-linking-rules.md",
    "faq_format_rules": "faq-format-rules.md",
    "source_map": "source-map.md",
}

_FALLBACK: dict[str, str] = {
    "readme": "GCR Editorial Article skill pack.",
    "article_structure_rules": "Keep articles compact with proportional H2/H3 by content type.",
    "readability_rules": "Short paragraphs, bullet lists, strategic bold, GCR note boxes.",
    "neuromarketing_rules": "Open with real customer doubt; reassure ethically; no false urgency.",
    "shopify_html_rules": "Use h2,h3,p,ul,ol,li,strong,em,a,blockquote,div with GCR classes only.",
    "internal_linking_rules": "Link only with real URLs/handles; otherwise use internalLinkSuggestions.",
    "faq_format_rules": "Max 3 FAQ, short answers, H3 + p structure.",
    "source_map": "GCR custom editorial rules v1.",
}


@dataclass(frozen=True)
class EditorialSkillContext:
    readme: str
    article_structure_rules: str
    readability_rules: str
    neuromarketing_rules: str
    shopify_html_rules: str
    internal_linking_rules: str
    faq_format_rules: str
    source_map: str
    version: str
    loaded_from_files: bool

    def as_brief_prompt_context(self) -> str:
        return (
            f"# Editorial skill: {EDITORIAL_SKILL_NAME} ({self.version})\n"
            f"{self.readme}\n\n"
            f"# Article structure rules\n{self.article_structure_rules}\n\n"
            f"# Readability rules\n{self.readability_rules}\n\n"
            f"# Neuromarketing rules\n{self.neuromarketing_rules}\n\n"
            f"# Internal linking rules\n{self.internal_linking_rules}\n\n"
            f"# FAQ format rules\n{self.faq_format_rules}\n\n"
            f"# Source map\n{self.source_map}"
        )

    def as_article_prompt_context(self) -> str:
        return (
            f"# Editorial skill: {EDITORIAL_SKILL_NAME} ({self.version})\n"
            f"{self.readme}\n\n"
            f"# Article structure rules\n{self.article_structure_rules}\n\n"
            f"# Readability rules\n{self.readability_rules}\n\n"
            f"# Neuromarketing rules\n{self.neuromarketing_rules}\n\n"
            f"# Shopify HTML rules\n{self.shopify_html_rules}\n\n"
            f"# Internal linking rules\n{self.internal_linking_rules}\n\n"
            f"# FAQ format rules\n{self.faq_format_rules}\n\n"
            f"# Source map\n{self.source_map}"
        )


def _read_skill_file(directory: Path, key: str, filename: str) -> tuple[str, bool]:
    path = directory / filename
    if path.exists():
        try:
            return path.read_text(encoding="utf-8"), True
        except OSError:
            logger.warning("Editorial skill file unreadable: %s", filename)
    else:
        logger.warning("Editorial skill file missing: %s", filename)
    return _FALLBACK[key], False


def _parse_version_from_readme(content: str) -> str:
    match = re.search(r'^version:\s*["\']?([^"\'\n]+)["\']?', content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return EDITORIAL_SKILL_VERSION_FALLBACK


@lru_cache(maxsize=1)
def load_editorial_skill_context() -> EditorialSkillContext:
    loaded_any = False
    contents: dict[str, str] = {}
    for key, filename in _SKILL_FILES.items():
        text, ok = _read_skill_file(EDITORIAL_SKILL_DIR, key, filename)
        contents[key] = text
        loaded_any = loaded_any or ok

    version = _parse_version_from_readme(contents["readme"])
    return EditorialSkillContext(
        readme=contents["readme"],
        article_structure_rules=contents["article_structure_rules"],
        readability_rules=contents["readability_rules"],
        neuromarketing_rules=contents["neuromarketing_rules"],
        shopify_html_rules=contents["shopify_html_rules"],
        internal_linking_rules=contents["internal_linking_rules"],
        faq_format_rules=contents["faq_format_rules"],
        source_map=contents["source_map"],
        version=version,
        loaded_from_files=loaded_any,
    )


def clear_editorial_skill_cache() -> None:
    load_editorial_skill_context.cache_clear()
