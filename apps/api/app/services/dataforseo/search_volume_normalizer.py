"""Normalize DataForSEO search volume API responses."""

from __future__ import annotations

from typing import Any


def _normalize_monthly_searches(raw: Any) -> list[dict[str, Any]] | None:
    if not isinstance(raw, list):
        return None
    items: list[dict[str, Any]] = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        items.append(
            {
                "year": entry.get("year"),
                "month": entry.get("month"),
                "searchVolume": entry.get("search_volume"),
            }
        )
    return items or None


def _compute_trend(monthly_searches: list[dict[str, Any]] | None) -> dict[str, Any] | None:
    if not monthly_searches or len(monthly_searches) < 2:
        return None

    sorted_months = sorted(
        monthly_searches,
        key=lambda item: (item.get("year") or 0, item.get("month") or 0),
    )
    volumes = [
        item.get("searchVolume")
        for item in sorted_months
        if isinstance(item.get("searchVolume"), (int, float))
    ]
    if len(volumes) < 2:
        return {
            "direction": "unknown",
            "lastMonth": volumes[-1] if volumes else None,
            "previousMonth": None,
            "averageLast12Months": None,
        }

    last_month = volumes[-1]
    previous_month = volumes[-2]
    recent = volumes[-12:] if len(volumes) >= 12 else volumes
    average_last_12 = sum(recent) / len(recent) if recent else None

    direction = "unknown"
    if previous_month and previous_month > 0:
        change_ratio = (last_month - previous_month) / previous_month
        if change_ratio >= 0.10:
            direction = "up"
        elif change_ratio <= -0.10:
            direction = "down"
        else:
            direction = "stable"

    return {
        "direction": direction,
        "lastMonth": last_month,
        "previousMonth": previous_month,
        "averageLast12Months": round(average_last_12, 2) if average_last_12 is not None else None,
    }


def normalize_search_volume_result(raw_row: dict[str, Any], *, fallback_keyword: str = "") -> dict[str, Any]:
    monthly_searches = _normalize_monthly_searches(raw_row.get("monthly_searches"))
    return {
        "keyword": raw_row.get("keyword") or fallback_keyword,
        "searchVolume": raw_row.get("search_volume"),
        "cpc": raw_row.get("cpc"),
        "competition": raw_row.get("competition"),
        "competitionIndex": raw_row.get("competition_index"),
        "monthlySearches": monthly_searches,
        "trend": _compute_trend(monthly_searches),
    }


def _extract_search_volume_rows(result: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    tasks = result.get("tasks") or []
    for task in tasks:
        if not isinstance(task, dict):
            continue
        task_results = task.get("result")
        if not isinstance(task_results, list):
            continue
        for row in task_results:
            if isinstance(row, dict):
                rows.append(row)
    return rows


def normalize_search_volume_batch_response(
    result: dict[str, Any],
    keywords: list[str],
) -> dict[str, Any]:
    rows = _extract_search_volume_rows(result)
    rows_by_keyword = {
        str(row.get("keyword") or "").strip().lower(): row
        for row in rows
        if isinstance(row.get("keyword"), str) or row.get("keyword") is not None
    }

    normalized_results: list[dict[str, Any]] = []
    for keyword in keywords:
        row = rows_by_keyword.get(keyword.strip().lower())
        if row:
            normalized_results.append(normalize_search_volume_result(row, fallback_keyword=keyword))
        else:
            normalized_results.append(
                {
                    "keyword": keyword,
                    "searchVolume": None,
                    "cpc": None,
                    "competition": None,
                    "competitionIndex": None,
                    "monthlySearches": None,
                    "trend": None,
                }
            )

    total_cost = result.get("cost_usd")
    keyword_count = len(keywords)
    average_cost = (
        float(total_cost) / keyword_count
        if total_cost is not None and keyword_count > 0
        else None
    )

    return {
        "keywordCount": keyword_count,
        "totalCostUsd": total_cost,
        "averageCostPerKeywordUsd": average_cost,
        "results": normalized_results,
        "itemsCount": keyword_count,
        "items": normalized_results[:5],
    }
