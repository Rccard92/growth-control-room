"""Competitor aggregation from SERP results."""

from __future__ import annotations

from typing import Any


def build_competitor_summary(serp_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_domain: dict[str, dict[str, Any]] = {}

    for serp in serp_results:
        keyword = serp.get("keyword")
        for result in serp.get("topResults") or []:
            if not isinstance(result, dict):
                continue
            domain = result.get("domain")
            if not domain:
                continue
            position = result.get("position")
            entry = by_domain.setdefault(
                domain,
                {
                    "domain": domain,
                    "bestPosition": position,
                    "appearancesCount": 0,
                    "keywords": [],
                    "urls": [],
                    "titles": [],
                },
            )
            entry["appearancesCount"] += 1
            if keyword and keyword not in entry["keywords"]:
                entry["keywords"].append(keyword)
            url = result.get("url")
            if url and url not in entry["urls"]:
                entry["urls"].append(url)
            title = result.get("title")
            if title and title not in entry["titles"]:
                entry["titles"].append(title)
            if position is not None:
                current_best = entry.get("bestPosition")
                if current_best is None or position < current_best:
                    entry["bestPosition"] = position

    competitors = sorted(
        by_domain.values(),
        key=lambda item: (
            -(item.get("appearancesCount") or 0),
            item.get("bestPosition") if item.get("bestPosition") is not None else 999,
        ),
    )
    return competitors
