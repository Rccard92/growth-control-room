"""Refresh context service tests."""

from app.services.brand_intelligence.refresh_context_service import ARCHIVE_DRAFT_STATUSES


def test_archive_draft_statuses_include_active_drafts() -> None:
    assert "draft" in ARCHIVE_DRAFT_STATUSES
    assert "needs_review" in ARCHIVE_DRAFT_STATUSES
    assert "approved" in ARCHIVE_DRAFT_STATUSES


def test_archive_draft_statuses_exclude_applied() -> None:
    assert "applied" not in ARCHIVE_DRAFT_STATUSES
    assert "rejected" not in ARCHIVE_DRAFT_STATUSES
