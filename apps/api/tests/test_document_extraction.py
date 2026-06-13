"""Document extraction confidence rules."""

from app.services.brand_intelligence.document_extraction import _normalize_fact_status


def test_low_confidence_needs_review() -> None:
    assert _normalize_fact_status(0.3) == "needs_review"


def test_high_confidence_suggested() -> None:
    assert _normalize_fact_status(0.8) == "suggested"
