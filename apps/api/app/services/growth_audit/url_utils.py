"""URL normalization and validation for Growth Audit."""

from __future__ import annotations

from urllib.parse import urlparse, urlunparse

from app.services.growth_audit.exceptions import GrowthAuditValidationError
from app.services.seo_skills.input_collector import (
    is_private_or_blocked_host,
    validate_public_http_url,
)

_STATIC_ASSET_EXTENSIONS = (
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".svg",
    ".ico",
    ".css",
    ".js",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".map",
    ".pdf",
    ".zip",
    ".mp4",
    ".webm",
    ".mp3",
)

_EXCLUDED_PATH_PREFIXES = (
    "/cart",
    "/checkout",
    "/account",
    "/admin",
    "/search",
)


def normalize_root_url(url: str) -> str:
    """Validate and normalize a root URL for audit runs."""
    try:
        validated = validate_public_http_url(url.strip())
    except Exception as exc:
        raise GrowthAuditValidationError(str(exc)) from exc

    parsed = urlparse(validated)
    normalized = urlunparse(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path.rstrip("/") or "/",
            "",
            "",
            "",
        )
    )
    return normalized


def extract_domain(url: str) -> str:
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()
    if not hostname:
        raise GrowthAuditValidationError("URL host is not allowed")
    if is_private_or_blocked_host(hostname):
        raise GrowthAuditValidationError("URL host is not allowed")
    return hostname


def normalize_url(url: str) -> str:
    try:
        validated = validate_public_http_url(url.strip())
    except Exception as exc:
        raise GrowthAuditValidationError(str(exc)) from exc

    parsed = urlparse(validated)
    path = parsed.path or "/"
    if not path.startswith("/"):
        path = f"/{path}"
    normalized = urlunparse(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            path.rstrip("/") if path != "/" else "/",
            "",
            "",
            "",
        )
    )
    return normalized


def get_url_path(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path or "/"
    if not path.startswith("/"):
        path = f"/{path}"
    return path.rstrip("/") if path != "/" else "/"


def is_excluded_audit_url(url: str) -> bool:
    path = get_url_path(url).lower()
    if any(path == prefix or path.startswith(f"{prefix}/") for prefix in _EXCLUDED_PATH_PREFIXES):
        return True
    if any(path.endswith(ext) for ext in _STATIC_ASSET_EXTENSIONS):
        return True
    return False
