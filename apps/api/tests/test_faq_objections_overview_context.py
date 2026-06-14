"""Overview and AI Context resilience tests for legacy FAQ dict data."""

import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.schemas.brand_faq_objections import BrandFaqObjectionsRead
from app.services.brand_intelligence.context import BrandIntelligenceContextBuilder
from app.services.brand_intelligence.faq_objections_service import faq_objections_completion
from app.services.brand_intelligence.score import compute_brand_knowledge_score

_NOW = datetime.now(timezone.utc)
_PID = uuid4()


def _legacy_faq_row() -> SimpleNamespace:
    return SimpleNamespace(
        general_faq=[{"question": "Spedite in Italia?", "answer": "Sì, in 48h"}],
        product_process_questions=None,
        purchase_shipping_questions=None,
        objections=[{"objection": "Costa troppo", "answer": "Valore artigianale"}],
        myths_misconceptions=None,
        recommended_answers=["Risposta consigliata test"],
        content_opportunities=None,
        social_comment_insights=[{"insight": "Cliente scettico", "doubt": "Prezzo alto"}],
        notes=None,
    )


def test_faq_objections_completion_legacy_dict_no_crash() -> None:
    assert faq_objections_completion(_legacy_faq_row()) == "complete"


def test_brand_faq_objections_read_from_legacy_dict_returns_string_lists() -> None:
    row = SimpleNamespace(
        id=uuid4(),
        project_id=_PID,
        general_faq=[{"question": "FAQ?", "answer": "Sì"}],
        product_process_questions=None,
        purchase_shipping_questions=None,
        objections=["Obiezione plain"],
        myths_misconceptions=None,
        recommended_answers=None,
        content_opportunities=None,
        social_comment_insights=None,
        notes=None,
        last_import_source=None,
        last_confidence=None,
        warnings=None,
        created_at=_NOW,
        updated_at=_NOW,
    )
    read = BrandFaqObjectionsRead.model_validate(row)
    assert read.general_faq == ["Domanda: FAQ?\nRisposta: Sì"]
    assert read.objections == ["Obiezione plain"]


def test_format_faq_objections_for_prompt_with_legacy_read() -> None:
    read = BrandFaqObjectionsRead(
        id=uuid4(),
        project_id=_PID,
        general_faq=["Domanda: Spedite?\nRisposta: Sì"],
        objections=["Costa troppo"],
        recommended_answers=["Valore artigianale"],
        created_at=_NOW,
        updated_at=_NOW,
    )
    text = BrandIntelligenceContextBuilder.format_faq_objections_for_prompt(read)
    assert text is not None
    assert "FAQ & OBJECTIONS" in text
    assert "Spedite?" in text
    assert "Costa troppo" in text


def test_compute_brand_knowledge_score_with_legacy_faq_dict_no_crash() -> None:
    legacy_faq = _legacy_faq_row()
    mock_session = AsyncMock()

    async def mock_execute(stmt):
        result = AsyncMock()
        stmt_str = str(stmt)
        if "brand_faq_objections" in stmt_str:
            result.scalar_one_or_none = lambda: legacy_faq
            result.scalar_one = lambda: 0
        else:
            result.scalar_one_or_none = lambda: None
            result.scalar_one = lambda: 0
        return result

    mock_session.execute = mock_execute

    async def run() -> None:
        score = await compute_brand_knowledge_score(mock_session, _PID)
        assert score.section_scores["faqObjections"] > 0

    asyncio.run(run())
