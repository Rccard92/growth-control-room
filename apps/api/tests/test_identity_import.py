"""Brand Identity import and apply unit tests."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.schemas.brand_identity_visual import BrandIdentityProposal
from app.services.brand_intelligence.identity_import import import_identity_from_file
from app.services.brand_intelligence.identity_service import apply_identity_proposal

def test_brand_identity_proposal_parses_camelcase() -> None:
    proposal = BrandIdentityProposal.model_validate(
        {
            "positioning": "Premium artisan",
            "brandValues": ["qualità", "tradizione"],
            "whatBrandIs": "Un brand artigianale",
        }
    )
    assert proposal.positioning == "Premium artisan"
    assert proposal.brand_values == ["qualità", "tradizione"]
    assert proposal.what_brand_is == "Un brand artigianale"


def test_import_identity_empty_file_raises() -> None:
    async def run() -> None:
        with pytest.raises(HTTPException) as exc:
            await import_identity_from_file(
                None,  # type: ignore[arg-type]
                uuid4(),
                filename="empty.txt",
                content_type="text/plain",
                data=b"",
            )
        assert exc.value.status_code == 422

    asyncio.run(run())


def test_import_identity_unsupported_type_raises() -> None:
    async def run() -> None:
        with pytest.raises(HTTPException) as exc:
            await import_identity_from_file(
                None,  # type: ignore[arg-type]
                uuid4(),
                filename="virus.exe",
                content_type="application/octet-stream",
                data=b"fake",
            )
        assert exc.value.status_code == 422

    asyncio.run(run())


def test_import_identity_openai_not_configured() -> None:
    async def run() -> None:
        with (
            patch(
                "app.services.brand_intelligence.identity_import.extract_text_from_bytes",
                return_value="Testo brand identity valido con abbastanza contenuto.",
            ),
            patch(
                "app.services.brand_intelligence.identity_import.is_openai_configured",
                return_value=False,
            ),
            pytest.raises(HTTPException) as exc,
        ):
            await import_identity_from_file(
                None,  # type: ignore[arg-type]
                uuid4(),
                filename="brand.txt",
                content_type="text/plain",
                data=b"content",
            )
        assert exc.value.status_code == 503
        assert "OPENAI_API_KEY" in str(exc.value.detail)

    asyncio.run(run())


def test_import_identity_success_mock_ai() -> None:
    async def run() -> None:
        with (
            patch(
                "app.services.brand_intelligence.identity_import.extract_text_from_bytes",
                return_value="Il brand si posiziona come produttore artigianale di miele.",
            ),
            patch(
                "app.services.brand_intelligence.identity_import.is_openai_configured",
                return_value=True,
            ),
            patch(
                "app.services.brand_intelligence.identity_import.generate_structured_json",
                new=AsyncMock(
                    return_value={
                        "positioning": "Artigianale premium",
                        "brandValues": ["qualità", "natura"],
                        "differentiators": ["apicoltura locale"],
                    }
                ),
            ),
        ):
            result = await import_identity_from_file(
                None,  # type: ignore[arg-type]
                uuid4(),
                filename="brand.txt",
                content_type="text/plain",
                data=b"content",
            )
            assert result.proposal.positioning == "Artigianale premium"
            assert len(result.proposal.brand_values or []) == 2
            assert result.confidence > 0

    asyncio.run(run())


def test_apply_identity_proposal_saves_fields() -> None:
    row = SimpleNamespace(
        positioning=None,
        brand_values=None,
        differentiators=None,
        production_principles=None,
        quality_principles=None,
        trust_elements=None,
        what_brand_is=None,
        what_brand_is_not=None,
        storytelling_notes=None,
    )
    mock_session = AsyncMock()
    proposal = BrandIdentityProposal.model_validate(
        {
            "positioning": "Premium niche",
            "brandValues": ["craft", "trust"],
            "whatBrandIs": "Artigianale",
        }
    )

    async def run() -> None:
        with patch(
            "app.services.brand_intelligence.identity_service._get_or_create_identity",
            new=AsyncMock(return_value=row),
        ):
            result = await apply_identity_proposal(mock_session, uuid4(), proposal)
            assert result.positioning == "Premium niche"
            assert result.brand_values == ["craft", "trust"]
            assert result.what_brand_is == "Artigianale"

    asyncio.run(run())


def test_apply_identity_partial_does_not_wipe_existing() -> None:
    row = SimpleNamespace(
        positioning="Existing positioning",
        brand_values=["existing"],
        differentiators=None,
        production_principles=None,
        quality_principles=None,
        trust_elements=None,
        what_brand_is="Existing is",
        what_brand_is_not=None,
        storytelling_notes=None,
    )
    mock_session = AsyncMock()
    proposal = BrandIdentityProposal.model_validate({"storytellingNotes": "New notes"})

    async def run() -> None:
        with patch(
            "app.services.brand_intelligence.identity_service._get_or_create_identity",
            new=AsyncMock(return_value=row),
        ):
            result = await apply_identity_proposal(mock_session, uuid4(), proposal)
            assert result.positioning == "Existing positioning"
            assert result.brand_values == ["existing"]
            assert result.storytelling_notes == "New notes"

    asyncio.run(run())
