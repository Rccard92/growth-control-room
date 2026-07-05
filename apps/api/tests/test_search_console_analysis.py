"""Tests for Growth Audit Search Console analysis."""

from __future__ import annotations

import asyncio
import os
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

from app.api.routes.growth_audit import analyze_growth_audit_search_console_endpoint
from app.models.growth_audit import GrowthAuditPage, GrowthAuditRun
from app.schemas.growth_audit import GrowthAuditSearchConsoleAnalysisRequest
from app.services.google.exceptions import GoogleIntegrationNotConnectedError
from app.services.growth_audit.exceptions import GrowthAuditValidationError
from app.services.growth_audit.search_console_analysis import (
    _build_gsc_findings,
    _build_page_metrics_lookup,
    _compute_run_gsc_summary,
    analyze_growth_audit_search_console,
)


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


def test_build_page_metrics_lookup_extracts_queries() -> None:
    metrics = _build_page_metrics_lookup(
        [
            {
                "keys": ["https://example.com/products/a"],
                "clicks": 10,
                "impressions": 200,
                "ctr": 0.05,
                "position": 8.2,
            }
        ],
        [
            {
                "keys": ["https://example.com/products/a", "miele bio"],
                "clicks": 4,
                "impressions": 80,
                "ctr": 0.05,
                "position": 7.5,
            }
        ],
    )
    assert "https://example.com/products/a" in metrics
    assert metrics["https://example.com/products/a"]["clicks"] == 10
    assert metrics["https://example.com/products/a"]["topQueries"][0]["query"] == "miele bio"


def test_compute_run_gsc_summary_aggregates_totals() -> None:
    summary = _compute_run_gsc_summary(
        {
            "https://example.com/a": {
                "clicks": 10,
                "impressions": 100,
                "ctr": 0.1,
                "position": 5.0,
                "topQueries": [],
            },
            "https://example.com/b": {
                "clicks": 5,
                "impressions": 50,
                "ctr": 0.1,
                "position": 7.0,
                "topQueries": [],
            },
        },
        synced_at="2026-06-13T10:00:00Z",
    )
    assert summary["totalClicks"] == 15
    assert summary["totalImpressions"] == 150
    assert summary["pagesWithData"] == 2


def test_build_gsc_findings_limited_to_ten() -> None:
    pages = [
        _build_page(project_id=uuid4(), run_id=uuid4(), page_id=uuid4())
        for _ in range(12)
    ]
    metrics = {
        page.normalized_url: {
            "clicks": 0,
            "impressions": 500,
            "ctr": 0.005,
            "position": 12.0,
            "topQueries": [{"query": "test", "clicks": 0, "impressions": 100, "ctr": 0, "position": 12}],
        }
        for page in pages
    }
    findings = _build_gsc_findings(pages, metrics)
    assert len(findings) <= 10


def test_analyze_search_console_requires_property() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        audit_run = _build_run(project_id, run_id)
        project = MagicMock()
        project.search_console_site_url = None

        session = AsyncMock()
        with (
            patch(
                "app.services.growth_audit.search_console_analysis.get_growth_audit_run",
                new=AsyncMock(return_value=audit_run),
            ),
            patch(
                "app.services.growth_audit.search_console_analysis.get_project_in_default_workspace",
                new=AsyncMock(return_value=project),
            ),
            pytest.raises(GrowthAuditValidationError, match="Seleziona prima"),
        ):
            await analyze_growth_audit_search_console(
                session,
                project_id=project_id,
                run_id=run_id,
            )

    asyncio.run(run())


def test_analyze_search_console_updates_page_metadata_and_summary() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        page = _build_page(project_id=project_id, run_id=run_id)
        audit_run = _build_run(project_id, run_id)
        audit_run.pages = [page]
        project = MagicMock()
        project.search_console_site_url = "https://example.com/"

        session = AsyncMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        with (
            patch(
                "app.services.growth_audit.search_console_analysis.get_growth_audit_run",
                new=AsyncMock(return_value=audit_run),
            ),
            patch(
                "app.services.growth_audit.search_console_analysis.get_project_in_default_workspace",
                new=AsyncMock(return_value=project),
            ),
            patch(
                "app.services.growth_audit.search_console_analysis.get_valid_google_access_token",
                new=AsyncMock(return_value="access-token"),
            ),
            patch(
                "app.services.growth_audit.search_console_analysis.fetch_search_console_search_analytics",
                new=AsyncMock(
                    side_effect=[
                        {
                            "rows": [
                                {
                                    "keys": ["https://example.com/products/a"],
                                    "clicks": 12,
                                    "impressions": 240,
                                    "ctr": 0.05,
                                    "position": 8.1,
                                }
                            ]
                        },
                        {
                            "rows": [
                                {
                                    "keys": ["https://example.com/products/a", "miele"],
                                    "clicks": 5,
                                    "impressions": 90,
                                    "ctr": 0.055,
                                    "position": 7.8,
                                }
                            ]
                        },
                    ]
                ),
            ),
            patch(
                "app.services.growth_audit.search_console_analysis.list_growth_audit_pages",
                new=AsyncMock(return_value=[page]),
            ),
            patch(
                "app.services.growth_audit.search_console_analysis.create_growth_audit_event",
                new=AsyncMock(),
            ),
        ):
            result = await analyze_growth_audit_search_console(
                session,
                project_id=project_id,
                run_id=run_id,
            )

        assert result["pages_updated"] == 1
        assert page.page_metadata["searchConsole"]["clicks"] == 12
        assert audit_run.summary["searchConsole"]["totalClicks"] == 12
        session.commit.assert_awaited_once()

    asyncio.run(run())


def test_search_console_route_returns_503_when_not_connected() -> None:
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
                "app.api.routes.growth_audit.analyze_growth_audit_search_console",
                new=AsyncMock(
                    side_effect=GoogleIntegrationNotConnectedError(
                        "Account Google non collegato.",
                        integration="google_search_console",
                    )
                ),
            ),
            pytest.raises(HTTPException) as exc,
        ):
            await analyze_growth_audit_search_console_endpoint(
                project_id,
                run_id,
                GrowthAuditSearchConsoleAnalysisRequest(days=28),
                session,
            )

        assert exc.value.status_code == 503

    asyncio.run(run())


def test_search_console_route_returns_200_with_mock() -> None:
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
                "app.api.routes.growth_audit.analyze_growth_audit_search_console",
                new=AsyncMock(
                    return_value={
                        "run": audit_run,
                        "summary": {"totalClicks": 10, "totalImpressions": 100},
                        "pages_updated": 1,
                        "findings_created": 1,
                    }
                ),
            ),
        ):
            response = await analyze_growth_audit_search_console_endpoint(
                project_id,
                run_id,
                GrowthAuditSearchConsoleAnalysisRequest(),
                session,
            )

        assert response.summary["totalClicks"] == 10
        assert "aggiornati" in response.message.lower()

    asyncio.run(run())
