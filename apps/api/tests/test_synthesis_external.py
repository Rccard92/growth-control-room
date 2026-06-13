"""Synthesis external sources integration tests."""

from app.services.brand_intelligence.synthesis import SYNTHESIS_SYSTEM_PROMPT


def test_synthesis_prompt_includes_external_ids() -> None:
    assert "source_external_ids" in SYNTHESIS_SYSTEM_PROMPT
    assert "external sources" in SYNTHESIS_SYSTEM_PROMPT.lower() or "source_external" in SYNTHESIS_SYSTEM_PROMPT


def test_persist_section_draft_accepts_external_ids() -> None:
    import inspect

    from app.services.brand_intelligence import synthesis

    sig = inspect.signature(synthesis._persist_section_draft)
    assert "source_external_ids" in sig.parameters
