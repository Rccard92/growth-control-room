"""FAQ & Objections service completion and apply tests."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.schemas.brand_faq_objections import BrandFaqObjectionsProposal, BrandFaqObjectionsUpdate
from app.services.brand_intelligence.faq_objections_service import (
    apply_faq_objections_proposal,
    faq_objections_completion,
    faq_objections_missing_fields,
    normalize_faq_objections_row,
    upsert_faq_objections,
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
        general_faq=["Domanda: Spedite in tutta Italia?\nRisposta: Sì"],
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
        general_faq=["Domanda: Q?\nRisposta: A"],
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
        general_faq=["Domanda: Esistente?\nRisposta: Sì"],
        product_process_questions=None,
        purchase_shipping_questions=None,
        objections=["Obiezione esistente"],
        myths_misconceptions=None,
        recommended_answers=["Risposta esistente"],
        content_opportunities=None,
        social_comment_insights=None,
        notes=None,
        warnings=None,
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
            assert result.general_faq == ["Domanda: Esistente?\nRisposta: Sì"]
            assert result.objections == ["Obiezione esistente"]
            assert result.notes == "Nuove note operative"

    asyncio.run(run())


def test_apply_faq_objections_proposal_writes_string_lists() -> None:
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
        warnings=None,
    )
    mock_session = AsyncMock()
    proposal = BrandFaqObjectionsProposal(
        general_faq=["Domanda: Come ordino?\nRisposta: Dal sito"],
        objections=["Costa troppo"],
        recommended_answers=["Obiezione: Costa troppo\nRisposta consigliata: Valore artigianale"],
    )

    async def run() -> None:
        with patch(
            "app.services.brand_intelligence.faq_objections_service._get_or_create_faq_objections",
            new=AsyncMock(return_value=row),
        ):
            result = await apply_faq_objections_proposal(mock_session, uuid4(), proposal)
            assert result.general_faq == ["Domanda: Come ordino?\nRisposta: Dal sito"]
            assert result.objections == ["Costa troppo"]
            assert result.recommended_answers == [
                "Obiezione: Costa troppo\nRisposta consigliata: Valore artigianale"
            ]

    asyncio.run(run())


def test_upsert_faq_objections_with_dict_in_objections_does_not_crash() -> None:
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
        warnings=None,
    )
    mock_session = AsyncMock()
    payload = BrandFaqObjectionsUpdate.model_validate(
        {
            "generalFaq": ["Domanda: Q?\nRisposta: A"],
            "objections": [{"objection": "Costa troppo", "answer": "Valore"}],
        }
    )

    async def run() -> None:
        with patch(
            "app.services.brand_intelligence.faq_objections_service._get_or_create_faq_objections",
            new=AsyncMock(return_value=row),
        ):
            result = await upsert_faq_objections(mock_session, uuid4(), payload)
            assert result.general_faq == ["Domanda: Q?\nRisposta: A"]
            assert result.objections == [
                "Obiezione: Costa troppo\nRisposta consigliata: Valore"
            ]

    asyncio.run(run())


def test_upsert_faq_objections_with_list_str_on_all_fields() -> None:
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
        warnings=None,
    )
    mock_session = AsyncMock()
    payload = BrandFaqObjectionsUpdate(
        general_faq=["Domanda: Q?\nRisposta: A"],
        product_process_questions=["Domanda: P?\nRisposta: B"],
        purchase_shipping_questions=["Domanda: S?\nRisposta: C"],
        objections=["Obiezione 1"],
        myths_misconceptions=["Mito: X\nCorrezione: Y"],
        recommended_answers=["Risposta 1"],
        content_opportunities=["Opportunità 1"],
        social_comment_insights=["Insight: test | Dubbio: dubbio"],
        notes="Note test",
    )

    async def run() -> None:
        with patch(
            "app.services.brand_intelligence.faq_objections_service._get_or_create_faq_objections",
            new=AsyncMock(return_value=row),
        ):
            result = await upsert_faq_objections(mock_session, uuid4(), payload)
            assert result.general_faq == ["Domanda: Q?\nRisposta: A"]
            assert result.objections == ["Obiezione 1"]
            assert result.social_comment_insights == ["Insight: test | Dubbio: dubbio"]
            assert result.notes == "Note test"

    asyncio.run(run())


def test_faq_objections_completion_with_legacy_dict_does_not_crash() -> None:
    row = SimpleNamespace(
        general_faq=[{"question": "Spedite?", "answer": "Sì"}],
        product_process_questions=None,
        purchase_shipping_questions=None,
        objections=[{"objection": "Costa troppo", "answer": "Valore"}],
        myths_misconceptions=None,
        recommended_answers=["Risposta consigliata"],
        content_opportunities=None,
        social_comment_insights=[{"insight": "Cliente scettico", "doubt": "Prezzo"}],
        notes=None,
    )
    assert faq_objections_completion(row) == "complete"
    missing = faq_objections_missing_fields(row)
    assert missing == []


def test_normalize_faq_objections_row_converts_legacy_dicts() -> None:
    row = SimpleNamespace(
        general_faq=[{"question": "Q?", "answer": "A"}],
        product_process_questions=None,
        purchase_shipping_questions=None,
        objections=["plain"],
        myths_misconceptions=None,
        recommended_answers=None,
        content_opportunities=None,
        social_comment_insights=None,
    )
    changed = normalize_faq_objections_row(row)  # type: ignore[arg-type]
    assert changed is True
    assert row.general_faq == ["Domanda: Q?\nRisposta: A"]
    assert row.objections == ["plain"]
