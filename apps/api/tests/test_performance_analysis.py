"""Tests for performance analysis normalizers."""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

from app.services.growth_audit.performance_analysis import (
    build_performance_findings,
    normalize_crux_result,
    normalize_pagespeed_result,
)


def _pagespeed_fixture() -> dict:
    return {
        "lighthouseResult": {
            "categories": {
                "performance": {"score": 0.62},
                "accessibility": {"score": 0.91},
                "best-practices": {"score": 0.83},
                "seo": {"score": 0.88},
            },
            "audits": {
                "largest-contentful-paint": {
                    "numericValue": 4200,
                    "score": 0.45,
                    "title": "Largest Contentful Paint",
                    "displayValue": "4.2 s",
                },
                "cumulative-layout-shift": {
                    "numericValue": 0.18,
                    "score": 0.7,
                    "title": "Cumulative Layout Shift",
                },
                "total-blocking-time": {
                    "numericValue": 720,
                    "score": 0.4,
                    "title": "Total Blocking Time",
                },
                "first-contentful-paint": {
                    "numericValue": 1800,
                    "score": 0.8,
                    "title": "First Contentful Paint",
                },
                "unused-javascript": {
                    "numericValue": 120000,
                    "score": 0.2,
                    "title": "Reduce unused JavaScript",
                    "description": "Reduce unused JavaScript",
                },
            },
        }
    }


def test_normalize_pagespeed_result_extracts_scores_and_metrics() -> None:
    normalized = normalize_pagespeed_result(_pagespeed_fixture())

    assert normalized["performanceScore"] == 62
    assert normalized["accessibilityScore"] == 91
    assert normalized["lcp"] == 4200
    assert normalized["cls"] == 0.18
    assert normalized["tbt"] == 720
    assert normalized["fcp"] == 1800


def test_normalize_crux_result_extracts_inp_lcp_cls() -> None:
    normalized = normalize_crux_result(
        {
            "_cruxSource": "url",
            "record": {
                "key": {"formFactor": "PHONE"},
                "collectionPeriod": {"firstDate": "2026-01-01"},
                "metrics": {
                    "largest_contentful_paint": {"percentiles": {"p75": 2500}},
                    "cumulative_layout_shift": {"percentiles": {"p75": 12}},
                    "interaction_to_next_paint": {"percentiles": {"p75": 320}},
                },
            },
        }
    )

    assert normalized["source"] == "url"
    assert normalized["lcpP75"] == 2500
    assert normalized["clsP75"] == 0.12
    assert normalized["inpP75"] == 320


def test_normalize_crux_result_missing() -> None:
    normalized = normalize_crux_result(None)
    assert normalized["source"] == "missing"


def test_build_performance_findings_from_pagespeed_and_crux() -> None:
    pagespeed = normalize_pagespeed_result(_pagespeed_fixture())
    crux = normalize_crux_result(None)
    findings = build_performance_findings(pagespeed, crux)

    titles = {finding["title"] for finding in findings}
    assert "LCP elevato" in titles
    assert "Total Blocking Time alto" in titles
    assert all(finding["category"] == "performance" for finding in findings)
