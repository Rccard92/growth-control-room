"""Batch processor external fetch integration tests."""

from pathlib import Path

_BATCH_PROCESSOR = (
    Path(__file__).resolve().parents[1]
    / "app"
    / "services"
    / "brand_intelligence"
    / "batch_processor.py"
)


def test_batch_processor_fetches_external_before_ai_facts() -> None:
    source = _BATCH_PROCESSOR.read_text(encoding="utf-8")
    assert "fetch_batch_external_sources" in source
    assert "Recupero fonti esterne" in source
    idx_fetch = source.index("fetch_batch_external_sources")
    idx_ai = source.index("Estrazione AI file")
    assert idx_fetch < idx_ai


def test_batch_processor_progress_ranges() -> None:
    source = _BATCH_PROCESSOR.read_text(encoding="utf-8")
    assert "progress_percent=35" in source
    assert "progress_percent=50" in source
    assert "progress_percent=75" in source
