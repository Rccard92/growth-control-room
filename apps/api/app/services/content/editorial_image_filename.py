"""SEO filename generation for editorial hero images."""

from __future__ import annotations

import hashlib
import re
from uuid import UUID

from app.utils.slug import slugify

FALLBACK_FILENAME = "articolo-solmielato.jpg"
MAX_SLUG_LENGTH = 90
FORBIDDEN_SLUG_PATTERNS = (
    "chatgpt",
    "openai",
    "image",
    "generated",
    "output",
    "temp",
)
_UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def _is_forbidden_slug(slug: str) -> bool:
    lowered = slug.lower()
    if not lowered:
        return True
    if _UUID_PATTERN.match(lowered):
        return True
    for pattern in FORBIDDEN_SLUG_PATTERNS:
        if pattern in lowered:
            return True
    return False


def _base_slug_from_title(title: str) -> str:
    stripped = title.strip()
    if not stripped:
        return ""
    slug = slugify(stripped)
    if _is_forbidden_slug(slug):
        return ""
    if len(slug) > MAX_SLUG_LENGTH:
        slug = slug[:MAX_SLUG_LENGTH].rstrip("-")
    return slug


def build_editorial_image_filename(
    title: str,
    *,
    version: int = 1,
    short_hash: str | None = None,
) -> str:
    """Build SEO filename from article title."""
    base_slug = _base_slug_from_title(title)
    if not base_slug:
        base_slug = FALLBACK_FILENAME.removesuffix(".jpg")

    if version > 1:
        suffix = f"-v{version}"
        max_base = MAX_SLUG_LENGTH - len(suffix)
        base_slug = base_slug[:max_base].rstrip("-") + suffix
    elif short_hash:
        suffix = f"-{short_hash[:6]}"
        max_base = MAX_SLUG_LENGTH - len(suffix)
        base_slug = base_slug[:max_base].rstrip("-") + suffix

    return f"{base_slug}.jpg"


def resolve_unique_editorial_image_filename(
    title: str,
    *,
    existing_filenames: set[str],
    version_hint: str | None = None,
) -> str:
    """Return a unique filename, adding -v2/-v3 or short hash on collision."""
    if version_hint:
        short_hash = hashlib.sha256(version_hint.encode()).hexdigest()
        candidate = build_editorial_image_filename(title, short_hash=short_hash)
        if candidate not in existing_filenames:
            return candidate

    version = 1
    while version < 100:
        candidate = build_editorial_image_filename(title, version=version)
        if candidate not in existing_filenames:
            return candidate
        version += 1

    short_hash = hashlib.sha256(f"{title}:{version_hint or version}".encode()).hexdigest()
    return build_editorial_image_filename(title, short_hash=short_hash)


def filename_slug_from_image_filename(filename: str | None) -> str:
    if not filename:
        return ""
    name = filename.strip().lower()
    if name.endswith(".jpg"):
        name = name[:-4]
    elif name.endswith(".jpeg"):
        name = name[:-5]
    return name
