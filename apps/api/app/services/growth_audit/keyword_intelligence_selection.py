"""Seed query selection for Keyword Intelligence analysis."""

from __future__ import annotations

from typing import Any

from app.models.growth_audit import GrowthAuditPage

GENERIC_SHORT_QUERIES = {"miele", "api", "bio", "shop", "store", "home"}


def _safe_float(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _score_query(
    query_row: dict[str, Any],
    *,
    max_impressions: float,
) -> tuple[float, str]:
    query = str(query_row.get("query") or "").strip()
    impressions = _safe_float(query_row.get("impressions"))
    clicks = _safe_float(query_row.get("clicks"))
    ctr = _safe_float(query_row.get("ctr"))
    position = _safe_float(query_row.get("position"))

    score = 0.0
    reasons: list[str] = []

    if max_impressions > 0 and impressions > 0:
        impression_ratio = impressions / max_impressions
        score += 30.0 * impression_ratio
        if impression_ratio >= 0.5:
            reasons.append("high_impressions")

    if ctr < 0.01 and impressions > 100:
        score += 25.0
        reasons.append("low_ctr_high_impressions")

    if 4 <= position <= 15:
        score += 25.0
        reasons.append("position_opportunity")

    if clicks > 0:
        score += 10.0
        reasons.append("has_clicks")

    word_count = len(query.split())
    if word_count >= 3:
        score += 5.0
        reasons.append("long_tail")

    normalized = query.lower().strip()
    if normalized in GENERIC_SHORT_QUERIES or (word_count == 1 and len(normalized) <= 5):
        score -= 15.0
        reasons.append("generic_query_penalty")

    selection_reason = reasons[0] if reasons else "gsc_top_query"
    return score, selection_reason


def _fallback_candidates(page: GrowthAuditPage) -> list[str]:
    metadata = page.page_metadata or {}
    shopify = metadata.get("shopify")
    technical = metadata.get("technical")
    candidates: list[str] = []
    for value in (
        page.source_entity_title,
        shopify.get("title") if isinstance(shopify, dict) else None,
        technical.get("h1") if isinstance(technical, dict) else None,
        page.h1,
        page.title,
    ):
        if isinstance(value, str) and value.strip():
            candidates.append(value.strip())
    return candidates


def select_keyword_intelligence_seed_queries(
    search_console_meta: dict[str, Any] | None,
    page: GrowthAuditPage,
    *,
    max_seed_queries: int,
) -> list[dict[str, Any]]:
    top_queries: list[dict[str, Any]] = []
    if isinstance(search_console_meta, dict):
        raw_queries = search_console_meta.get("topQueries")
        if isinstance(raw_queries, list):
            top_queries = [q for q in raw_queries if isinstance(q, dict) and q.get("query")]

    if not top_queries:
        fallback = _fallback_candidates(page)
        if not fallback:
            return []
        seen: set[str] = set()
        selected: list[dict[str, Any]] = []
        for candidate in fallback:
            key = candidate.lower()
            if key in seen:
                continue
            seen.add(key)
            selected.append(
                {
                    "query": candidate,
                    "clicks": None,
                    "impressions": None,
                    "ctr": None,
                    "position": None,
                    "selected": True,
                    "score": 0,
                    "selectionReason": "fallback_page_title",
                }
            )
            if len(selected) >= max_seed_queries:
                break
        return selected

    max_impressions = max(
        (_safe_float(q.get("impressions")) for q in top_queries),
        default=0.0,
    )
    scored: list[dict[str, Any]] = []
    for row in top_queries:
        query = str(row.get("query") or "").strip()
        if not query:
            continue
        score, selection_reason = _score_query(row, max_impressions=max_impressions)
        scored.append(
            {
                "query": query,
                "clicks": row.get("clicks"),
                "impressions": row.get("impressions"),
                "ctr": row.get("ctr"),
                "position": row.get("position"),
                "selected": True,
                "score": round(score, 2),
                "selectionReason": selection_reason,
            }
        )

    scored.sort(key=lambda item: item.get("score", 0), reverse=True)
    return scored[:max_seed_queries]
