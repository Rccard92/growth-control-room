"""Runtime loader for gcr-editorial-image skill pack."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

_SKILLS_ROOT = Path(__file__).resolve().parents[5] / "packages" / "skills"
EDITORIAL_IMAGE_SKILL_DIR = _SKILLS_ROOT / "seo" / "gcr-editorial-image"
EDITORIAL_IMAGE_SKILL_NAME = "gcr-editorial-image"
EDITORIAL_IMAGE_SKILL_VERSION_FALLBACK = "v1.0"

_SKILL_FILES: dict[str, str] = {
    "readme": "README.md",
    "featured_image_rules": "featured-image-rules.md",
}

_FALLBACK: dict[str, str] = {
    "readme": "GCR Editorial Image skill pack.",
    "featured_image_rules": (
        "Editorial hero image: clean, natural, premium, no text, no health claims."
    ),
}


@dataclass(frozen=True)
class EditorialImageSkillContext:
    readme: str
    featured_image_rules: str
    version: str
    loaded_from_files: bool

    def as_prompt_context(self) -> str:
        return (
            f"# Editorial image skill: {EDITORIAL_IMAGE_SKILL_NAME} ({self.version})\n"
            f"{self.readme}\n\n"
            f"# Featured image rules\n{self.featured_image_rules}"
        )


def _read_skill_file(directory: Path, key: str, filename: str) -> tuple[str, bool]:
    path = directory / filename
    if path.is_file():
        try:
            return path.read_text(encoding="utf-8").strip(), True
        except OSError as exc:
            logger.warning("Cannot read editorial image skill %s: %s", filename, exc)
    return _FALLBACK[key], False


def _parse_version(readme: str) -> str:
    match = re.search(r'^version:\s*["\']?([^"\']+)["\']?', readme, re.MULTILINE | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    match = re.search(r"version:\s*(v[\d.]+)", readme, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return EDITORIAL_IMAGE_SKILL_VERSION_FALLBACK


@lru_cache(maxsize=1)
def load_editorial_image_skill_context() -> EditorialImageSkillContext:
    loaded_any = False
    contents: dict[str, str] = {}
    for key, filename in _SKILL_FILES.items():
        text, from_file = _read_skill_file(EDITORIAL_IMAGE_SKILL_DIR, key, filename)
        contents[key] = text
        loaded_any = loaded_any or from_file
    version = _parse_version(contents["readme"])
    return EditorialImageSkillContext(
        readme=contents["readme"],
        featured_image_rules=contents["featured_image_rules"],
        version=version,
        loaded_from_files=loaded_any,
    )
