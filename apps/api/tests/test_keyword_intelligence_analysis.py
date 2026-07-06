"""Tests for Keyword Intelligence analysis."""

from __future__ import annotations

import asyncio
import os
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

from app.api.routes.growth_audit import analyze_growth_audit_page_keyword_intelligence_endpoint
from app.core.config import settings
from app.models.growth_audit import GrowthAuditPage, GrowthAuditRun
from app.schemas.growth_audit import GrowthAuditKeywordIntelligenceAnalysisRequest
from app.services.dataforseo.exceptions import DataForSeoRealCallsDisabledError
from app.services.growth_audit.keyword_intelligence_analysis import (
    analyze_growth_audit_page_keyword_intelligence,
)
from app.services.growth_audit.keyword_intelligence_competitors import build_competitor_summary
from app.services.growth_audit.keyword_intelligence_findings import (
    build_keyword_intelligence_findings,
)
from app.services.growth_audit.keyword_intelligence_selection import (
    select_keyword_intelligence_seed_queries,
)


def _build_run(project_id, run_id=None) -> GrowthAuditRun:
    run_id = run_id or uuid4()
    now = datetime.now(UTC)
    return GrowthAuditRun(
        id=run_id,
        project_id=project_id,
        root_url="https://solmielato.it",
        normalized_domain="solmielato.it",
        status="completed",
        phase="completed",
        audit_mode="full_site_mvp",
        provider="openai",
        progress_percent=100,
        summary={},
        created_at=now,
        updated_at=now,
    )


def _build_product_page(*, project_id, run_id, page_id=None, metadata=None) -> GrowthAuditPage:
    page_id = page_id or uuid4()
    now = datetime.now(UTC)
    return GrowthAuditPage(
        id=page_id,
        run_id=run_id,
        project_id=project_id,
        url="https://solmielato.it/products/polline",
        normalized_url="https://solmielato.it/products/polline",
        page_type="product",
        source_entity_type="shopify_product",
        source="shopify_product",
        status="analyzed",
        title="Polline biologico",
        source_entity_title="Polline biologico",
        page_metadata=metadata or {},
        created_at=now,
        updated_at=now,
    )


def test_select_seed_queries_orders_by_score() -> None:
    page = _build_product_page(project_id=uuid4(), run_id=uuid4())
    gsc = {
        "topQueries": [
            {
                "query": "miele",
                "clicks": 1,
                "impressions": 50,
                "ctr": 0.02,
                "position": 20,
            },
            {
                "query": "polline biologico",
                "clicks": 10,
                "impressions": 477,
                "ctr": 0.0021,
                "position": 9,
            },
        ]
    }
    selected = select_keyword_intelligence_seed_queries(gsc, page, max_seed_queries=5)
    assert selected[0]["query"] == "polline biologico"
    assert selected[0]["selected"] is True


def test_fallback_title_without_gsc() -> None:
    page = _build_product_page(project_id=uuid4(), run_id=uuid4())
    selected = select_keyword_intelligence_seed_queries(None, page, max_seed_queries=3)
    assert len(selected) == 1
    assert selected[0]["selectionReason"] == "fallback_page_title"
    assert selected[0]["query"] == "Polline biologico"


def test_competitor_summary_aggregates_domains() -> None:
    summary = build_competitor_summary(
        [
            {
                "keyword": "polline biologico",
                "topResults": [
                    {
                        "domain": "example.it",
                        "position": 1,
                        "url": "https://example.it/a",
                        "title": "A",
                    },
                    {
                        "domain": "other.it",
                        "position": 3,
                        "url": "https://other.it/b",
                        "title": "B",
                    },
                ],
            },
            {
                "keyword": "polline bio",
                "topResults": [
                    {
                        "domain": "example.it",
                        "position": 2,
                        "url": "https://example.it/c",
                        "title": "C",
                    }
                ],
            },
        ]
    )
    assert summary[0]["domain"] == "example.it"
    assert summary[0]["appearancesCount"] == 2
    assert summary[0]["bestPosition"] == 1


def test_findings_max_five() -> None:
    findings, tasks = build_keyword_intelligence_findings(
        seed_queries=[
            {
                "query": "polline biologico",
                "impressions": 500,
                "ctr": 0.005,
            }
        ],
        search_volume=[{"keyword": "polline biologico", "searchVolume": 140}],
        serp_results=[
            {
                "keyword": "polline biologico",
                "refinementChips": ["Benefici", "Come assumerlo"],
                "topResults": [],
            }
        ],
        competitors=[
            {
                "domain": "example.it",
                "appearancesCount": 3,
                "bestPosition": 1,
                "keywords": ["polline biologico"],
            }
        ],
    )
    assert len(findings) <= 5
    assert len(tasks) == len(findings)


def test_endpoint_blocks_real_calls_disabled() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        page_id = uuid4()
        session = AsyncMock()
        request = GrowthAuditKeywordIntelligenceAnalysisRequest.model_validate(
            {"maxSeedQueries": 5, "force": True}
        )
        with patch(
            "app.api.routes.growth_audit.get_project_in_default_workspace",
            new=AsyncMock(),
        ), patch(
            "app.api.routes.growth_audit.analyze_growth_audit_page_keyword_intelligence",
            new=AsyncMock(
                side_effect=DataForSeoRealCallsDisabledError("DataForSEO real calls disabled.")
            ),
        ):
            with pytest.raises(HTTPException) as exc:
                await analyze_growth_audit_page_keyword_intelligence_endpoint(
                    project_id,
                    run_id,
                    page_id,
                    request,
                    session,
                )
        assert exc.value.status_code == 409

    asyncio.run(run())


def test_force_false_returns_cached_metadata() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        page_id = uuid4()
        synced_at = datetime.now(UTC).isoformat()
        existing = {
            "syncedAt": synced_at,
            "searchVolume": [{"keyword": "polline biologico", "searchVolume": 140}],
            "competitors": [],
            "cost": {"totalUsd": 0.09},
        }
        audit_run = _build_run(project_id, run_id)
        page = _build_product_page(
            project_id=project_id,
            run_id=run_id,
            page_id=page_id,
            metadata={"keywordIntelligence": existing},
        )

        session = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        with (
            patch(
                "app.services.growth_audit.keyword_intelligence_analysis.get_growth_audit_run",
                new=AsyncMock(return_value=audit_run),
            ),
            patch(
                "app.services.growth_audit.keyword_intelligence_analysis._get_growth_audit_page",
                new=AsyncMock(return_value=page),
            ),
            patch(
                "app.services.growth_audit.keyword_intelligence_analysis.safe_test_keyword_search_volume_batch",
                new=AsyncMock(),
            ) as sv_mock,
            patch(
                "app.services.growth_audit.keyword_intelligence_analysis._count_open_findings_and_tasks",
                new=AsyncMock(return_value=(0, 0)),
            ),
        ):
            _, _, summary, cached, _, _ = await analyze_growth_audit_page_keyword_intelligence(
                session,
                project_id=project_id,
                run_id=run_id,
                page_id=page_id,
                force=False,
            )

        assert cached is True
        assert summary["syncedAt"] == synced_at
        sv_mock.assert_not_called()

    asyncio.run(run())


def test_analysis_updates_metadata_and_calls_dfs() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        page_id = uuid4()
        audit_run = _build_run(project_id, run_id)
        page = _build_product_page(
            project_id=project_id,
            run_id=run_id,
            page_id=page_id,
            metadata={
                "searchConsole": {
                    "topQueries": [
                        {
                            "query": "polline biologico",
                            "clicks": 10,
                            "impressions": 477,
                            "ctr": 0.0021,
                            "position": 9,
                        }
                    ]
                }
            },
        )

        session = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        settings.dataforseo_login = "login"
        settings.dataforseo_password = "password"
        settings.dataforseo_enable_real_calls = True

        sv_result = {
            "cost_usd": 0.09,
            "summary": {
                "results": [
                    {
                        "keyword": "polline biologico",
                        "searchVolume": 140,
                        "cpc": 0.29,
                        "competition": "HIGH",
                    }
                ]
            },
        }
        ideas_result = {
            "cost_usd": 0.09,
            "summary": {
                "seedKeyword": "polline biologico",
                "ideasCount": 1,
                "items": [{"keyword": "polline biologico italiano", "searchVolume": 30}],
            },
        }
        serp_result = {
            "cost_usd": 0.002,
            "summary": {
                "keyword": "polline biologico",
                "topResults": [
                    {
                        "position": 1,
                        "domain": "example.it",
                        "title": "Polline",
                        "url": "https://example.it",
                    }
                ],
                "refinementChips": ["Benefici"],
            },
        }

        with (
            patch(
                "app.services.growth_audit.keyword_intelligence_analysis.get_growth_audit_run",
                new=AsyncMock(return_value=audit_run),
            ),
            patch(
                "app.services.growth_audit.keyword_intelligence_analysis._get_growth_audit_page",
                new=AsyncMock(return_value=page),
            ),
            patch(
                "app.services.growth_audit.keyword_intelligence_analysis.assert_dataforseo_budget_allows",
                new=AsyncMock(),
            ),
            patch(
                "app.services.growth_audit.keyword_intelligence_analysis.estimate_keyword_intelligence_cost",
                new=AsyncMock(return_value=0.2),
            ),
            patch(
                "app.services.growth_audit.keyword_intelligence_analysis.create_growth_audit_event",
                new=AsyncMock(),
            ),
            patch(
                "app.services.growth_audit.keyword_intelligence_analysis.safe_test_keyword_search_volume_batch",
                new=AsyncMock(return_value=sv_result),
            ) as sv_mock,
            patch(
                "app.services.growth_audit.keyword_intelligence_analysis.safe_test_keyword_ideas",
                new=AsyncMock(return_value=ideas_result),
            ) as ideas_mock,
            patch(
                "app.services.growth_audit.keyword_intelligence_analysis.safe_test_serp",
                new=AsyncMock(return_value=serp_result),
            ) as serp_mock,
            patch(
                "app.services.growth_audit.keyword_intelligence_analysis.record_dataforseo_call",
                new=AsyncMock(side_effect=[0.09, 0.09, 0.002]),
            ),
            patch(
                "app.services.growth_audit.keyword_intelligence_analysis._count_open_findings_and_tasks",
                new=AsyncMock(return_value=(1, 1)),
            ),
        ):
            run_obj, page_obj, summary, cached, _, _ = (
                await analyze_growth_audit_page_keyword_intelligence(
                    session,
                    project_id=project_id,
                    run_id=run_id,
                    page_id=page_id,
                    max_seed_queries=10,
                    keyword_ideas_seeds=1,
                    serp_keywords=1,
                    force=True,
                )
            )

        assert cached is False
        assert summary["searchVolume"][0]["searchVolume"] == 140
        assert page_obj.page_metadata["keywordIntelligence"]["cost"]["totalUsd"] > 0
        assert run_obj.summary["keywordIntelligence"]["pagesAnalyzed"] == 1
        sv_mock.assert_awaited_once()
        ideas_mock.assert_awaited_once()
        serp_mock.assert_awaited_once()

    asyncio.run(run())


def test_stale_cache_triggers_refresh() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        page_id = uuid4()
        stale_sync = (datetime.now(UTC) - timedelta(days=10)).isoformat()
        page = _build_product_page(
            project_id=project_id,
            run_id=run_id,
            page_id=page_id,
            metadata={
                "keywordIntelligence": {"syncedAt": stale_sync, "competitors": [], "cost": {}},
                "searchConsole": {
                    "topQueries": [
                        {"query": "polline biologico", "impressions": 100, "ctr": 0.01, "position": 8}
                    ]
                },
            },
        )
        audit_run = _build_run(project_id, run_id)
        session = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        settings.dataforseo_enable_real_calls = True

        with (
            patch(
                "app.services.growth_audit.keyword_intelligence_analysis.get_growth_audit_run",
                new=AsyncMock(return_value=audit_run),
            ),
            patch(
                "app.services.growth_audit.keyword_intelligence_analysis._get_growth_audit_page",
                new=AsyncMock(return_value=page),
            ),
            patch(
                "app.services.growth_audit.keyword_intelligence_analysis.assert_dataforseo_budget_allows",
                new=AsyncMock(),
            ),
            patch(
                "app.services.growth_audit.keyword_intelligence_analysis.estimate_keyword_intelligence_cost",
                new=AsyncMock(return_value=0.2),
            ),
            patch(
                "app.services.growth_audit.keyword_intelligence_analysis.create_growth_audit_event",
                new=AsyncMock(),
            ),
            patch(
                "app.services.growth_audit.keyword_intelligence_analysis.safe_test_keyword_search_volume_batch",
                new=AsyncMock(
                    return_value={
                        "cost_usd": 0.09,
                        "summary": {"results": [{"keyword": "polline biologico", "searchVolume": 10}]},
                    }
                ),
            ) as sv_mock,
            patch(
                "app.services.growth_audit.keyword_intelligence_analysis.safe_test_keyword_ideas",
                new=AsyncMock(return_value={"cost_usd": 0.09, "summary": {"items": []}}),
            ),
            patch(
                "app.services.growth_audit.keyword_intelligence_analysis.safe_test_serp",
                new=AsyncMock(return_value={"cost_usd": 0.002, "summary": {"topResults": []}}),
            ),
            patch(
                "app.services.growth_audit.keyword_intelligence_analysis.record_dataforseo_call",
                new=AsyncMock(return_value=0.09),
            ),
            patch(
                "app.services.growth_audit.keyword_intelligence_analysis._count_open_findings_and_tasks",
                new=AsyncMock(return_value=(0, 0)),
            ),
        ):
            await analyze_growth_audit_page_keyword_intelligence(
                session,
                project_id=project_id,
                run_id=run_id,
                page_id=page_id,
                serp_keywords=0,
                keyword_ideas_seeds=0,
                force=False,
            )

        sv_mock.assert_awaited_once()

    asyncio.run(run())
