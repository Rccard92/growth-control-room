"""Normalize DataForSEO keyword ideas API responses."""

from __future__ import annotations

from typing import Any

from app.services.dataforseo.search_volume_normalizer import _normalize_monthly_searches


def _extract_keyword_idea_rows(result: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    tasks = result.get("tasks") or []
    for task in tasks:
        if not isinstance(task, dict):
            continue
        task_results = task.get("result")
        if not isinstance(task_results, list):
            continue
        for row in task_results:
            if not isinstance(row, dict):
                continue
            items = row.get("items")
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict):
                        rows.append(item)
            elif row.get("keyword"):
                rows.append(row)
    return rows


def normalize_keyword_idea_item(raw_item: dict[str, Any]) -> dict[str, Any]:
    keyword_info = raw_item.get("keyword_info")
    if not isinstance(keyword_info, dict):
        keyword_info = raw_item
    monthly_searches = _normalize_monthly_searches(
        keyword_info.get("monthly_searches") or raw_item.get("monthly_searches")
    )
    return {
        "keyword": raw_item.get("keyword") or keyword_info.get("keyword"),
        "searchVolume": keyword_info.get("search_volume") or raw_item.get("search_volume"),
        "cpc": keyword_info.get("cpc") or raw_item.get("cpc"),
        "competition": keyword_info.get("competition") or raw_item.get("competition"),
        "competitionIndex": keyword_info.get("competition_index")
        or raw_item.get("competition_index"),
        "monthlySearches": monthly_searches,
    }


def normalize_keyword_ideas_response(
    result: dict[str, Any],
    seed_keyword: str,
) -> dict[str, Any]:
    rows = _extract_keyword_idea_rows(result)
    seen: set[str] = set()
    items: list[dict[str, Any]] = []
    for row in rows:
        normalized = normalize_keyword_idea_item(row)
        keyword = str(normalized.get("keyword") or "").strip()
        if not keyword:
            continue
        key = keyword.lower()
        if key in seen:
            continue
        seen.add(key)
        items.append(normalized)

    total_cost = result.get("cost_usd")
    return {
        "seedKeyword": seed_keyword,
        "ideasCount": len(items),
        "totalCostUsd": total_cost,
        "items": items,
        "topIdeas": [item["keyword"] for item in items[:5] if item.get("keyword")],
        "itemsCount": len(items),
    }
