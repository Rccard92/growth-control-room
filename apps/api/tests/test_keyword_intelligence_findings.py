"""Tests for Keyword Intelligence findings evidence formatting."""

from __future__ import annotations

from app.services.growth_audit.keyword_intelligence_findings import (
    build_keyword_intelligence_findings,
)


def test_ctr_finding_evidence_is_string_with_structured_metadata() -> None:
    findings, _ = build_keyword_intelligence_findings(
        seed_queries=[
            {
                "query": "polline biologico",
                "impressions": 477,
                "ctr": 0.0021,
            }
        ],
        search_volume=[{"keyword": "polline biologico", "searchVolume": 140}],
        serp_results=[],
        competitors=[],
    )
    assert len(findings) == 1
    finding = findings[0]
    assert isinstance(finding["evidence"], str)
    assert "polline biologico" in finding["evidence"]
    assert "477 impression" in finding["evidence"]
    assert "0.21%" in finding["evidence"]
    assert isinstance(finding["structuredEvidence"], dict)
    assert finding["structuredEvidence"]["searchVolume"] == 140


def test_refinement_chips_finding_evidence_is_string() -> None:
    findings, _ = build_keyword_intelligence_findings(
        seed_queries=[],
        search_volume=[],
        serp_results=[
            {
                "keyword": "polline biologico",
                "refinementChips": ["Benefici", "Come assumerlo"],
                "topResults": [],
            }
        ],
        competitors=[],
    )
    assert len(findings) == 1
    finding = findings[0]
    assert isinstance(finding["evidence"], str)
    assert "refinement chips" in finding["evidence"]
    assert "Benefici" in finding["evidence"]
    assert finding["structuredEvidence"]["refinementChips"] == [
        "Benefici",
        "Come assumerlo",
    ]


def test_competitor_finding_evidence_is_string() -> None:
    findings, _ = build_keyword_intelligence_findings(
        seed_queries=[],
        search_volume=[],
        serp_results=[],
        competitors=[
            {
                "domain": "kontak.it",
                "appearancesCount": 2,
                "bestPosition": 3,
                "keywords": ["polline biologico"],
            }
        ],
    )
    assert len(findings) == 1
    finding = findings[0]
    assert isinstance(finding["evidence"], str)
    assert "kontak.it" in finding["evidence"]
    assert "2 volte" in finding["evidence"]
    assert finding["structuredEvidence"]["domain"] == "kontak.it"
