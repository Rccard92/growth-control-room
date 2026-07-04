"""Tests for Growth Audit single-page rescan."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.models.growth_audit import GrowthAuditEvent, GrowthAuditPage, GrowthAuditRun
from app.schemas.growth_audit import GrowthAuditPageRescanRequest
from app.services.growth_audit.exceptions import (
    GrowthAuditRunNotFoundError,
    GrowthAuditValidationError,
)
from app.services.growth_audit.run_service import rescan_growth_audit_page


def _mock_scan_result(url: str = "https://example.com/products/a", *, score: int = 88) -> dict:
    return {
        "url": url,
        "finalUrl": url,
        "httpStatus": 200,
        "fetchError": None,
        "title": "Updated Product Title Between Thirty And Sixty Five",
        "metaDescription": "Updated meta description long enough for search engines and users.",
        "canonicalUrl": url,
        "h1": "Updated H1",
        "score": score,
        "schema": {"types": ["Product", "WebPage"]},
        "images": {"total": 3, "missingAlt": 0},
        "links": {"internal": 5, "external": 2},
        "robots": {"noindex": False, "nofollow": False},
        "findings": [
            {
                "category": "seo",
                "severity": "medium",
                "priority": "medium",
                "title": "New finding after rescan",
                "description": "Issue",
                "recommendation": "Fix it",
            }
        ],
        "tasks": [
            {
                "title": "New task after rescan",
                "description": "Do it",
                "ownerType": "seo",
                "priority": "high",
                "estimatedEffort": "low",
            }
        ],
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
        seo_score=70,
        summary={
            "pagesAnalyzed": 2,
            "sources": {"seed": 1, "sitemap": 1},
            "pageTypes": {"homepage": 1, "product": 1},
        },
        config={"includeAiAnalysis": False},
        created_at=now,
        updated_at=now,
    )


def _build_analyzed_page(*, project_id, run_id, page_id=None) -> GrowthAuditPage:
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
        source="sitemap",
        status="analyzed",
        priority="normal",
        title="Old title",
        score=55,
        http_status=200,
        created_at=now,
        updated_at=now,
    )


def test_rescan_rejects_active_run() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        page_id = uuid4()
        audit_run = _build_completed_run(project_id, run_id)
        audit_run.status = "analyzing"

        session = AsyncMock()
        with patch(
            "app.services.growth_audit.run_service.get_growth_audit_run",
            new=AsyncMock(return_value=audit_run),
        ):
            with pytest.raises(GrowthAuditValidationError, match="still active"):
                await rescan_growth_audit_page(
                    session,
                    project_id=project_id,
                    run_id=run_id,
                    page_id=page_id,
                )

    asyncio.run(run())


def test_rescan_page_not_found() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        page_id = uuid4()
        audit_run = _build_completed_run(project_id, run_id)

        session = AsyncMock()
        with (
            patch(
                "app.services.growth_audit.run_service.get_growth_audit_run",
                new=AsyncMock(return_value=audit_run),
            ),
            patch(
                "app.services.growth_audit.run_service._get_growth_audit_page",
                new=AsyncMock(return_value=None),
            ),
        ):
            with pytest.raises(GrowthAuditRunNotFoundError):
                await rescan_growth_audit_page(
                    session,
                    project_id=project_id,
                    run_id=run_id,
                    page_id=page_id,
                )

    asyncio.run(run())


def test_rescan_updates_analyzed_page() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        page_id = uuid4()
        audit_run = _build_completed_run(project_id, run_id)
        page = _build_analyzed_page(project_id=project_id, run_id=run_id, page_id=page_id)

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
                "app.services.growth_audit.run_service.get_growth_audit_run",
                new=AsyncMock(return_value=audit_run),
            ),
            patch(
                "app.services.growth_audit.run_service._get_growth_audit_page",
                new=AsyncMock(return_value=page),
            ),
            patch(
                "app.services.growth_audit.run_service.scan_page_technical",
                new=AsyncMock(return_value=_mock_scan_result(page.url, score=88)),
            ),
            patch(
                "app.services.growth_audit.run_service.score_technical_scan",
            ),
            patch(
                "app.services.growth_audit.run_service._supersede_page_open_items",
                new=AsyncMock(return_value=(1, 1)),
            ),
            patch(
                "app.services.growth_audit.run_service.recompute_growth_audit_run_summary",
                new=AsyncMock(),
            ) as mock_recompute,
            patch(
                "app.services.growth_audit.run_service._count_open_findings_and_tasks",
                new=AsyncMock(return_value=(1, 1)),
            ),
            patch(
                "app.services.growth_audit.run_service.create_growth_audit_event",
                new=AsyncMock(side_effect=track_event),
            ),
        ):
            result_run, result_page, findings_count, tasks_count = await rescan_growth_audit_page(
                session,
                project_id=project_id,
                run_id=run_id,
                page_id=page_id,
                clear_previous_open_items=True,
            )

        assert result_page.score == 88
        assert result_page.title == "Updated Product Title Between Thirty And Sixty Five"
        assert result_page.status == "analyzed"
        assert findings_count == 1
        assert tasks_count == 1
        assert "page_rescan_started" in events
        assert "page_previous_items_superseded" in events
        assert "page_rescan_completed" in events
        mock_recompute.assert_awaited_once()
        assert session.add.call_count >= 1

    asyncio.run(run())


def test_rescan_clear_previous_false_skips_supersede() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        page_id = uuid4()
        audit_run = _build_completed_run(project_id, run_id)
        page = _build_analyzed_page(project_id=project_id, run_id=run_id, page_id=page_id)

        session = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        with (
            patch(
                "app.services.growth_audit.run_service.get_growth_audit_run",
                new=AsyncMock(return_value=audit_run),
            ),
            patch(
                "app.services.growth_audit.run_service._get_growth_audit_page",
                new=AsyncMock(return_value=page),
            ),
            patch(
                "app.services.growth_audit.run_service.scan_page_technical",
                new=AsyncMock(return_value=_mock_scan_result(page.url)),
            ),
            patch("app.services.growth_audit.run_service.score_technical_scan"),
            patch(
                "app.services.growth_audit.run_service._supersede_page_open_items",
                new=AsyncMock(return_value=(0, 0)),
            ) as mock_supersede,
            patch(
                "app.services.growth_audit.run_service.recompute_growth_audit_run_summary",
                new=AsyncMock(),
            ),
            patch(
                "app.services.growth_audit.run_service._count_open_findings_and_tasks",
                new=AsyncMock(return_value=(2, 2)),
            ),
            patch(
                "app.services.growth_audit.run_service.create_growth_audit_event",
                new=AsyncMock(),
            ),
        ):
            await rescan_growth_audit_page(
                session,
                project_id=project_id,
                run_id=run_id,
                page_id=page_id,
                clear_previous_open_items=False,
            )

        mock_supersede.assert_not_awaited()

    asyncio.run(run())


def test_rescan_scan_failure_marks_page_failed() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        page_id = uuid4()
        audit_run = _build_completed_run(project_id, run_id)
        page = _build_analyzed_page(project_id=project_id, run_id=run_id, page_id=page_id)

        session = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        events: list[str] = []

        async def track_event(session_arg, **kwargs):
            events.append(kwargs["event_type"])
            return MagicMock()

        with (
            patch(
                "app.services.growth_audit.run_service.get_growth_audit_run",
                new=AsyncMock(return_value=audit_run),
            ),
            patch(
                "app.services.growth_audit.run_service._get_growth_audit_page",
                new=AsyncMock(return_value=page),
            ),
            patch(
                "app.services.growth_audit.run_service.scan_page_technical",
                new=AsyncMock(side_effect=RuntimeError("network down")),
            ),
            patch(
                "app.services.growth_audit.run_service._supersede_page_open_items",
                new=AsyncMock(return_value=(0, 0)),
            ),
            patch(
                "app.services.growth_audit.run_service.recompute_growth_audit_run_summary",
                new=AsyncMock(),
            ),
            patch(
                "app.services.growth_audit.run_service._count_open_findings_and_tasks",
                new=AsyncMock(return_value=(0, 0)),
            ),
            patch(
                "app.services.growth_audit.run_service.create_growth_audit_event",
                new=AsyncMock(side_effect=track_event),
            ),
        ):
            _, result_page, _, _ = await rescan_growth_audit_page(
                session,
                project_id=project_id,
                run_id=run_id,
                page_id=page_id,
            )

        assert result_page.status == "failed"
        assert "page_rescan_failed" in events

    asyncio.run(run())


def test_rescan_route_returns_200() -> None:
    async def run() -> None:
        from app.api.routes.growth_audit import rescan_growth_audit_page_endpoint

        project_id = uuid4()
        run_id = uuid4()
        page_id = uuid4()
        session = AsyncMock()
        audit_run = _build_completed_run(project_id, run_id)
        page = _build_analyzed_page(project_id=project_id, run_id=run_id, page_id=page_id)
        page.score = 90
        page.status = "analyzed"

        with (
            patch(
                "app.api.routes.growth_audit.get_project_in_default_workspace",
                new_callable=AsyncMock,
            ),
            patch(
                "app.api.routes.growth_audit.rescan_growth_audit_page",
                new_callable=AsyncMock,
                return_value=(audit_run, page, 2, 1),
            ),
        ):
            response = await rescan_growth_audit_page_endpoint(
                project_id,
                run_id,
                page_id,
                GrowthAuditPageRescanRequest(clearPreviousOpenItems=True),
                session,
            )

        assert response.run.id == run_id
        assert response.page.id == page_id
        assert response.findings_count == 2
        assert response.tasks_count == 1
        assert "riscansionata" in response.message.lower()

    asyncio.run(run())
