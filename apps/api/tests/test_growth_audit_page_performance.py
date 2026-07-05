"""Tests for Growth Audit page performance analysis."""

from __future__ import annotations

import asyncio
import os
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

from app.api.routes.growth_audit import analyze_growth_audit_page_performance_endpoint
from app.models.growth_audit import GrowthAuditEvent, GrowthAuditPage, GrowthAuditPageResult, GrowthAuditRun
from app.schemas.growth_audit import GrowthAuditPagePerformanceAnalysisRequest
from app.services.google.exceptions import GoogleApiRequestError, GoogleIntegrationNotConfiguredError
from app.services.growth_audit.exceptions import GrowthAuditValidationError
from app.services.growth_audit.page_performance_analysis import (
    PERFORMANCE_RESULT_TYPE,
    analyze_growth_audit_page_performance,
)
from app.services.growth_audit.performance_analysis import normalize_pagespeed_result


def _pagespeed_raw() -> dict:
    return {
        "lighthouseResult": {
            "categories": {
                "performance": {"score": 0.72},
                "accessibility": {"score": 0.9},
                "best-practices": {"score": 0.85},
                "seo": {"score": 0.88},
            },
            "audits": {
                "largest-contentful-paint": {
                    "numericValue": 2800,
                    "score": 0.7,
                    "title": "LCP",
                },
                "cumulative-layout-shift": {
                    "numericValue": 0.08,
                    "score": 0.9,
                    "title": "CLS",
                },
                "total-blocking-time": {
                    "numericValue": 250,
                    "score": 0.85,
                    "title": "TBT",
                },
            },
        }
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
        pages_discovered=1,
        pages_classified=1,
        pages_analyzed=1,
        pages_failed=0,
        site_score=70,
        summary={"pagesAnalyzed": 1},
        config={"includeAiAnalysis": False},
        created_at=now,
        updated_at=now,
    )


def _build_page(*, project_id, run_id, page_id=None) -> GrowthAuditPage:
    page_id = page_id or uuid4()
    now = datetime.now(UTC)
    return GrowthAuditPage(
        id=page_id,
        run_id=run_id,
        project_id=project_id,
        url="https://example.com/products/a",
        normalized_url="https://example.com/products/a",
        path="/products/a",
        page_type="product",
        source="shopify_product",
        status="analyzed",
        priority="normal",
        title="Prodotto A",
        score=82,
        http_status=200,
        created_at=now,
        updated_at=now,
    )


def test_analyze_performance_creates_completed_result() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        page_id = uuid4()
        audit_run = _build_completed_run(project_id, run_id)
        page = _build_page(project_id=project_id, run_id=run_id, page_id=page_id)

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
                "app.services.growth_audit.page_performance_analysis.get_growth_audit_run",
                new=AsyncMock(return_value=audit_run),
            ),
            patch(
                "app.services.growth_audit.page_performance_analysis._get_growth_audit_page",
                new=AsyncMock(return_value=page),
            ),
            patch(
                "app.services.growth_audit.page_performance_analysis.is_pagespeed_configured",
                return_value=True,
            ),
            patch(
                "app.services.growth_audit.page_performance_analysis.is_crux_configured",
                return_value=True,
            ),
            patch(
                "app.services.growth_audit.page_performance_analysis.fetch_pagespeed_insights",
                new=AsyncMock(return_value=_pagespeed_raw()),
            ),
            patch(
                "app.services.growth_audit.page_performance_analysis.fetch_crux_record",
                new=AsyncMock(return_value=None),
            ),
            patch(
                "app.services.growth_audit.page_performance_analysis._update_run_summary_after_performance_analysis",
                new=AsyncMock(),
            ),
            patch(
                "app.services.growth_audit.page_performance_analysis._count_open_findings_and_tasks",
                new=AsyncMock(return_value=(1, 1)),
            ),
            patch(
                "app.services.growth_audit.page_performance_analysis.create_growth_audit_event",
                new=AsyncMock(side_effect=track_event),
            ),
        ):
            result_run, result_page, result, findings_count, tasks_count = (
                await analyze_growth_audit_page_performance(
                    session,
                    project_id=project_id,
                    run_id=run_id,
                    page_id=page_id,
                )
            )

        assert result.result_type == PERFORMANCE_RESULT_TYPE
        assert result.status == "completed"
        assert result.score == 72
        assert result_page.performance_score == 72
        assert result_page.page_metadata["performance"]["cruxSource"] == "missing"
        assert "performance_analysis_started" in events
        assert "performance_analysis_completed" in events
        assert findings_count == 1
        assert tasks_count == 1

    asyncio.run(run())


def test_analyze_performance_crux_missing_does_not_fail() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        page_id = uuid4()
        audit_run = _build_completed_run(project_id, run_id)
        page = _build_page(project_id=project_id, run_id=run_id, page_id=page_id)

        session = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        with (
            patch(
                "app.services.growth_audit.page_performance_analysis.get_growth_audit_run",
                new=AsyncMock(return_value=audit_run),
            ),
            patch(
                "app.services.growth_audit.page_performance_analysis._get_growth_audit_page",
                new=AsyncMock(return_value=page),
            ),
            patch(
                "app.services.growth_audit.page_performance_analysis.is_pagespeed_configured",
                return_value=True,
            ),
            patch(
                "app.services.growth_audit.page_performance_analysis.is_crux_configured",
                return_value=False,
            ),
            patch(
                "app.services.growth_audit.page_performance_analysis.fetch_pagespeed_insights",
                new=AsyncMock(return_value=_pagespeed_raw()),
            ),
            patch(
                "app.services.growth_audit.page_performance_analysis._update_run_summary_after_performance_analysis",
                new=AsyncMock(),
            ),
            patch(
                "app.services.growth_audit.page_performance_analysis._count_open_findings_and_tasks",
                new=AsyncMock(return_value=(0, 0)),
            ),
            patch(
                "app.services.growth_audit.page_performance_analysis.create_growth_audit_event",
                new=AsyncMock(return_value=GrowthAuditEvent(id=uuid4(), run_id=run_id, project_id=project_id, event_type="x", message="m")),
            ),
        ):
            _, _, result, _, _ = await analyze_growth_audit_page_performance(
                session,
                project_id=project_id,
                run_id=run_id,
                page_id=page_id,
            )

        assert result.status == "completed"
        assert result.artifacts["crux"]["source"] == "missing"

    asyncio.run(run())


def test_analyze_performance_pagespeed_error_raises() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        page_id = uuid4()
        audit_run = _build_completed_run(project_id, run_id)
        page = _build_page(project_id=project_id, run_id=run_id, page_id=page_id)

        session = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        with (
            patch(
                "app.services.growth_audit.page_performance_analysis.get_growth_audit_run",
                new=AsyncMock(return_value=audit_run),
            ),
            patch(
                "app.services.growth_audit.page_performance_analysis._get_growth_audit_page",
                new=AsyncMock(return_value=page),
            ),
            patch(
                "app.services.growth_audit.page_performance_analysis.is_pagespeed_configured",
                return_value=True,
            ),
            patch(
                "app.services.growth_audit.page_performance_analysis.fetch_pagespeed_insights",
                new=AsyncMock(side_effect=GoogleApiRequestError("PageSpeed failed")),
            ),
            patch(
                "app.services.growth_audit.page_performance_analysis._persist_failed_performance_result",
                new=AsyncMock(return_value=GrowthAuditPageResult(id=uuid4(), run_id=run_id, page_id=page_id, project_id=project_id, result_type="performance", status="failed")),
            ),
            patch(
                "app.services.growth_audit.page_performance_analysis.create_growth_audit_event",
                new=AsyncMock(return_value=GrowthAuditEvent(id=uuid4(), run_id=run_id, project_id=project_id, event_type="x", message="m")),
            ),
            pytest.raises(GoogleApiRequestError),
        ):
            await analyze_growth_audit_page_performance(
                session,
                project_id=project_id,
                run_id=run_id,
                page_id=page_id,
            )

    asyncio.run(run())


def test_performance_route_returns_200_with_mock() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        page_id = uuid4()
        now = datetime.now(UTC)
        audit_run = _build_completed_run(project_id, run_id)
        page = _build_page(project_id=project_id, run_id=run_id, page_id=page_id)
        result = GrowthAuditPageResult(
            id=uuid4(),
            run_id=run_id,
            page_id=page_id,
            project_id=project_id,
            result_type=PERFORMANCE_RESULT_TYPE,
            status="completed",
            score=72,
            summary="Performance score 72.",
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
                "app.api.routes.growth_audit.analyze_growth_audit_page_performance",
                new=AsyncMock(return_value=(audit_run, page, result, 1, 1)),
            ),
        ):
            response = await analyze_growth_audit_page_performance_endpoint(
                project_id,
                run_id,
                page_id,
                GrowthAuditPagePerformanceAnalysisRequest(strategy="mobile"),
                session,
            )

        assert response.result.score == 72
        assert response.findings_count == 1

    asyncio.run(run())


def test_performance_route_missing_api_key_returns_503() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        page_id = uuid4()
        session = AsyncMock()

        with (
            patch(
                "app.api.routes.growth_audit.get_project_in_default_workspace",
                new=AsyncMock(),
            ),
            patch(
                "app.api.routes.growth_audit.analyze_growth_audit_page_performance",
                new=AsyncMock(
                    side_effect=GoogleIntegrationNotConfiguredError(
                        "PageSpeed Insights non configurato.",
                        integration="google_pagespeed",
                    )
                ),
            ),
            pytest.raises(HTTPException) as exc,
        ):
            await analyze_growth_audit_page_performance_endpoint(
                project_id,
                run_id,
                page_id,
                GrowthAuditPagePerformanceAnalysisRequest(),
                session,
            )

        assert exc.value.status_code == 503

    asyncio.run(run())


def test_normalize_pagespeed_fixture_score() -> None:
    normalized = normalize_pagespeed_result(_pagespeed_raw())
    assert normalized["performanceScore"] == 72
