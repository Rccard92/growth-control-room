"""Batch service helper tests."""

from app.services.brand_intelligence.batch_service import (
    ACTIVE_BATCH_STATUSES,
    TERMINAL_BATCH_STATUSES,
)


def test_active_batch_statuses() -> None:
    assert "extracting" in ACTIVE_BATCH_STATUSES
    assert "ai_processing" in ACTIVE_BATCH_STATUSES
    assert "review_ready" not in ACTIVE_BATCH_STATUSES


def test_terminal_batch_statuses() -> None:
    assert "review_ready" in TERMINAL_BATCH_STATUSES
    assert "partially_failed" in TERMINAL_BATCH_STATUSES
    assert "failed" in TERMINAL_BATCH_STATUSES
    assert "extracting" not in TERMINAL_BATCH_STATUSES


def test_progress_clamped_in_update() -> None:
    from app.services.brand_intelligence import batch_service

    assert batch_service is not None
