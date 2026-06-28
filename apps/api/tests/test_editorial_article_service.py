"""Editorial article generator service tests."""

import asyncio
from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.schemas.content_seo_editorial import (
    EditorialArticleUpdateRequest,
    normalize_editorial_article_payload,
)
from app.services.content.editorial_article_service import (
    ArticleGenerationError,
    generate_editorial_article,
    generate_editorial_article_core,
    update_editorial_article,
)
from app.utils.html_sanitize import sanitize_editorial_article_html


def _sample_ai_article() -> dict:
    return {
        "title": "Guida olio EVO",
        "handle": "guida-olio-evo",
        "excerpt": "Tutto sull'olio extravergine.",
        "bodyHtml": "<h2>Cos'è</h2><p>Testo <strong>utile</strong>.</p><script>alert(1)</script>",
        "bodyMarkdown": "## Cos'è\nTesto utile.",
        "seoTitle": "Olio EVO: guida",
        "metaDescription": "Guida completa.",
        "tags": ["olio", "cucina"],
        "linkedProducts": ["Olio classico"],
        "cta": "Scopri la linea",
        "warnings": [],
    }


def test_sanitize_editorial_article_html_strips_script() -> None:
    raw = "<h2>Titolo</h2><p>Ok</p><script>evil()</script>"
    out = sanitize_editorial_article_html(raw)
    assert "<script" not in out
    assert "<h2>" in out
    assert "<p>" in out


def test_sanitize_editorial_article_html_preserves_gcr_div() -> None:
    raw = (
        '<div class="gcr-article-body">'
        '<div class="gcr-article-note"><strong>Da ricordare:</strong> test</div>'
        "</div>"
    )
    out = sanitize_editorial_article_html(raw)
    assert 'class="gcr-article-body"' in out
    assert "Da ricordare" in out


def test_normalize_editorial_article_payload_skill_fields() -> None:
    raw = {
        **_sample_ai_article(),
        "readabilityChecklist": ["Paragrafi brevi"],
        "skillPackUsed": "gcr-editorial-article",
        "skillPackVersion": "v1",
        "htmlBlocksUsed": ["gcr-article-note"],
    }
    payload = normalize_editorial_article_payload(raw)
    assert payload.skill_pack_used == "gcr-editorial-article"
    assert payload.readability_checklist == ["Paragrafi brevi"]
    assert payload.html_blocks_used == ["gcr-article-note"]


def test_build_article_system_prompt_includes_editorial_skill() -> None:
    from app.services.content.editorial_article_service import _build_article_system_prompt
    from app.services.content.editorial_skill_loader import load_editorial_skill_context

    editorial_skill = load_editorial_skill_context()
    prompt = _build_article_system_prompt(
        None,
        "brand guardrails",
        editorial_skill.as_article_prompt_context(),
    )
    assert "gcr-editorial-article" in prompt
    assert "gcr-article-note" in prompt
    assert "neuromarketing" in prompt.lower() or "Neuromarketing" in prompt


def test_normalize_editorial_article_payload_sanitizes_body() -> None:
    payload = normalize_editorial_article_payload(_sample_ai_article())
    assert payload.title == "Guida olio EVO"
    assert "<script" not in payload.body_html
    assert "<h2>" in payload.body_html
    assert "utile" in payload.body_html


def test_normalize_editorial_article_payload_new_metadata_fields() -> None:
    raw = {
        **_sample_ai_article(),
        "authorName": "A cura di Davide",
        "authorRole": "coordinatore produzione",
        "communityCta": "Scrivici nei commenti",
        "contentLengthProfile": "medio",
    }
    payload = normalize_editorial_article_payload(raw)
    assert payload.author_name == "A cura di Davide"
    assert payload.author_role == "coordinatore produzione"
    assert payload.community_cta == "Scrivici nei commenti"
    assert payload.content_length_profile == "medio"


def test_postprocess_editorial_article_removes_duplicate_intro() -> None:
    from app.schemas.content_seo_editorial import EditorialBriefPayload
    from app.services.content.editorial_article_postprocess import postprocess_editorial_article_html

    brief = EditorialBriefPayload(
        proposed_title="Titolo",
        max_h2=5,
        max_h3=3,
        structure_complexity="snella",
    )
    excerpt = "Il miele cristallizza per un processo naturale legato al contenuto di zuccheri."
    body = (
        "<p>Il miele cristallizza per un processo naturale legato al contenuto di zuccheri.</p>"
        "<h2>Perché succede</h2><p>Dettaglio utile.</p>"
    )
    html, warnings = postprocess_editorial_article_html(body, excerpt, brief)
    assert "Rimossa introduzione duplicata" in warnings[0]
    assert html.startswith("<h2>")


def test_postprocess_editorial_article_reduces_repetitions() -> None:
    from app.schemas.content_seo_editorial import EditorialBriefPayload
    from app.services.content.editorial_article_postprocess import postprocess_editorial_article_html

    brief = EditorialBriefPayload(
        proposed_title="Titolo",
        avoid_repetitions=["cristallizzazione è naturale"],
        max_h2=5,
        max_h3=3,
    )
    body = (
        "<h2>Uno</h2><p>La cristallizzazione è naturale.</p>"
        "<h2>Due</h2><p>Ancora: la cristallizzazione è naturale.</p>"
        "<h2>Tre</h2><p>Di nuovo la cristallizzazione è naturale.</p>"
    )
    _, warnings = postprocess_editorial_article_html(body, "", brief)
    assert any("Ridotte ripetizioni" in w for w in warnings)


def test_enrich_article_payload_reading_time() -> None:
    from app.services.content.editorial_article_service import _enrich_article_payload

    payload = normalize_editorial_article_payload(_sample_ai_article())
    enriched = _enrich_article_payload(payload)
    assert enriched.estimated_reading_time.endswith("min")
    assert enriched.content_length_profile in ("breve", "medio", "approfondito")


def test_apply_brief_author_clears_signature_when_no_suggestion() -> None:
    from app.services.content.editorial_article_service import _apply_brief_author_to_payload

    payload = normalize_editorial_article_payload(
        {
            **_sample_ai_article(),
            "authorName": "A cura di Davide",
            "authorRole": "coordinatore",
        }
    )
    brief = {"proposedTitle": "Titolo", "authorSuggestion": ""}
    result = _apply_brief_author_to_payload(payload, brief, SimpleNamespace())
    assert result.author_name == ""
    assert result.author_role == ""


def test_apply_brief_author_sets_davide_from_suggestion() -> None:
    from app.schemas.brand_editorial_guidelines import BrandPersonEntry
    from app.services.content.editorial_article_service import _apply_brief_author_to_payload

    payload = normalize_editorial_article_payload(_sample_ai_article())
    brief = {
        "proposedTitle": "Titolo",
        "authorSuggestion": "Davide",
        "authorReason": "Produzione e lavorazione",
        "communityCtaSuggestion": "Raccontaci la tua esperienza",
        "contentLengthProfile": "breve",
    }
    eg = SimpleNamespace(
        brand_people=[
            BrandPersonEntry(name="Davide", role="coordinatore della produzione"),
        ]
    )
    bundle = SimpleNamespace(editorial_guidelines=eg)
    result = _apply_brief_author_to_payload(payload, brief, bundle)
    assert result.author_name == "A cura di Davide"
    assert result.author_role == "coordinatore della produzione"
    assert result.community_cta == "Raccontaci la tua esperienza"
    assert result.content_length_profile == "breve"


def test_generate_editorial_article_brief_not_approved() -> None:
    project_id = uuid4()
    item_id = uuid4()
    row = SimpleNamespace(
        id=item_id,
        project_id=project_id,
        status="brief_pending",
        brief_payload={"proposedTitle": "Titolo"},
        linked_shopify_product_id=None,
        linked_shopify_product_title=None,
        content_type="educational_article",
        title="Idea",
        planned_date=date(2026, 6, 15),
        article_payload=None,
    )
    mock_session = AsyncMock()

    async def run() -> None:
        with patch(
            "app.services.content.editorial_article_service.is_openai_configured",
            return_value=True,
        ):
            with patch(
                "app.services.content.editorial_article_service.get_editorial_item",
                new_callable=AsyncMock,
                return_value=row,
            ):
                with pytest.raises(ArticleGenerationError) as exc:
                    await generate_editorial_article_core(mock_session, project_id, item_id)
                assert exc.value.brief_not_approved

    asyncio.run(run())


def test_generate_editorial_article_no_openai() -> None:
    project_id = uuid4()
    item_id = uuid4()

    async def run() -> None:
        mock_session = AsyncMock()
        with patch(
            "app.services.content.editorial_article_service.is_openai_configured",
            return_value=False,
        ):
            with pytest.raises(HTTPException) as exc:
                await generate_editorial_article(mock_session, project_id, item_id)
            assert exc.value.status_code == 503
            assert "OPENAI_API_KEY" in str(exc.value.detail)

    asyncio.run(run())


def test_generate_editorial_article_success() -> None:
    project_id = uuid4()
    item_id = uuid4()
    row = SimpleNamespace(
        id=item_id,
        project_id=project_id,
        status="brief_approved",
        brief_payload={"proposedTitle": "Titolo", "h2H3Structure": ["H2: Intro"]},
        linked_shopify_product_id="gid://shopify/Product/1",
        linked_shopify_product_title="Olio",
        linked_shopify_product_handle="olio-classico",
        content_type="educational_article",
        title="Idea blog",
        planned_date=date(2026, 6, 15),
        article_payload=None,
    )
    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    async def run() -> None:
        with patch(
            "app.services.content.editorial_article_service.is_openai_configured",
            return_value=True,
        ):
            with patch(
                "app.services.content.editorial_article_service.get_editorial_item",
                new_callable=AsyncMock,
                return_value=row,
            ):
                with patch(
                    "app.services.ai.context_profiles.BrandIntelligenceContextBuilder.build_brand_context",
                    new_callable=AsyncMock,
                    return_value=SimpleNamespace(
                        brand_identity=None,
                        safe_claims=None,
                        product_knowledge=None,
                        faq_objections=None,
                        profile=None,
                        prompt_context=None,
                        editorial_guidelines=None,
                    ),
                ):
                    with patch(
                        "app.services.content.editorial_article_service.BrandIntelligenceContextBuilder.build_brand_context",
                        new_callable=AsyncMock,
                        return_value=SimpleNamespace(
                            brand_identity=None,
                            safe_claims=None,
                            product_knowledge=None,
                            faq_objections=None,
                            profile=None,
                            prompt_context=None,
                            editorial_guidelines=None,
                        ),
                    ):
                        with patch(
                            "app.services.content.editorial_article_service.BrandIntelligenceContextBuilder.format_for_prompt",
                            return_value="BRAND CONTEXT",
                        ):
                            with patch(
                                "app.services.content.editorial_article_service.get_product_knowledge_prompt_for_entity",
                                new_callable=AsyncMock,
                                return_value="PK",
                            ):
                                with patch(
                                    "app.services.content.editorial_article_service.load_seo_skill_context",
                                    return_value=SimpleNamespace(brand_guardrails="GUARDRAILS"),
                                ):
                                    with patch(
                                        "app.services.content.editorial_article_service.load_editorial_skill_context",
                                        return_value=SimpleNamespace(
                                            as_article_prompt_context=lambda: "EDITORIAL SKILL",
                                            version="v1.1",
                                        ),
                                    ):
                                        with patch(
                                            "app.services.content.editorial_article_service.fetch_latest_editorial_ai_log",
                                            new_callable=AsyncMock,
                                            return_value=None,
                                        ):
                                            with patch(
                                                "app.services.content.editorial_article_service.build_editorial_link_context",
                                                new_callable=AsyncMock,
                                                return_value=[],
                                            ):
                                                with patch(
                                                    "app.services.content.editorial_article_service.generate_structured_json",
                                                    new_callable=AsyncMock,
                                                    return_value=_sample_ai_article(),
                                                ):
                                                    result = await generate_editorial_article_core(
                                                        mock_session, project_id, item_id
                                                    )
        assert result.status == "draft_review"
        assert result.article_payload is not None
        assert result.article_payload["title"] == "Guida olio EVO"
        assert result.article_payload.get("authorName", "") == ""

    asyncio.run(run())


def test_update_editorial_article_ready_to_publish() -> None:
    project_id = uuid4()
    item_id = uuid4()
    row = SimpleNamespace(
        id=item_id,
        project_id=project_id,
        status="draft_review",
        article_payload=None,
    )
    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    request = EditorialArticleUpdateRequest(
        article_payload=_sample_ai_article(),
        status="ready_to_publish",
    )

    async def run() -> None:
        with patch(
            "app.services.content.editorial_article_service.get_editorial_item",
            new_callable=AsyncMock,
            return_value=row,
        ):
            result = await update_editorial_article(
                mock_session, project_id, item_id, request
            )
        assert result.status == "ready_to_publish"
        assert result.article_payload is not None

    asyncio.run(run())
