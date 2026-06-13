"""Product Knowledge general import and apply unit tests."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.schemas.brand_product_knowledge import BrandProductKnowledgeGeneralProposal
from app.services.brand_intelligence.product_knowledge_general_import import import_general_from_file
from app.services.brand_intelligence.product_knowledge_general_service import apply_general_proposal


def test_general_proposal_parses_camelcase() -> None:
    proposal = BrandProductKnowledgeGeneralProposal.model_validate(
        {
            "generalPrinciples": ["Artigianale"],
            "commonStrengths": ["Qualità"],
            "commonFaq": [{"question": "Come si usa?", "answer": "A crudo"}],
        }
    )
    assert proposal.general_principles == ["Artigianale"]
    assert proposal.common_strengths == ["Qualità"]
    assert proposal.common_faq[0]["question"] == "Come si usa?"


def test_import_general_empty_file_raises() -> None:
    async def run() -> None:
        with pytest.raises(HTTPException) as exc:
            await import_general_from_file(
                None,  # type: ignore[arg-type]
                uuid4(),
                filename="empty.txt",
                content_type="text/plain",
                data=b"",
            )
        assert exc.value.status_code == 422

    asyncio.run(run())


def test_import_general_openai_not_configured() -> None:
    async def run() -> None:
        with (
            patch(
                "app.services.brand_intelligence.product_knowledge_general_import.extract_text_from_bytes",
                return_value="Catalogo prodotti con regole comuni di qualità artigianale.",
            ),
            patch(
                "app.services.brand_intelligence.product_knowledge_general_import.is_openai_configured",
                return_value=False,
            ),
            pytest.raises(HTTPException) as exc,
        ):
            await import_general_from_file(
                None,  # type: ignore[arg-type]
                uuid4(),
                filename="catalog.txt",
                content_type="text/plain",
                data=b"content",
            )
        assert exc.value.status_code == 503

    asyncio.run(run())


def test_import_general_success_mock_ai() -> None:
    async def run() -> None:
        with (
            patch(
                "app.services.brand_intelligence.product_knowledge_general_import.extract_text_from_bytes",
                return_value="Miele di Limone e Polline: entrambi artigianali, stessi principi qualità.",
            ),
            patch(
                "app.services.brand_intelligence.product_knowledge_general_import.is_openai_configured",
                return_value=True,
            ),
            patch(
                "app.services.brand_intelligence.product_knowledge_general_import._load_safe_claims_block",
                new=AsyncMock(return_value=""),
            ),
            patch(
                "app.services.brand_intelligence.product_knowledge_general_import.generate_structured_json",
                new=AsyncMock(
                    return_value={
                        "generalPrinciples": ["Produzione artigianale"],
                        "commonStrengths": ["Tracciabilità"],
                    }
                ),
            ),
        ):
            result = await import_general_from_file(
                None,  # type: ignore[arg-type]
                uuid4(),
                filename="catalog.txt",
                content_type="text/plain",
                data=b"content",
            )
            assert result.proposal.general_principles == ["Produzione artigianale"]
            assert result.confidence > 0

    asyncio.run(run())


def test_apply_general_partial_does_not_wipe() -> None:
    row = SimpleNamespace(
        general_principles=["Existing"],
        common_strengths=None,
        common_quality_rules=None,
        common_production_notes=None,
        common_usage_notes=None,
        common_objections=None,
        common_faq=None,
        communication_rules=None,
        product_storytelling_rules=None,
        notes=None,
    )
    mock_session = AsyncMock()
    proposal = BrandProductKnowledgeGeneralProposal.model_validate({"notes": "New notes"})

    async def run() -> None:
        with patch(
            "app.services.brand_intelligence.product_knowledge_general_service._get_or_create_general",
            new=AsyncMock(return_value=row),
        ):
            result = await apply_general_proposal(mock_session, uuid4(), proposal)
            assert result.general_principles == ["Existing"]
            assert result.notes == "New notes"

    asyncio.run(run())
