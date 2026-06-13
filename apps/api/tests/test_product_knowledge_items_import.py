"""Product Knowledge items import unit tests."""

import asyncio
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.schemas.brand_product_knowledge import BrandProductKnowledgeItemProposal
from app.services.brand_intelligence.product_knowledge_items_import import (
    ITEMS_IMPORT_SYSTEM_PROMPT,
    compute_item_missing_fields,
    import_items_from_file,
)


def test_item_proposal_parses_camelcase() -> None:
    proposal = BrandProductKnowledgeItemProposal.model_validate(
        {
            "productName": "Miele di Limone",
            "productLine": "Miele",
            "origin": "Sicilia",
            "tasteNotes": "Agrumato",
            "objections": ["Troppo dolce"],
            "faq": [{"question": "Come si usa?", "answer": "A crudo"}],
        }
    )
    assert proposal.product_name == "Miele di Limone"
    assert proposal.origin == "Sicilia"
    assert proposal.objections == ["Troppo dolce"]


def test_compute_item_missing_fields() -> None:
    proposal = BrandProductKnowledgeItemProposal.model_validate(
        {
            "productName": "Polline",
            "origin": "Calabria",
        }
    )
    missing = compute_item_missing_fields(proposal)
    assert "productLine" in missing
    assert "strategicDescription" in missing
    assert "origin" not in missing


def test_import_items_empty_file_raises() -> None:
    async def run() -> None:
        with pytest.raises(HTTPException) as exc:
            await import_items_from_file(
                None,  # type: ignore[arg-type]
                uuid4(),
                filename="empty.txt",
                content_type="text/plain",
                data=b"",
            )
        assert exc.value.status_code == 422

    asyncio.run(run())


def test_import_items_openai_not_configured() -> None:
    async def run() -> None:
        with (
            patch(
                "app.services.brand_intelligence.product_knowledge_items_import.extract_text_from_bytes",
                return_value="Miele di Limone: origine Sicilia, gusto agrumato.",
            ),
            patch(
                "app.services.brand_intelligence.product_knowledge_items_import.is_openai_configured",
                return_value=False,
            ),
            pytest.raises(HTTPException) as exc,
        ):
            await import_items_from_file(
                None,  # type: ignore[arg-type]
                uuid4(),
                filename="catalog.txt",
                content_type="text/plain",
                data=b"content",
            )
        assert exc.value.status_code == 503
        assert "OPENAI_API_KEY" in exc.value.detail

    asyncio.run(run())


def test_import_items_success_mock_ai() -> None:
    async def run() -> None:
        ai_response = {
            "items": [
                {
                    "productName": "Miele di Limone",
                    "productLine": "Miele",
                    "origin": "Sicilia",
                    "tasteNotes": "Agrumato",
                    "targetAudience": "",
                    "conservation": "",
                    "warnings": [],
                },
                {
                    "productName": "Polline",
                    "origin": "Calabria",
                    "warnings": ["Dato dedotto dal contesto"],
                },
            ]
        }
        captured: dict = {}

        async def fake_generate(*, system_prompt: str, user_prompt: str, timeout: float):
            captured["system_prompt"] = system_prompt
            return ai_response

        with (
            patch(
                "app.services.brand_intelligence.product_knowledge_items_import.extract_text_from_bytes",
                return_value="MIELE DI LIMONE origine Sicilia. POLLINE Calabria.",
            ),
            patch(
                "app.services.brand_intelligence.product_knowledge_items_import.is_openai_configured",
                return_value=True,
            ),
            patch(
                "app.services.brand_intelligence.product_knowledge_items_import._load_safe_claims_block",
                new=AsyncMock(return_value=""),
            ),
            patch(
                "app.services.brand_intelligence.product_knowledge_items_import.generate_structured_json",
                side_effect=fake_generate,
            ),
            patch(
                "app.services.brand_intelligence.product_knowledge_items_import.suggest_shopify_matches",
                new=AsyncMock(),
            ),
        ):
            result = await import_items_from_file(
                None,  # type: ignore[arg-type]
                uuid4(),
                filename="master.pdf",
                content_type="application/pdf",
                data=b"pdf",
            )

        assert len(result.proposal.items) == 2
        assert result.proposal.items[0].product_name == "Miele di Limone"
        assert result.proposal.items[0].target_audience is None
        assert "targetAudience" in result.proposal.items[0].missing_fields
        assert "schede prodotto SPECIFICHE" in captured["system_prompt"]
        assert "NON estrarre regole generali" in ITEMS_IMPORT_SYSTEM_PROMPT

    asyncio.run(run())


def test_import_items_no_products_raises() -> None:
    async def run() -> None:
        with (
            patch(
                "app.services.brand_intelligence.product_knowledge_items_import.extract_text_from_bytes",
                return_value="Testo generico senza prodotti.",
            ),
            patch(
                "app.services.brand_intelligence.product_knowledge_items_import.is_openai_configured",
                return_value=True,
            ),
            patch(
                "app.services.brand_intelligence.product_knowledge_items_import._load_safe_claims_block",
                new=AsyncMock(return_value=""),
            ),
            patch(
                "app.services.brand_intelligence.product_knowledge_items_import.generate_structured_json",
                return_value={"items": []},
            ),
            pytest.raises(HTTPException) as exc,
        ):
            await import_items_from_file(
                None,  # type: ignore[arg-type]
                uuid4(),
                filename="empty.txt",
                content_type="text/plain",
                data=b"x",
            )
        assert exc.value.status_code == 422
        assert "Nessun prodotto" in exc.value.detail

    asyncio.run(run())
