"""Tests for Growth Audit page-level AI/GEO/CRO analysis."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.models.growth_audit import GrowthAuditEvent, GrowthAuditPage, GrowthAuditPageResult, GrowthAuditRun
from app.schemas.growth_audit import GrowthAuditPageAiAnalysisRequest
from app.services.growth_audit.exceptions import GrowthAuditValidationError
from app.services.growth_audit.page_ai_analysis import (
    AI_RESULT_TYPE,
    analyze_growth_audit_page_with_ai,
    list_growth_audit_page_results,
)
from app.services.growth_audit.page_ai_prompts import build_system_prompt


def _mock_ai_output() -> dict:
    return {
        "score": 72,
        "seoScore": 70,
        "geoScore": 65,
        "croScore": 68,
        "adsReadinessScore": 60,
        "summary": "Pagina prodotto solida ma migliorabile su trust e GEO citability.",
        "pageType": "product",
        "findings": [
            {
                "category": "geo",
                "severity": "medium",
                "priority": "medium",
                "title": "Citabilità AI limitata",
                "description": "Mancano FAQ strutturate.",
                "evidence": "Nessuna sezione FAQ nel contenuto.",
                "recommendation": "Aggiungi FAQ con risposte dirette.",
                "howToValidate": "Verifica presenza FAQ nel sorgente.",
                "impact": "medium",
                "effort": "low",
            }
        ],
        "tasks": [
            {
                "title": "Aggiungi FAQ prodotto",
                "description": "3-5 domande frequenti con risposte concise.",
                "ownerType": "content",
                "priority": "medium",
                "estimatedEffort": "low",
            }
        ],
        "recommendations": [],
        "artifacts": {
            "shopifyEditHints": ["Rafforza meta description con benefit chiave"],
            "croChecklist": ["Verifica CTA above the fold"],
            "geoChecklist": ["Aggiungi definizioni chiare del prodotto"],
            "adsReadinessNotes": ["Allinea headline con intent commerciale"],
        },
    }


def _build_completed_run(project_id, run_id=None) -> GrowthAuditRun:
    run_id = run_id or uuid4()
    now = datetime.now(UTC)
    return GrowthAuditRun(
        id=run_id,
        project_id=project_id,
        root_url="https://example.com",
        normalized_domain="example.com",
        status="completed",
        phase="completed",
        audit_mode="full_site_mvp",
        provider="openai",
        progress_percent=100,
        pages_discovered=2,
        pages_classified=2,
        pages_analyzed=2,
        pages_failed=0,
        site_score=70,
        summary={"pagesAnalyzed": 2},
        config={"includeAiAnalysis": False},
        created_at=now,
        updated_at=now,
    )


def _build_analyzed_page(*, project_id, run_id, page_id=None, page_type: str = "product") -> GrowthAuditPage:
    page_id = page_id or uuid4()
    now = datetime.now(UTC)
    return GrowthAuditPage(
        id=page_id,
        run_id=run_id,
        project_id=project_id,
        url="https://example.com/products/a",
        normalized_url="https://example.com/products/a",
        path="/products/a",
        page_type=page_type,
        source="shopify_product",
        status="analyzed",
        priority="normal",
        title="Miele biologico",
        score=82,
        http_status=200,
        page_metadata={"technical": {"schemaTypes": ["Product"]}},
        created_at=now,
        updated_at=now,
    )


def _build_technical_result(*, project_id, run_id, page_id) -> GrowthAuditPageResult:
    now = datetime.now(UTC)
    return GrowthAuditPageResult(
        id=uuid4(),
        run_id=run_id,
        page_id=page_id,
        project_id=project_id,
        result_type="technical",
        status="completed",
        score=82,
        summary="Technical score 82.",
        findings=[],
        tasks=[],
        created_at=now,
        updated_at=now,
    )


def test_analyze_ai_rejects_active_run() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        page_id = uuid4()
        audit_run = _build_completed_run(project_id, run_id)
        audit_run.status = "analyzing"

        session = AsyncMock()
        with patch(
            "app.services.growth_audit.page_ai_analysis.get_growth_audit_run",
            new=AsyncMock(return_value=audit_run),
        ):
            with pytest.raises(GrowthAuditValidationError, match="ancora in corso"):
                await analyze_growth_audit_page_with_ai(
                    session,
                    project_id=project_id,
                    run_id=run_id,
                    page_id=page_id,
                )

    asyncio.run(run())


def test_analyze_ai_happy_path() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        page_id = uuid4()
        audit_run = _build_completed_run(project_id, run_id)
        page = _build_analyzed_page(project_id=project_id, run_id=run_id, page_id=page_id)
        technical = _build_technical_result(
            project_id=project_id,
            run_id=run_id,
            page_id=page_id,
        )

        session = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        events: list[str] = []

        async def track_event(session_arg, **kwargs):
            events.append(kwargs["event_type"])
            return GrowthAuditEvent(
                id=uuid4(),
                run_id=run_id,
                project_id=project_id,
                event_type=kwargs["event_type"],
                message=kwargs["message"],
            )

        with (
            patch(
                "app.services.growth_audit.page_ai_analysis.get_growth_audit_run",
                new=AsyncMock(return_value=audit_run),
            ),
            patch(
                "app.services.growth_audit.page_ai_analysis._get_growth_audit_page",
                new=AsyncMock(return_value=page),
            ),
            patch(
                "app.services.growth_audit.page_ai_analysis._load_latest_technical_result",
                new=AsyncMock(return_value=technical),
            ),
            patch(
                "app.services.growth_audit.page_ai_analysis._build_page_analysis_context",
                new=AsyncMock(return_value={"url": page.url, "pageType": "product"}),
            ),
            patch(
                "app.services.growth_audit.page_ai_analysis.generate_structured_json_with_provider",
                new=AsyncMock(return_value=_mock_ai_output()),
            ),
            patch(
                "app.services.growth_audit.page_ai_analysis._update_run_summary_after_ai_analysis",
                new=AsyncMock(),
            ),
            patch(
                "app.services.growth_audit.page_ai_analysis._count_open_findings_and_tasks",
                new=AsyncMock(return_value=(2, 1)),
            ),
            patch(
                "app.services.growth_audit.page_ai_analysis.create_growth_audit_event",
                new=AsyncMock(side_effect=track_event),
            ),
        ):
            result_run, result_page, result, findings_count, tasks_count = (
                await analyze_growth_audit_page_with_ai(
                    session,
                    project_id=project_id,
                    run_id=run_id,
                    page_id=page_id,
                )
            )

        assert result.result_type == AI_RESULT_TYPE
        assert result.status == "completed"
        assert result.score == 72
        assert result_page.geo_score == 65
        assert result_page.cro_score == 68
        assert result_page.score == 82
        assert result_page.page_metadata["ai"]["latestScore"] == 72
        assert findings_count == 2
        assert tasks_count == 1
        assert "page_ai_analysis_started" in events
        assert "page_ai_analysis_completed" in events
        assert session.add.call_count >= 3

    asyncio.run(run())


def test_product_prompt_contains_ecommerce_keywords() -> None:
    prompt = build_system_prompt(
        "product",
        include_seo=True,
        include_geo=True,
        include_cro=True,
        include_ads_readiness=True,
        depth="standard",
    )
    assert "ecommerce" in prompt.lower() or "prodotto" in prompt.lower()
    assert "Product" in prompt or "schema" in prompt.lower()
    assert "CRO" in prompt
    assert "trust" in prompt.lower()


def test_blog_prompt_contains_eeat_geo() -> None:
    prompt = build_system_prompt(
        "blog_article",
        include_seo=True,
        include_geo=True,
        include_cro=False,
        include_ads_readiness=False,
        depth="standard",
    )
    assert "E-E-A-T" in prompt or "search intent" in prompt.lower()
    assert "GEO" in prompt
    assert "linking" in prompt.lower()


def test_provider_error_creates_failed_result() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        page_id = uuid4()
        audit_run = _build_completed_run(project_id, run_id)
        page = _build_analyzed_page(project_id=project_id, run_id=run_id, page_id=page_id)
        technical = _build_technical_result(
            project_id=project_id,
            run_id=run_id,
            page_id=page_id,
        )

        session = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.commit = AsyncMock()

        events: list[str] = []

        async def track_event(session_arg, **kwargs):
            events.append(kwargs["event_type"])
            return GrowthAuditEvent(
                id=uuid4(),
                run_id=run_id,
                project_id=project_id,
                event_type=kwargs["event_type"],
                message=kwargs["message"],
            )

        with (
            patch(
                "app.services.growth_audit.page_ai_analysis.get_growth_audit_run",
                new=AsyncMock(return_value=audit_run),
            ),
            patch(
                "app.services.growth_audit.page_ai_analysis._get_growth_audit_page",
                new=AsyncMock(return_value=page),
            ),
            patch(
                "app.services.growth_audit.page_ai_analysis._load_latest_technical_result",
                new=AsyncMock(return_value=technical),
            ),
            patch(
                "app.services.growth_audit.page_ai_analysis._build_page_analysis_context",
                new=AsyncMock(return_value={"url": page.url}),
            ),
            patch(
                "app.services.growth_audit.page_ai_analysis.generate_structured_json_with_provider",
                new=AsyncMock(side_effect=ValueError("OpenAI provider is not configured")),
            ),
            patch(
                "app.services.growth_audit.page_ai_analysis.create_growth_audit_event",
                new=AsyncMock(side_effect=track_event),
            ),
        ):
            with pytest.raises(GrowthAuditValidationError, match="non configurato"):
                await analyze_growth_audit_page_with_ai(
                    session,
                    project_id=project_id,
                    run_id=run_id,
                    page_id=page_id,
                )

        assert "page_ai_analysis_started" in events
        assert "page_ai_analysis_failed" in events
        assert session.commit.await_count >= 1

    asyncio.run(run())


def test_invalid_schema_error_returns_readable_message() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        page_id = uuid4()
        audit_run = _build_completed_run(project_id, run_id)
        page = _build_analyzed_page(project_id=project_id, run_id=run_id, page_id=page_id)
        technical = _build_technical_result(
            project_id=project_id,
            run_id=run_id,
            page_id=page_id,
        )

        session = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.commit = AsyncMock()

        events: list[str] = []
        added_results: list[GrowthAuditPageResult] = []

        def track_add(obj):
            if isinstance(obj, GrowthAuditPageResult):
                added_results.append(obj)

        session.add.side_effect = track_add

        async def track_event(session_arg, **kwargs):
            events.append(kwargs["event_type"])
            return GrowthAuditEvent(
                id=uuid4(),
                run_id=run_id,
                project_id=project_id,
                event_type=kwargs["event_type"],
                message=kwargs["message"],
            )

        openai_error = (
            "Invalid schema for response_format 'growth_audit_page_ai_output': "
            "In context=('properties', 'artifacts'), 'required' is required..."
        )

        with (
            patch(
                "app.services.growth_audit.page_ai_analysis.get_growth_audit_run",
                new=AsyncMock(return_value=audit_run),
            ),
            patch(
                "app.services.growth_audit.page_ai_analysis._get_growth_audit_page",
                new=AsyncMock(return_value=page),
            ),
            patch(
                "app.services.growth_audit.page_ai_analysis._load_latest_technical_result",
                new=AsyncMock(return_value=technical),
            ),
            patch(
                "app.services.growth_audit.page_ai_analysis._build_page_analysis_context",
                new=AsyncMock(return_value={"url": page.url}),
            ),
            patch(
                "app.services.growth_audit.page_ai_analysis.generate_structured_json_with_provider",
                new=AsyncMock(side_effect=ValueError(openai_error)),
            ),
            patch(
                "app.services.growth_audit.page_ai_analysis.create_growth_audit_event",
                new=AsyncMock(side_effect=track_event),
            ),
        ):
            with pytest.raises(GrowthAuditValidationError) as exc_info:
                await analyze_growth_audit_page_with_ai(
                    session,
                    project_id=project_id,
                    run_id=run_id,
                    page_id=page_id,
                )

        assert exc_info.value.args[0] == (
            "Analisi AI non riuscita: configurazione output non valida. "
            "Riprova dopo l'aggiornamento del sistema."
        )
        assert "Invalid schema for response_format" not in exc_info.value.args[0]
        assert "page_ai_analysis_started" in events
        assert "page_ai_analysis_failed" in events
        assert any(r.status == "failed" for r in added_results)

    asyncio.run(run())


def test_ai_analysis_route_returns_200() -> None:
    from app.api.routes.growth_audit import analyze_growth_audit_page_ai_endpoint

    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        page_id = uuid4()
        audit_run = _build_completed_run(project_id, run_id)
        page = _build_analyzed_page(project_id=project_id, run_id=run_id, page_id=page_id)
        now = datetime.now(UTC)
        page_result = GrowthAuditPageResult(
            id=uuid4(),
            run_id=run_id,
            page_id=page_id,
            project_id=project_id,
            result_type=AI_RESULT_TYPE,
            skill_key="growth_audit_page_ai",
            status="completed",
            score=72,
            summary="Done",
            created_at=now,
            updated_at=now,
        )

        session = AsyncMock()
        with (
            patch(
                "app.api.routes.growth_audit.get_project_in_default_workspace",
                new=AsyncMock(),
            ),
            patch(
                "app.api.routes.growth_audit.analyze_growth_audit_page_with_ai",
                new=AsyncMock(return_value=(audit_run, page, page_result, 2, 1)),
            ),
        ):
            response = await analyze_growth_audit_page_ai_endpoint(
                project_id,
                run_id,
                page_id,
                GrowthAuditPageAiAnalysisRequest.model_validate({"provider": "openai"}),
                session,
            )

        assert response.result.status == "completed"
        assert response.findings_count == 2
        assert response.tasks_count == 1
        assert "Analisi AI completata" in response.message

    asyncio.run(run())


def test_list_page_results_filters_by_type() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        page_id = uuid4()
        now = datetime.now(UTC)
        ai_result = GrowthAuditPageResult(
            id=uuid4(),
            run_id=run_id,
            page_id=page_id,
            project_id=project_id,
            result_type=AI_RESULT_TYPE,
            status="completed",
            score=70,
            created_at=now,
            updated_at=now,
        )

        session = AsyncMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [ai_result]
        mock_result.scalars.return_value = mock_scalars
        session.execute = AsyncMock(return_value=mock_result)

        with patch(
            "app.services.growth_audit.page_ai_analysis._get_growth_audit_page",
            new=AsyncMock(return_value=_build_analyzed_page(
                project_id=project_id,
                run_id=run_id,
                page_id=page_id,
            )),
        ):
            results = await list_growth_audit_page_results(
                session,
                project_id=project_id,
                run_id=run_id,
                page_id=page_id,
                result_type=AI_RESULT_TYPE,
            )

        assert len(results) == 1
        assert results[0].result_type == AI_RESULT_TYPE

    asyncio.run(run())


def test_list_page_results_route() -> None:
    from app.api.routes.growth_audit import list_growth_audit_page_results_endpoint

    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        page_id = uuid4()
        now = datetime.now(UTC)
        page_result = GrowthAuditPageResult(
            id=uuid4(),
            run_id=run_id,
            page_id=page_id,
            project_id=project_id,
            result_type=AI_RESULT_TYPE,
            status="completed",
            score=72,
            created_at=now,
            updated_at=now,
        )

        session = AsyncMock()
        with (
            patch(
                "app.api.routes.growth_audit.get_project_in_default_workspace",
                new=AsyncMock(),
            ),
            patch(
                "app.api.routes.growth_audit.list_growth_audit_page_results",
                new=AsyncMock(return_value=[page_result]),
            ),
        ):
            response = await list_growth_audit_page_results_endpoint(
                project_id,
                run_id,
                page_id,
                AI_RESULT_TYPE,
                session,
            )

        assert len(response.results) == 1
        assert response.results[0].result_type == AI_RESULT_TYPE

    asyncio.run(run())
