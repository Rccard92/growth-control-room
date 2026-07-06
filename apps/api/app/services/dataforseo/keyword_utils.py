"""Keyword list helpers for DataForSEO sandbox."""

from __future__ import annotations

from app.services.dataforseo.constants import SEARCH_VOLUME_BATCH_MAX_KEYWORDS


def resolve_search_volume_keywords(
    *,
    keyword: str,
    keywords: list[str] | None,
) -> list[str]:
    source = keywords if keywords else [keyword]
    resolved: list[str] = []
    seen: set[str] = set()
    for item in source:
        cleaned = str(item).strip()
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        resolved.append(cleaned)

    if not resolved:
        raise ValueError("Inserisci almeno una keyword.")

    if len(resolved) > SEARCH_VOLUME_BATCH_MAX_KEYWORDS:
        raise ValueError(
            f"Massimo {SEARCH_VOLUME_BATCH_MAX_KEYWORDS} keyword per batch test."
        )

    return resolved
