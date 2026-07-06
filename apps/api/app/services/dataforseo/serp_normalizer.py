"""Normalize DataForSEO SERP API responses."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse


def _extract_domain(url: str | None) -> str | None:
    if not url:
        return None
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower().replace("www.", "") or None
    except ValueError:
        return None


def _extract_serp_rows(result: dict[str, Any]) -> list[dict[str, Any]]:
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


def normalize_serp_organic_item(raw_item: dict[str, Any]) -> dict[str, Any]:
    url = raw_item.get("url")
    item_type = raw_item.get("type") or ("organic" if url else None)
    return {
        "position": raw_item.get("rank_group") or raw_item.get("rank_absolute"),
        "title": raw_item.get("title"),
        "url": url,
        "domain": _extract_domain(url) if url else raw_item.get("domain"),
        "description": raw_item.get("description"),
        "type": item_type,
    }


def _collect_refinement_chips(row: dict[str, Any]) -> list[str]:
    chips: list[str] = []
    for item in row.get("items") or []:
        if not isinstance(item, dict):
            continue
        if item.get("type") == "refinement_chips":
            for chip in item.get("items") or []:
                if isinstance(chip, dict) and chip.get("title"):
                    chips.append(str(chip["title"]))
                elif isinstance(chip, str):
                    chips.append(chip)
    return chips


def _collect_people_also_ask(row: dict[str, Any]) -> list[str]:
    questions: list[str] = []
    for item in row.get("items") or []:
        if not isinstance(item, dict):
            continue
        if item.get("type") == "people_also_ask":
            for paa in item.get("items") or []:
                if isinstance(paa, dict) and paa.get("title"):
                    questions.append(str(paa["title"]))
    return questions


def _collect_related_searches(row: dict[str, Any]) -> list[str]:
    related: list[str] = []
    for item in row.get("items") or []:
        if not isinstance(item, dict):
            continue
        if item.get("type") == "related_searches":
            for rel in item.get("items") or []:
                if isinstance(rel, dict) and rel.get("title"):
                    related.append(str(rel["title"]))
                elif isinstance(rel, str):
                    related.append(rel)
    return related


def _collect_serp_features(row: dict[str, Any]) -> list[str]:
    features: list[str] = []
    for item in row.get("items") or []:
        if isinstance(item, dict) and item.get("type"):
            feature_type = str(item["type"])
            if feature_type not in ("organic",):
                features.append(feature_type)
    return list(dict.fromkeys(features))


def normalize_serp_response(result: dict[str, Any], keyword: str) -> dict[str, Any]:
    rows = _extract_serp_rows(result)
    organic: list[dict[str, Any]] = []
    refinement_chips: list[str] = []
    people_also_ask: list[str] = []
    related_searches: list[str] = []
    serp_features: list[str] = []

    for row in rows:
        refinement_chips.extend(_collect_refinement_chips(row))
        people_also_ask.extend(_collect_people_also_ask(row))
        related_searches.extend(_collect_related_searches(row))
        serp_features.extend(_collect_serp_features(row))
        for item in row.get("items") or []:
            if not isinstance(item, dict):
                continue
            if item.get("type") == "organic" or item.get("url"):
                organic.append(normalize_serp_organic_item(item))

    return {
        "keyword": keyword,
        "resultCount": len(organic),
        "totalCostUsd": result.get("cost_usd"),
        "topResults": organic[:10],
        "refinementChips": list(dict.fromkeys(refinement_chips)),
        "peopleAlsoAsk": list(dict.fromkeys(people_also_ask)),
        "relatedSearches": list(dict.fromkeys(related_searches)),
        "serpFeatures": list(dict.fromkeys(serp_features)),
        "itemsCount": len(organic),
    }
