"""FAQ & Objections service completion and apply tests."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.schemas.brand_faq_objections import BrandFaqObjectionsProposal, FaqEntry
from app.services.brand_intelligence.faq_objections_service import (
    apply_faq_objections_proposal,
    faq_objections_completion,
    faq_objections_missing_fields,
)


def test_faq_objections_completion_empty() -> None:
    assert faq_objections_completion(None) == "empty"


def test_faq_objections_completion_partial() -> None:
    row = SimpleNamespace(
        general_faq=None,
        product_process_questions=None,
        purchase_shipping_questions=None,
        objections=["Prezzo alto"],
        myths_misconceptions=None,
        recommended_answers=None,
        content_opportunities=None,
        social_comment_insights=None,
        notes=None,
    )
    assert faq_objections_completion(row) == "partial"


def test_faq_objections_completion_complete() -> None:
    row = SimpleNamespace(
        general_faq=[{"question": "Spedite in tutta Italia?", "answer": "Sì"}],
        product_process_questions=None,
        purchase_shipping_questions=None,
        objections=["Non mi fido"],
        myths_misconceptions=None,
        recommended_answers=["Rispondi con garanzia soddisfatti"],
        content_opportunities=None,
        social_comment_insights=None,
        notes=None,
    )
    assert faq_objections_completion(row) == "complete"


def test_faq_objections_missing_fields() -> None:
    row = SimpleNamespace(
        general_faq=[{"question": "Q?", "answer": "A"}],
        product_process_questions=None,
        purchase_shipping_questions=None,
        objections=None,
        myths_misconceptions=None,
        recommended_answers=None,
        content_opportunities=None,
        social_comment_insights=None,
        notes=None,
    )
    missing = faq_objections_missing_fields(row)
    assert "objections" in missing
    assert "recommended_answers" in missing


def test_apply_faq_objections_proposal_merge_non_destructive() -> None:
    row = SimpleNamespace(
        general_faq=[{"question": "Esistente?", "answer": "Sì"}],
        product_process_questions=None,
        purchase_shipping_questions=None,
        objections=["Obiezione esistente"],
        myths_misconceptions=None,
        recommended_answers=["Risposta esistente"],
        content_opportunities=None,
        social_comment_insights=None,
        notes=None,
    )
    mock_session = AsyncMock()
    proposal = BrandFaqObjectionsProposal.model_validate(
        {"notes": "Nuove note operative"}
    )

    async def run() -> None:
        with patch(
            "app.services.brand_intelligence.faq_objections_service._get_or_create_faq_objections",
            new=AsyncMock(return_value=row),
        ):
            result = await apply_faq_objections_proposal(mock_session, uuid4(), proposal)
            assert result.general_faq == [{"question": "Esistente?", "answer": "Sì"}]
            assert result.objections == ["Obiezione esistente"]
            assert result.notes == "Nuove note operative"

    asyncio.run(run())


def test_apply_faq_objections_proposal_writes_faq() -> None:
    row = SimpleNamespace(
        general_faq=None,
        product_process_questions=None,
        purchase_shipping_questions=None,
        objections=None,
        myths_misconceptions=None,
        recommended_answers=None,
        content_opportunities=None,
        social_comment_insights=None,
        notes=None,
    )
    mock_session = AsyncMock()
    proposal = BrandFaqObjectionsProposal(
        general_faq=[FaqEntry(question="Come ordino?", answer="Dal sito")],
        objections=["Costa troppo"],
        recommended_answers=["Spiega il valore artigianale"],
    )

    async def run() -> None:
        with patch(
            "app.services.brand_intelligence.faq_objections_service._get_or_create_faq_objections",
            new=AsyncMock(return_value=row),
        ):
            result = await apply_faq_objections_proposal(mock_session, uuid4(), proposal)
            assert result.general_faq == [{"question": "Come ordino?", "answer": "Dal sito"}]
            assert result.objections == ["Costa troppo"]

    asyncio.run(run())
