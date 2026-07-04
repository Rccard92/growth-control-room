"""Tests for Growth Audit technical scoring."""

from __future__ import annotations

from app.services.growth_audit.technical_scoring import score_technical_scan


def _base_scan(**overrides) -> dict:
    scan = {
        "httpStatus": 200,
        "title": "A Good Title Between Thirty And Sixty Five Chars",
        "titleLength": 48,
        "metaDescription": (
            "A meta description that is long enough to be useful for search engines "
            "and users clicking from results pages and within range."
        ),
        "metaDescriptionLength": 120,
        "canonicalUrl": "https://example.com/page",
        "h1Count": 1,
        "robots": {"noindex": False, "nofollow": False, "raw": ""},
        "schema": {"jsonLdCount": 1, "types": ["WebPage"]},
        "openGraph": {"title": "OG", "description": "Desc", "image": "https://example.com/i.jpg"},
        "images": {"total": 2, "missingAlt": 0},
        "checks": {
            "httpOk": True,
            "hasTitle": True,
            "titleLengthOk": True,
            "hasMetaDescription": True,
            "metaDescriptionLengthOk": True,
            "hasCanonical": True,
            "canonicalSameDomain": True,
            "hasSingleH1": True,
            "hasNoindex": False,
            "hasJsonLd": True,
            "hasOpenGraph": True,
            "imagesAltOk": True,
        },
    }
    scan.update(overrides)
    return scan


def test_missing_title_generates_finding_and_task() -> None:
    scan = _base_scan(title=None, titleLength=0)
    scan["checks"]["hasTitle"] = False
    score, findings, tasks = score_technical_scan(scan, "unknown")
    assert score < 100
    assert any(f["title"] == "Title mancante" for f in findings)
    assert any("title" in t["title"].lower() for t in tasks)


def test_missing_meta_generates_finding_and_task() -> None:
    scan = _base_scan(metaDescription=None, metaDescriptionLength=0)
    scan["checks"]["hasMetaDescription"] = False
    score, findings, tasks = score_technical_scan(scan, "product")
    assert score < 100
    assert any(f["title"] == "Meta description mancante" for f in findings)
    assert any("meta description" in t["title"].lower() for t in tasks)
    meta_finding = next(f for f in findings if f["title"] == "Meta description mancante")
    assert meta_finding["severity"] == "high"


def test_product_without_product_schema_high_finding() -> None:
    scan = _base_scan(schema={"jsonLdCount": 1, "types": ["WebPage"]})
    score, findings, _ = score_technical_scan(scan, "product")
    assert score < 100
    product_finding = next(f for f in findings if f["title"] == "Product schema mancante")
    assert product_finding["severity"] == "high"


def test_noindex_critical_severity() -> None:
    scan = _base_scan(robots={"noindex": True, "nofollow": False, "raw": "noindex"})
    scan["checks"]["hasNoindex"] = True
    score, findings, _ = score_technical_scan(scan, "product")
    noindex_finding = next(f for f in findings if f["title"] == "Noindex presente")
    assert noindex_finding["severity"] == "critical"
    assert score <= 75


def test_score_clamped_0_100() -> None:
    scan = _base_scan(
        httpStatus=500,
        title=None,
        titleLength=0,
        metaDescription=None,
        metaDescriptionLength=0,
        canonicalUrl=None,
        h1Count=0,
        robots={"noindex": True, "nofollow": True, "raw": "noindex, nofollow"},
        schema={"jsonLdCount": 0, "types": []},
        openGraph={"title": None, "description": None, "image": None},
        images={"total": 5, "missingAlt": 5},
        checks={
            "httpOk": False,
            "hasTitle": False,
            "hasMetaDescription": False,
            "hasCanonical": False,
            "canonicalSameDomain": False,
            "hasSingleH1": False,
            "hasNoindex": True,
            "hasJsonLd": False,
            "hasOpenGraph": False,
            "imagesAltOk": False,
        },
    )
    score, _, _ = score_technical_scan(scan, "product")
    assert 0 <= score <= 100
