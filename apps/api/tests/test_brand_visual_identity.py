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


def test_visual_extract_proposal_parses_camelcase() -> None:
    proposal = VisualExtractProposal.model_validate(
        {
            "primaryLogoUrl": "https://brand.test/logo.png",
            "faviconUrl": "https://brand.test/favicon.ico",
            "colorPalette": [{"hex": "#112233", "role": "primary"}],
            "visualStyleNotes": "Clean minimal",
        }
    )
    assert proposal.primary_logo_url == "https://brand.test/logo.png"
    assert proposal.favicon_url == "https://brand.test/favicon.ico"
    assert len(proposal.color_palette) == 1
    assert proposal.color_palette[0].hex == "#112233"
    assert proposal.visual_style_notes == "Clean minimal"


def test_apply_visual_proposal_maps_palette_roles() -> None:
    row = SimpleNamespace(
        primary_logo_url=None,
        secondary_logo_url=None,
        favicon_url=None,
        visual_style_notes=None,
        image_style_notes=None,
        color_palette=None,
        website_extracted_palette=None,
        primary_color=None,
        secondary_color=None,
        accent_color=None,
        background_color=None,
        text_color=None,
        fonts=None,
        do_show=None,
        do_not_show=None,
    )
    mock_session = AsyncMock()
    proposal = VisualExtractProposal(
        primary_logo_url="https://brand.test/logo.png",
        favicon_url="https://brand.test/favicon.ico",
        color_palette=[
            VisualColorSwatch(hex="#112233", role="primary"),
            VisualColorSwatch(hex="#AABBCC", role="secondary"),
            VisualColorSwatch(hex="#FF8800", role="accent"),
            VisualColorSwatch(hex="#FFFFFF", role="background"),
            VisualColorSwatch(hex="#111111", role="text"),
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
            assert result.favicon_url == "https://brand.test/favicon.ico"
            assert result.primary_color == "#112233"
            assert result.secondary_color == "#AABBCC"
            assert result.accent_color == "#FF8800"
            assert result.background_color == "#FFFFFF"
            assert result.text_color == "#111111"
            assert result.website_extracted_palette is not None
            assert result.visual_style_notes == "Clean minimal"

    asyncio.run(run())


def test_apply_visual_proposal_camelcase_payload() -> None:
    row = SimpleNamespace(
        primary_logo_url="https://existing.test/logo.png",
        secondary_logo_url=None,
        favicon_url=None,
        visual_style_notes=None,
        image_style_notes=None,
        color_palette=None,
        website_extracted_palette=None,
        primary_color="#000000",
        secondary_color=None,
        accent_color=None,
        background_color=None,
        text_color=None,
        fonts=None,
        do_show=None,
        do_not_show=None,
    )
    mock_session = AsyncMock()
    proposal = VisualExtractProposal.model_validate(
        {
            "faviconUrl": "https://brand.test/favicon.ico",
            "colorPalette": [{"hex": "#AABBCC", "role": "secondary"}],
        }
    )

    async def run() -> None:
        with patch(
            "app.services.brand_intelligence.visual_identity_service._get_or_create_visual",
            new=AsyncMock(return_value=row),
        ):
            result = await apply_visual_proposal(mock_session, uuid4(), proposal)
            assert result.primary_logo_url == "https://existing.test/logo.png"
            assert result.favicon_url == "https://brand.test/favicon.ico"
            assert result.secondary_color == "#AABBCC"
            assert result.primary_color == "#000000"

    asyncio.run(run())


def test_apply_visual_proposal_does_not_wipe_existing_logo() -> None:
    row = SimpleNamespace(
        primary_logo_url="https://existing.test/logo.png",
        secondary_logo_url=None,
        favicon_url="https://existing.test/favicon.ico",
        visual_style_notes="Existing notes",
        image_style_notes=None,
        color_palette=[{"hex": "#111111", "role": "primary"}],
        website_extracted_palette=None,
        primary_color="#111111",
        secondary_color=None,
        accent_color=None,
        background_color=None,
        text_color=None,
        fonts=None,
        do_show=None,
        do_not_show=None,
    )
    mock_session = AsyncMock()
    proposal = VisualExtractProposal.model_validate({"visualStyleNotes": "Updated notes"})

    async def run() -> None:
        with patch(
            "app.services.brand_intelligence.visual_identity_service._get_or_create_visual",
            new=AsyncMock(return_value=row),
        ):
            result = await apply_visual_proposal(mock_session, uuid4(), proposal)
            assert result.primary_logo_url == "https://existing.test/logo.png"
            assert result.favicon_url == "https://existing.test/favicon.ico"
            assert result.visual_style_notes == "Updated notes"
            assert result.color_palette == [{"hex": "#111111", "role": "primary"}]

    asyncio.run(run())
