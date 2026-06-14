"""Batch processor synthesis integration tests."""

from pathlib import Path

from app.services.brand_intelligence.synthesis import SECTION_SYNTHESIS_ORDER

_BATCH_PROCESSOR = (
    Path(__file__).resolve().parents[1]
    / "app"
    / "services"
    / "brand_intelligence"
    / "batch_processor.py"
)


def test_synthesis_progress_range_in_batch_processor() -> None:
    source = _BATCH_PROCESSOR.read_text(encoding="utf-8")
    assert "progress_percent=35" in source
    assert "progress_percent=73" in source
    assert "await apply_conflict_detection_to_batch" in source
    assert "await finalize_batch_counts" in source
    idx_conflict = source.index("await apply_conflict_detection_to_batch")
    idx_finalize = source.index("await finalize_batch_counts")
    assert idx_conflict < idx_finalize


def test_synthesis_order_matches_nine_bi_sections() -> None:
    assert len(SECTION_SYNTHESIS_ORDER) == 9
    assert "brand_profile" in SECTION_SYNTHESIS_ORDER
    assert "assets" in SECTION_SYNTHESIS_ORDER
