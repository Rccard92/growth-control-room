"""Brief service constants tests."""

from app.services.brand_intelligence.brief_service import PENDING_BRIEF_STATUSES


def test_pending_brief_statuses() -> None:
    assert "draft" in PENDING_BRIEF_STATUSES
    assert "approved" not in PENDING_BRIEF_STATUSES
