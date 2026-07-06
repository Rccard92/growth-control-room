"""Findings and tasks from Keyword Intelligence analysis."""

from __future__ import annotations

from typing import Any

MAX_FINDINGS = 5

INFORMATIVE_CHIP_KEYWORDS = (
    "benefici",
    "come",
    "assum",
    "dosaggio",
    "faq",
    "guida",
    "recension",
)


def build_keyword_intelligence_findings(
    *,
    seed_queries: list[dict[str, Any]],
    search_volume: list[dict[str, Any]],
    serp_results: list[dict[str, Any]],
    competitors: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    findings: list[dict[str, Any]] = []
    volume_by_query = {
        str(item.get("keyword") or "").lower(): item for item in search_volume
    }

    for seed in seed_queries:
        query = str(seed.get("query") or "")
        volume_item = volume_by_query.get(query.lower(), {})
        impressions = seed.get("impressions")
        ctr = seed.get("ctr")
        search_vol = volume_item.get("searchVolume")
        if (
            impressions is not None
            and float(impressions or 0) >= 100
            and search_vol is not None
            and float(search_vol) >= 50
            and ctr is not None
            and float(ctr) < 0.01
        ):
            findings.append(
                {
                    "category": "seo",
                    "severity": "medium",
                    "priority": "high",
                    "title": "Keyword con domanda reale e CTR basso",
                    "description": (
                        f'La query "{query}" ha impression GSC elevate e volume di ricerca '
                        f"significativo, ma CTR basso."
                    ),
                    "recommendation": (
                        "Rivedere title/meta e contenuto per intercettare meglio la query."
                    ),
                    "evidence": {
                        "query": query,
                        "impressions": impressions,
                        "ctr": ctr,
                        "searchVolume": search_vol,
                    },
                }
            )
            break

    for serp in serp_results:
        chips = serp.get("refinementChips") or []
        informative = [
            chip
            for chip in chips
            if any(keyword in str(chip).lower() for keyword in INFORMATIVE_CHIP_KEYWORDS)
        ]
        if informative:
            findings.append(
                {
                    "category": "content",
                    "severity": "medium",
                    "priority": "medium",
                    "title": "SERP suggerisce sezioni informative mancanti",
                    "description": (
                        f'Per "{serp.get("keyword")}" la SERP mostra refinement chips informativi.'
                    ),
                    "recommendation": (
                        "Aggiungere FAQ/sezioni coerenti con i refinement chips."
                    ),
                    "evidence": {
                        "keyword": serp.get("keyword"),
                        "refinementChips": informative[:5],
                    },
                }
            )
            break

    for competitor in competitors:
        appearances = competitor.get("appearancesCount") or 0
        best_position = competitor.get("bestPosition")
        if appearances >= 2 or (best_position is not None and best_position <= 3):
            findings.append(
                {
                    "category": "seo",
                    "severity": "medium",
                    "priority": "medium",
                    "title": "Competitor ricorrente in SERP",
                    "description": (
                        f'Il dominio "{competitor.get("domain")}" compare spesso nei risultati SERP.'
                    ),
                    "recommendation": (
                        "Analizzare struttura e contenuti dei competitor principali."
                    ),
                    "evidence": {
                        "domain": competitor.get("domain"),
                        "appearancesCount": appearances,
                        "bestPosition": best_position,
                        "keywords": competitor.get("keywords", [])[:5],
                    },
                }
            )
            break

    findings = findings[:MAX_FINDINGS]
    tasks = [
        {
            "title": finding["title"],
            "description": finding.get("recommendation"),
            "ownerType": "seo" if finding.get("category") == "seo" else "content",
            "priority": finding.get("priority", "medium"),
            "estimatedEffort": "medium",
        }
        for finding in findings
    ]
    return findings, tasks
