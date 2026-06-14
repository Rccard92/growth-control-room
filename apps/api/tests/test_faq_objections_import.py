"""FAQ & Objections import unit tests."""

import asyncio
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.schemas.brand_faq_objections import BrandFaqObjectionsProposal
from app.services.brand_intelligence.faq_objections_import import import_faq_objections_from_file


def test_faq_objections_proposal_parses_string_lists() -> None:
    proposal = BrandFaqObjectionsProposal.model_validate(
        {
            "generalFaq": ["Domanda: Spedizioni?\nRisposta: 48h"],
            "objections": ["Prezzo alto"],
            "recommendedAnswers": ["Obiezione: Prezzo\nRisposta consigliata: Valore"],
        }
    )
    assert proposal.general_faq is not None
    assert "Spedizioni?" in proposal.general_faq[0]
    assert proposal.objections == ["Prezzo alto"]


def test_import_faq_objections_empty_file_raises() -> None:
    async def run() -> None:
        with pytest.raises(HTTPException) as exc:
            await import_faq_objections_from_file(
                None,  # type: ignore[arg-type]
                uuid4(),
                filename="empty.txt",
                content_type="text/plain",
                data=b"",
            )
        assert exc.value.status_code == 422

    asyncio.run(run())


def test_import_faq_objections_openai_not_configured() -> None:
    async def run() -> None:
        with (
            patch(
                "app.services.brand_intelligence.faq_objections_import.extract_text_from_bytes",
                return_value="FAQ: come ordino? Risposta: dal sito.",
            ),
            patch(
                "app.services.brand_intelligence.faq_objections_import.is_openai_configured",
                return_value=False,
            ),
            pytest.raises(HTTPException) as exc,
        ):
            await import_faq_objections_from_file(
                None,  # type: ignore[arg-type]
                uuid4(),
                filename="faq.txt",
                content_type="text/plain",
                data=b"content",
            )
        assert exc.value.status_code == 503

    asyncio.run(run())


def test_import_faq_objections_objections_as_objects_no_500() -> None:
    async def run() -> None:
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=AsyncMock(scalar_one_or_none=lambda: None))
        with (
            patch(
                "app.services.brand_intelligence.faq_objections_import.extract_text_from_bytes",
                return_value="Domanda: Spedite gratis? Obiezione: costa troppo.",
            ),
            patch(
                "app.services.brand_intelligence.faq_objections_import.is_openai_configured",
                return_value=True,
            ),
            patch(
                "app.services.brand_intelligence.faq_objections_import.generate_structured_json",
                new=AsyncMock(
                    return_value={
                        "generalFaq": [{"question": "Spedite gratis?", "answer": "Sopra 50€"}],
                        "objections": [
                            {
                                "objection": "Costa troppo",
                                "answer": "Spiega qualità artigianale",
                            }
                        ],
                    }
                ),
            ),
        ):
            result = await import_faq_objections_from_file(
                mock_session,
                uuid4(),
                filename="faq.txt",
                content_type="text/plain",
                data=b"content",
            )
            assert result.proposal.objections == ["Costa troppo"]
            assert result.proposal.recommended_answers is not None
            assert len(result.proposal.recommended_answers) >= 1
            assert result.confidence > 0

    asyncio.run(run())


def test_import_faq_objections_validation_error_returns_422() -> None:
    async def run() -> None:
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=AsyncMock(scalar_one_or_none=lambda: None))
        with (
            patch(
                "app.services.brand_intelligence.faq_objections_import.extract_text_from_bytes",
                return_value="Testo FAQ.",
            ),
            patch(
                "app.services.brand_intelligence.faq_objections_import.is_openai_configured",
                return_value=True,
            ),
            patch(
                "app.services.brand_intelligence.faq_objections_import.generate_structured_json",
                new=AsyncMock(return_value={"generalFaq": "not-a-list"}),
            ),
            patch(
                "app.services.brand_intelligence.faq_objections_import.BrandFaqObjectionsProposal.model_validate",
                side_effect=ValidationError.from_exception_data(
                    "BrandFaqObjectionsProposal",
                    [],
                ),
            ),
            pytest.raises(HTTPException) as exc,
        ):
            await import_faq_objections_from_file(
                mock_session,
                uuid4(),
                filename="faq.txt",
                content_type="text/plain",
                data=b"content",
            )
        assert exc.value.status_code == 422
        assert "Impossibile normalizzare la proposta FAQ" in str(exc.value.detail)

    asyncio.run(run())
