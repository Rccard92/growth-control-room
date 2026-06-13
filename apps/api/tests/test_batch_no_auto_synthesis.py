"""Batch processor no longer auto-runs section synthesis."""

from pathlib import Path


def test_batch_processor_does_not_call_synthesize_batch() -> None:
    source = Path(__file__).resolve().parents[1] / "app" / "services" / "brand_intelligence" / "batch_processor.py"
    content = source.read_text(encoding="utf-8")
    assert "synthesize_batch" not in content
