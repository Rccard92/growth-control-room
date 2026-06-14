"""Editorial brief generator service tests."""

import asyncio
from datetime import date, datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.schemas.content_seo_editorial import (
    EditorialBriefUpdateRequest,
    normalize_editorial_brief_payload,
)
from app.services.content.editorial_brief_service import (
    build_bi_warnings,
    generate_editorial_brief,
    update_editorial_brief,
)
from app.services.ai.openai_client import OpenAIRequestError


def _sample_ai_brief() -> dict:
    return {
        "proposedTitle": "Guida olio EVO",
        "searchIntent": "informational",
        "targetAudience": "Appassionati cucina",
        "primaryKeyword": "olio evo",
        "secondaryKeywords": ["extravergine", "condimento"],
        "contentAngle": "Educare sulla qualità",
        "h2H3Structure": ["H2: Cos'è l'olio EVO", "H3: Come sceglierlo"],
        "productsToLink": ["Olio classico"],
        "faqToInclude": ["Come conservarlo?"],
        "claimsToAvoid": ["Cura malattie"],
        "safeClaimsToUse": ["Spremitura a freddo"],
        "recommendedCta": "Scopri la linea",
        "metaTitle": "Olio EVO: guida",
        "metaDescription": "Guida completa all'olio extravergine.",
        "internalLinksSuggestions": ["/collections/oli"],
        "notes": "Tono educativo",
        "warnings": [],
    }


def test_normalize_editorial_brief_payload_coerces_lists() -> None:
    payload = normalize_editorial_brief_payload(
        {
            "proposedTitle": "Titolo",
            "secondaryKeywords": "uno\ndue",
            "h2H3Structure": ["H2: A"],
        }
    )
    assert payload.proposed_title == "Titolo"
    assert payload.secondary_keywords == ["uno", "due"]
    assert payload.h2_h3_structure == ["H2: A"]


def test_normalize_editorial_brief_payload_editorial_fields() -> None:
    payload = normalize_editorial_brief_payload(
        {
            "proposedTitle": "Titolo",
            "authorSuggestion": "Davide",
            "authorReason": "Contenuto su produzione",
            "contentLengthProfile": "medio",
            "communityCtaSuggestion": "Commenta sotto",
            "editorialToneNotes": ["Concreto", "Morbido"],
        }
    )
    assert payload.author_suggestion == "Davide"
    assert payload.author_reason == "Contenuto su produzione"
    assert payload.content_length_profile == "medio"
    assert payload.community_cta_suggestion == "Commenta sotto"
    assert payload.editorial_tone_notes == ["Concreto", "Morbido"]


def test_normalize_editorial_brief_payload_invalid_author_cleared() -> None:
    payload = normalize_editorial_brief_payload(
        {"proposedTitle": "Titolo", "authorSuggestion": "Mario Rossi"}
    )
    assert payload.author_suggestion == ""


def test_build_bi_warnings_when_sections_missing() -> None:
    bundle = SimpleNamespace(
        brand_identity=None,
        safe_claims=None,
        product_knowledge=None,
        faq_objections=None,
        editorial_guidelines=None,
    )
    warnings = build_bi_warnings(bundle)
    assert "Brand Identity mancante" in warnings
    assert "Safe Claims mancanti" in warnings
    assert "Product Knowledge mancante" in warnings
    assert "FAQ & Objections mancanti" in warnings
    assert "Editorial Guidelines mancanti" in warnings


def test_generate_editorial_brief_no_openai_key() -> None:
    project_id = uuid4()
    item_id = uuid4()
    mock_session = AsyncMock()

    async def run() -> None:
        with patch(
            "app.services.content.editorial_brief_service.is_openai_configured",
            return_value=False,
        ):
            with pytest.raises(HTTPException) as exc:
                await generate_editorial_brief(mock_session, project_id, item_id)
            assert exc.value.status_code == 503
            assert "OPENAI_API_KEY" in str(exc.value.detail)

    asyncio.run(run())


def test_generate_editorial_brief_success() -> None:
    project_id = uuid4()
    item_id = uuid4()
    row = SimpleNamespace(
        id=item_id,
        project_id=project_id,
        title="Idea blog",
        content_type="educational_article",
        planned_date=date(2026, 6, 15),
        objective="seo_traffic",
        commercial_intensity="balanced",
        primary_keyword="olio",
        secondary_keywords=["evo"],
        linked_shopify_product_id=None,
        linked_shopify_product_title=None,
        notes=None,
        brief_payload=None,
        status="idea",
    )
    bundle = SimpleNamespace(
        profile=SimpleNamespace(brand_name="Brand"),
        brand_identity=None,
        safe_claims=None,
        product_knowledge=None,
        faq_objections=None,
        prompt_context=None,
    )
    mock_session = AsyncMock()

    async def run() -> None:
        with (
            patch(
                "app.services.content.editorial_brief_service.is_openai_configured",
                return_value=True,
            ),
            patch(
                "app.services.content.editorial_brief_service.get_editorial_item",
                new=AsyncMock(return_value=row),
            ),
            patch(
                "app.services.content.editorial_brief_service.BrandIntelligenceContextBuilder.build_brand_context",
                new=AsyncMock(return_value=bundle),
            ),
            patch(
                "app.services.content.editorial_brief_service.BrandIntelligenceContextBuilder.format_for_prompt",
                return_value="BRAND CONTEXT",
            ),
            patch(
                "app.services.content.editorial_brief_service.load_seo_skill_context",
                return_value=SimpleNamespace(content_brief_rules="RULES"),
            ),
            patch(
                "app.services.content.editorial_brief_service.generate_structured_json",
                new=AsyncMock(return_value=_sample_ai_brief()),
            ),
            patch(
                "app.services.content.editorial_brief_service.build_bi_warnings",
                return_value=["Safe Claims mancanti"],
            ),
            patch(
                "app.services.content.editorial_brief_service.build_brand_context_used",
                return_value=["Brand Profile"],
            ),
        ):
            result = await generate_editorial_brief(mock_session, project_id, item_id)
            assert result.status == "brief_pending"
            assert result.brief_payload is not None
            assert result.brief_payload["proposedTitle"] == "Guida olio EVO"
            assert "Safe Claims mancanti" in result.brief_payload["warnings"]
            mock_session.commit.assert_awaited_once()

    asyncio.run(run())


def test_generate_editorial_brief_ai_failure_no_commit() -> None:
    project_id = uuid4()
    item_id = uuid4()
    row = SimpleNamespace(
        id=item_id,
        project_id=project_id,
        title="Idea",
        content_type="recipe",
        planned_date=date(2026, 6, 1),
        objective=None,
        commercial_intensity=None,
        primary_keyword=None,
        secondary_keywords=None,
        linked_shopify_product_id=None,
        linked_shopify_product_title=None,
        notes=None,
        brief_payload={"existing": True},
        status="idea",
    )
    bundle = SimpleNamespace(
        brand_identity=None,
        safe_claims=None,
        product_knowledge=None,
        faq_objections=None,
        profile=None,
        prompt_context=None,
    )
    mock_session = AsyncMock()

    async def run() -> None:
        with (
            patch(
                "app.services.content.editorial_brief_service.is_openai_configured",
                return_value=True,
            ),
            patch(
                "app.services.content.editorial_brief_service.get_editorial_item",
                new=AsyncMock(return_value=row),
            ),
            patch(
                "app.services.content.editorial_brief_service.BrandIntelligenceContextBuilder.build_brand_context",
                new=AsyncMock(return_value=bundle),
            ),
            patch(
                "app.services.content.editorial_brief_service.BrandIntelligenceContextBuilder.format_for_prompt",
                return_value=None,
            ),
            patch(
                "app.services.content.editorial_brief_service.load_seo_skill_context",
                return_value=SimpleNamespace(content_brief_rules="RULES"),
            ),
            patch(
                "app.services.content.editorial_brief_service.generate_structured_json",
                new=AsyncMock(side_effect=OpenAIRequestError("timeout")),
            ),
        ):
            with pytest.raises(HTTPException) as exc:
                await generate_editorial_brief(mock_session, project_id, item_id)
            assert exc.value.status_code == 502
            mock_session.commit.assert_not_called()
            assert row.brief_payload == {"existing": True}

    asyncio.run(run())


def test_update_editorial_brief_approve() -> None:
    project_id = uuid4()
    item_id = uuid4()
    row = SimpleNamespace(
        id=item_id,
        project_id=project_id,
        brief_payload=None,
        status="brief_pending",
    )
    mock_session = AsyncMock()
    request = EditorialBriefUpdateRequest.model_validate(
        {
            "briefPayload": _sample_ai_brief(),
            "status": "brief_approved",
        }
    )

    async def run() -> None:
        with patch(
            "app.services.content.editorial_brief_service.get_editorial_item",
            new=AsyncMock(return_value=row),
        ):
            result = await update_editorial_brief(mock_session, project_id, item_id, request)
            assert result.status == "brief_approved"
            assert result.brief_payload["proposedTitle"] == "Guida olio EVO"
            mock_session.commit.assert_awaited_once()

    asyncio.run(run())


def test_editorial_brief_update_rejects_published_status() -> None:
    with pytest.raises(ValidationError):
        EditorialBriefUpdateRequest.model_validate(
            {
                "briefPayload": _sample_ai_brief(),
                "status": "published",
            }
        )
