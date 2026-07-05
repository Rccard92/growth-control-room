"""Tests for Growth Audit Google Analytics 4 analysis."""

from __future__ import annotations

import asyncio
import os
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

from app.api.routes.growth_audit import analyze_growth_audit_analytics_endpoint
from app.models.growth_audit import GrowthAuditPage, GrowthAuditRun
from app.schemas.growth_audit import GrowthAuditAnalyticsAnalysisRequest
from app.services.google.exceptions import GoogleIntegrationNotConnectedError
from app.services.growth_audit.analytics_analysis import (
    _build_ga4_findings,
    _build_landing_metrics_lookup,
    _compute_run_analytics_summary,
    analyze_growth_audit_analytics,
)
from app.services.growth_audit.exceptions import GrowthAuditValidationError


def _build_run(project_id, run_id=None) -> GrowthAuditRun:
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
        summary={},
        config={},
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


def test_build_landing_metrics_lookup_normalizes_paths() -> None:
    metrics = _build_landing_metrics_lookup(
        [
            {
                "landingPagePlusQueryString": "/products/a",
                "sessions": 80,
                "totalUsers": 60,
                "engagedSessions": 40,
                "engagementRate": 0.35,
                "averageSessionDuration": 90,
                "conversions": 0,
                "totalRevenue": 0,
            }
        ],
        base_url="https://example.com",
    )
    assert "https://example.com/products/a" in metrics
    assert metrics["https://example.com/products/a"]["sessions"] == 80
    assert metrics["https://example.com/products/a"]["engagementRate"] == 0.35


def test_compute_run_analytics_summary_aggregates_totals() -> None:
    summary = _compute_run_analytics_summary(
        {
            "https://example.com/a": {
                "sessions": 100,
                "totalUsers": 80,
                "engagedSessions": 60,
                "engagementRate": 0.5,
                "averageSessionDuration": 80,
                "conversions": 2,
                "revenue": 120.5,
            },
            "https://example.com/b": {
                "sessions": 60,
                "totalUsers": 50,
                "engagedSessions": 30,
                "engagementRate": 0.3,
                "averageSessionDuration": 70,
                "conversions": 0,
                "revenue": 0,
            },
        },
        synced_at="2026-06-13T10:00:00Z",
    )
    assert summary["totalSessions"] == 160
    assert summary["totalUsers"] == 130
    assert summary["totalConversions"] == 2
    assert summary["pagesWithData"] == 2


def test_build_ga4_findings_limited_to_ten() -> None:
    pages = [_build_page(project_id=uuid4(), run_id=uuid4(), page_id=uuid4()) for _ in range(12)]
    metrics = {
        page.normalized_url: {
            "sessions": 60,
            "totalUsers": 50,
            "engagedSessions": 20,
            "engagementRate": 0.2,
            "averageSessionDuration": 50,
            "conversions": 0,
            "revenue": 0,
        }
        for page in pages
    }
    findings = _build_ga4_findings(pages, metrics)
    assert len(findings) <= 10


def test_analyze_analytics_requires_property() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        audit_run = _build_run(project_id, run_id)
        project = MagicMock()
        project.google_analytics_property_id = None

        session = AsyncMock()
        with (
            patch(
                "app.services.growth_audit.analytics_analysis.get_growth_audit_run",
                new=AsyncMock(return_value=audit_run),
            ),
            patch(
                "app.services.growth_audit.analytics_analysis.get_project_in_default_workspace",
                new=AsyncMock(return_value=project),
            ),
            pytest.raises(GrowthAuditValidationError, match="Seleziona prima"),
        ):
            await analyze_growth_audit_analytics(
                session,
                project_id=project_id,
                run_id=run_id,
            )

    asyncio.run(run())


def test_analyze_analytics_updates_page_metadata_and_summary() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        page = _build_page(project_id=project_id, run_id=run_id)
        audit_run = _build_run(project_id, run_id)
        project = MagicMock()
        project.google_analytics_property_id = "123456789"
        project.public_site_url = "https://example.com"

        session = AsyncMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.flush = AsyncMock()

        with (
            patch(
                "app.services.growth_audit.analytics_analysis.get_growth_audit_run",
                new=AsyncMock(return_value=audit_run),
            ),
            patch(
                "app.services.growth_audit.analytics_analysis.get_project_in_default_workspace",
                new=AsyncMock(return_value=project),
            ),
            patch(
                "app.services.growth_audit.analytics_analysis.get_valid_google_access_token",
                new=AsyncMock(return_value="access-token"),
            ),
            patch(
                "app.services.growth_audit.analytics_analysis.fetch_ga4_landing_pages_report",
                new=AsyncMock(
                    return_value={
                        "rows": [
                            {
                                "landingPagePlusQueryString": "/products/a",
                                "sessions": 55,
                                "totalUsers": 40,
                                "engagedSessions": 20,
                                "engagementRate": 0.35,
                                "averageSessionDuration": 75,
                                "conversions": 0,
                                "totalRevenue": 0,
                            }
                        ]
                    }
                ),
            ),
            patch(
                "app.services.growth_audit.analytics_analysis.list_growth_audit_pages",
                new=AsyncMock(return_value=[page]),
            ),
            patch(
                "app.services.growth_audit.analytics_analysis.create_growth_audit_event",
                new=AsyncMock(),
            ),
        ):
            result = await analyze_growth_audit_analytics(
                session,
                project_id=project_id,
                run_id=run_id,
            )

        assert result["pages_updated"] == 1
        assert page.page_metadata["analytics"]["sessions"] == 55
        assert audit_run.summary["analytics"]["totalSessions"] == 55
        session.commit.assert_awaited_once()

    asyncio.run(run())


def test_analytics_route_returns_503_when_not_connected() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        session = AsyncMock()

        with (
            patch(
                "app.api.routes.growth_audit.get_project_in_default_workspace",
                new=AsyncMock(),
            ),
            patch(
                "app.api.routes.growth_audit.analyze_growth_audit_analytics",
                new=AsyncMock(
                    side_effect=GoogleIntegrationNotConnectedError(
                        "Account Google non collegato.",
                        integration="ga4",
                    )
                ),
            ),
            pytest.raises(HTTPException) as exc,
        ):
            await analyze_growth_audit_analytics_endpoint(
                project_id,
                run_id,
                GrowthAuditAnalyticsAnalysisRequest(days=28),
                session,
            )

        assert exc.value.status_code == 503

    asyncio.run(run())


def test_analytics_route_returns_200_with_mock() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        audit_run = _build_run(project_id, run_id)
        session = AsyncMock()

        with (
            patch(
                "app.api.routes.growth_audit.get_project_in_default_workspace",
                new=AsyncMock(),
            ),
            patch(
                "app.api.routes.growth_audit.analyze_growth_audit_analytics",
                new=AsyncMock(
                    return_value={
                        "run": audit_run,
                        "summary": {"totalSessions": 120, "totalUsers": 90},
                        "pages_updated": 2,
                        "findings_created": 1,
                    }
                ),
            ),
        ):
            response = await analyze_growth_audit_analytics_endpoint(
                project_id,
                run_id,
                GrowthAuditAnalyticsAnalysisRequest(),
                session,
            )

        assert response.summary["totalSessions"] == 120
        assert "GA4" in response.message

    asyncio.run(run())
