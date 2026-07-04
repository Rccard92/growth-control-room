"""Page type classification and skill bundle metadata for Growth Audit."""

from __future__ import annotations

from typing import Any

from app.services.growth_audit.url_utils import get_url_path


def classify_page_type(
    url: str,
    title: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> str:
    path = get_url_path(url).lower()

    if path in ("/", ""):
        return "homepage"
    if path.startswith("/products/"):
        return "product"
    if path.startswith("/collections/"):
        return "collection"
    if path.startswith("/blogs/"):
        if path.count("/") >= 3:
            return "article"
        return "blog"
    if path.startswith("/pages/"):
        return "page"
    if any(
        segment in path
        for segment in (
            "/privacy",
            "/terms",
            "/refund",
            "/shipping",
            "/legal",
            "/policy",
        )
    ):
        return "policy"
    if path.startswith("/cart"):
        return "cart"
    if path.startswith("/checkout"):
        return "checkout"
    if path.startswith("/search"):
        return "search"
    if path.startswith("/account"):
        return "account"

    if metadata:
        page_type = metadata.get("page_type") or metadata.get("pageType")
        if isinstance(page_type, str) and page_type.strip():
            return page_type.strip().lower()

    if title:
        title_lower = title.lower()
        if "privacy" in title_lower or "policy" in title_lower:
            return "policy"

    return "other"


def get_default_skill_bundle_for_page_type(page_type: str) -> list[str]:
    bundles: dict[str, list[str]] = {
        "homepage": ["seo-audit", "geo-audit", "cro-audit"],
        "product": ["seo-audit", "geo-audit", "cro-audit"],
        "collection": ["seo-audit", "geo-audit"],
        "blog": ["seo-audit", "geo-audit"],
        "article": ["seo-audit", "geo-audit"],
        "page": ["seo-audit", "geo-audit"],
        "policy": ["seo-audit"],
        "other": ["seo-audit"],
        "unknown": ["seo-audit"],
    }
    return bundles.get(page_type, ["seo-audit"])
