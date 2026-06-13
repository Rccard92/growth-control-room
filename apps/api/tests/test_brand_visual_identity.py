"""Brand Visual Identity service unit tests (no DB)."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.schemas.brand_identity_visual import VisualColorSwatch, VisualExtractProposal
from app.services.brand_intelligence.visual_identity_service import (
    apply_visual_proposal,
    visual_completion,
    visual_has_minimum,
    visual_missing_fields,
)


def test_visual_has_minimum_with_logo() -> None:
    visual = SimpleNamespace(
        primary_logo_url="https://x.test/logo.png", primary_color=None, color_palette=None
    )
    assert visual_has_minimum(visual) is True


def test_visual_missing_fields_empty() -> None:
    missing = visual_missing_fields(None)
    assert "primary_logo_url" in missing
    assert "primary_color" in missing


def test_visual_completion_partial() -> None:
    visual = SimpleNamespace(
        primary_logo_url="https://x.test/logo.png",
        primary_color="#336699",
        secondary_color=None,
        accent_color=None,
        color_palette=None,
    )
    assert visual_completion(visual) == "partial"


def test_apply_visual_proposal_maps_palette_roles() -> None:
    row = SimpleNamespace(
        primary_logo_url=None,
        favicon_url=None,
        visual_style_notes=None,
        color_palette=None,
        website_extracted_palette=None,
        primary_color=None,
        secondary_color=None,
        accent_color=None,
        background_color=None,
        text_color=None,
        fonts=None,
    )
    mock_session = AsyncMock()
    proposal = VisualExtractProposal(
        primary_logo_url="https://brand.test/logo.png",
        favicon_url="https://brand.test/favicon.ico",
        color_palette=[
            VisualColorSwatch(hex="#112233", role="primary"),
            VisualColorSwatch(hex="#AABBCC", role="secondary"),
            VisualColorSwatch(hex="#FF8800", role="accent"),
        ],
        visual_style_notes="Clean minimal",
    )

    async def run() -> None:
        with patch(
            "app.services.brand_intelligence.visual_identity_service._get_or_create_visual",
            new=AsyncMock(return_value=row),
        ):
            result = await apply_visual_proposal(mock_session, uuid4(), proposal)
            assert result.primary_logo_url == "https://brand.test/logo.png"
            assert result.primary_color == "#112233"
            assert result.secondary_color == "#AABBCC"
            assert result.accent_color == "#FF8800"
            assert result.website_extracted_palette is not None

    asyncio.run(run())
