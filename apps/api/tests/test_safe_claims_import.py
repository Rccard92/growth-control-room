"""Safe Claims import and apply unit tests."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.schemas.brand_safe_claims import BrandSafeClaimsProposal
from app.services.brand_intelligence.safe_claims_import import import_safe_claims_from_file
from app.services.brand_intelligence.safe_claims_service import apply_safe_claims_proposal


def test_brand_safe_claims_proposal_parses_camelcase() -> None:
    proposal = BrandSafeClaimsProposal.model_validate(
        {
            "allowedClaims": ["100% naturale"],
            "forbiddenClaims": ["cura malattie"],
            "cautionClaims": ["effetto benefico"],
        }
    )
    assert proposal.allowed_claims == ["100% naturale"]
    assert proposal.forbidden_claims == ["cura malattie"]
    assert proposal.caution_claims == ["effetto benefico"]


def test_import_safe_claims_empty_file_raises() -> None:
    async def run() -> None:
        with pytest.raises(HTTPException) as exc:
            await import_safe_claims_from_file(
                None,  # type: ignore[arg-type]
                uuid4(),
                filename="empty.txt",
                content_type="text/plain",
                data=b"",
            )
        assert exc.value.status_code == 422

    asyncio.run(run())


def test_import_safe_claims_openai_not_configured() -> None:
    async def run() -> None:
        with (
            patch(
                "app.services.brand_intelligence.safe_claims_import.extract_text_from_bytes",
                return_value="Policy claim: non usare promesse mediche.",
            ),
            patch(
                "app.services.brand_intelligence.safe_claims_import.is_openai_configured",
                return_value=False,
            ),
            pytest.raises(HTTPException) as exc,
        ):
            await import_safe_claims_from_file(
                None,  # type: ignore[arg-type]
                uuid4(),
                filename="policy.txt",
                content_type="text/plain",
                data=b"content",
            )
        assert exc.value.status_code == 503
        assert "OPENAI_API_KEY" in str(exc.value.detail)

    asyncio.run(run())


def test_import_safe_claims_success_mock_ai() -> None:
    async def run() -> None:
        with (
            patch(
                "app.services.brand_intelligence.safe_claims_import.extract_text_from_bytes",
                return_value="Claim consentiti: artigianale. Vietati: cura malattie.",
            ),
            patch(
                "app.services.brand_intelligence.safe_claims_import.is_openai_configured",
                return_value=True,
            ),
            patch(
                "app.services.brand_intelligence.safe_claims_import.generate_structured_json",
                new=AsyncMock(
                    return_value={
                        "allowedClaims": ["Prodotto artigianale"],
                        "forbiddenClaims": ["Cura malattie"],
                        "disclaimers": ["Non sostituisce dieta equilibrata"],
                    }
                ),
            ),
        ):
            result = await import_safe_claims_from_file(
                None,  # type: ignore[arg-type]
                uuid4(),
                filename="policy.txt",
                content_type="text/plain",
                data=b"content",
            )
            assert len(result.proposal.allowed_claims or []) == 1
            assert len(result.proposal.forbidden_claims or []) == 1
            assert result.confidence > 0

    asyncio.run(run())


def test_apply_safe_claims_proposal_saves_fields() -> None:
    row = SimpleNamespace(
        allowed_claims=None,
        forbidden_claims=None,
        caution_claims=None,
        disclaimers=None,
        health_claim_rules=None,
        competitor_rules=None,
        process_secrets=None,
        tone_red_flags=None,
        notes=None,
    )
    mock_session = AsyncMock()
    proposal = BrandSafeClaimsProposal.model_validate(
        {
            "allowedClaims": ["Artigianale"],
            "forbiddenClaims": ["Cura"],
        }
    )

    async def run() -> None:
        with patch(
            "app.services.brand_intelligence.safe_claims_service._get_or_create_safe_claims",
            new=AsyncMock(return_value=row),
        ):
            result = await apply_safe_claims_proposal(mock_session, uuid4(), proposal)
            assert result.allowed_claims == ["Artigianale"]
            assert result.forbidden_claims == ["Cura"]

    asyncio.run(run())


def test_apply_safe_claims_partial_does_not_wipe_existing() -> None:
    row = SimpleNamespace(
        allowed_claims=["Existing allowed"],
        forbidden_claims=["Existing forbidden"],
        caution_claims=None,
        disclaimers=None,
        health_claim_rules=None,
        competitor_rules=None,
        process_secrets=None,
        tone_red_flags=None,
        notes=None,
    )
    mock_session = AsyncMock()
    proposal = BrandSafeClaimsProposal.model_validate({"notes": "New notes"})

    async def run() -> None:
        with patch(
            "app.services.brand_intelligence.safe_claims_service._get_or_create_safe_claims",
            new=AsyncMock(return_value=row),
        ):
            result = await apply_safe_claims_proposal(mock_session, uuid4(), proposal)
            assert result.allowed_claims == ["Existing allowed"]
            assert result.forbidden_claims == ["Existing forbidden"]
            assert result.notes == "New notes"

    asyncio.run(run())
