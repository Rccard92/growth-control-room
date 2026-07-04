"""Tests for Growth Audit API routes."""

from __future__ import annotations

import asyncio
import os
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

from app.api.routes.growth_audit import (
    create_growth_audit_run_endpoint,
    get_growth_audit_run_endpoint,
    list_growth_audit_events_endpoint,
    list_growth_audit_pages_endpoint,
    list_growth_audit_runs_endpoint,
)
from app.models.growth_audit import GrowthAuditEvent, GrowthAuditPage, GrowthAuditRun
from app.schemas.growth_audit import GrowthAuditRunCreateRequest
from app.services.growth_audit.exceptions import GrowthAuditRunNotFoundError


def _request(**overrides: object) -> GrowthAuditRunCreateRequest:
    base = {
        "rootUrl": "https://example.com",
        "provider": "openai",
        "auditMode": "full_site_mvp",
        "maxPages": 50,
        "includeAiAnalysis": False,
    }
    base.update(overrides)
    return GrowthAuditRunCreateRequest.model_validate(base)


def _run_with_relations(project_id, run_id=None) -> GrowthAuditRun:
    run_id = run_id or uuid4()
    now = datetime.now(UTC)
    run = GrowthAuditRun(
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
        pages_analyzed=0,
        pages_failed=0,
        created_at=now,
        updated_at=now,
    )
    run.pages = [
        GrowthAuditPage(
            id=uuid4(),
            run_id=run_id,
            project_id=project_id,
            url="https://example.com",
            normalized_url="https://example.com",
            path="/",
            page_type="homepage",
            source="seed",
            status="classified",
            priority="high",
            created_at=now,
            updated_at=now,
        )
    ]
    run.events = [
        GrowthAuditEvent(
            id=uuid4(),
            run_id=run_id,
            project_id=project_id,
            event_type="run_completed",
            phase="completed",
            message="Done",
            progress_percent=100,
            created_at=now,
        )
    ]
    return run


def test_growth_audit_routes_registered() -> None:
    from app.api.routes import growth_audit

    paths = {route.path for route in growth_audit.router.routes}
    assert "/projects/{project_id}/growth-audit/runs" in paths
    assert "/projects/{project_id}/growth-audit/runs/{run_id}" in paths
    assert "/projects/{project_id}/growth-audit/runs/{run_id}/pages" in paths
    assert "/projects/{project_id}/growth-audit/runs/{run_id}/events" in paths


def test_create_growth_audit_run_returns_201_payload() -> None:
    async def run() -> None:
        project_id = uuid4()
        session = AsyncMock()
        created = _run_with_relations(project_id)

        with (
            patch(
                "app.api.routes.growth_audit.get_project_in_default_workspace",
                new_callable=AsyncMock,
            ),
            patch(
                "app.api.routes.growth_audit.start_growth_audit_run",
                new_callable=AsyncMock,
                return_value=created,
            ),
        ):
            response = await create_growth_audit_run_endpoint(
                project_id,
                _request(),
                session,
            )

        assert response.run.id == created.id
        assert response.run.status == "completed"

    asyncio.run(run())


def test_list_growth_audit_runs_endpoint() -> None:
    async def run() -> None:
        project_id = uuid4()
        session = AsyncMock()
        created = _run_with_relations(project_id)

        with (
            patch(
                "app.api.routes.growth_audit.get_project_in_default_workspace",
                new_callable=AsyncMock,
            ),
            patch(
                "app.api.routes.growth_audit.list_growth_audit_runs",
                new_callable=AsyncMock,
                return_value=[created],
            ),
        ):
            response = await list_growth_audit_runs_endpoint(project_id, 20, session)

        assert len(response.runs) == 1

    asyncio.run(run())


def test_get_growth_audit_run_detail_endpoint() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        session = AsyncMock()
        created = _run_with_relations(project_id, run_id)

        with (
            patch(
                "app.api.routes.growth_audit.get_project_in_default_workspace",
                new_callable=AsyncMock,
            ),
            patch(
                "app.api.routes.growth_audit.get_growth_audit_run_detail",
                new_callable=AsyncMock,
                return_value=(created, 0, 0),
            ),
        ):
            response = await get_growth_audit_run_endpoint(project_id, run_id, session)

        assert response.run.id == run_id
        assert len(response.pages) == 1
        assert len(response.events) == 1

    asyncio.run(run())


def test_list_pages_and_events_endpoints() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        session = AsyncMock()
        created = _run_with_relations(project_id, run_id)

        with (
            patch(
                "app.api.routes.growth_audit.get_project_in_default_workspace",
                new_callable=AsyncMock,
            ),
            patch(
                "app.api.routes.growth_audit.list_growth_audit_pages",
                new_callable=AsyncMock,
                return_value=created.pages,
            ),
            patch(
                "app.api.routes.growth_audit.list_growth_audit_events",
                new_callable=AsyncMock,
                return_value=created.events,
            ),
        ):
            pages_response = await list_growth_audit_pages_endpoint(
                project_id,
                run_id,
                session,
            )
            events_response = await list_growth_audit_events_endpoint(
                project_id,
                run_id,
                session,
            )

        assert len(pages_response.pages) == 1
        assert len(events_response.events) == 1

    asyncio.run(run())


def test_get_growth_audit_run_wrong_project_returns_404() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        session = AsyncMock()

        with (
            patch(
                "app.api.routes.growth_audit.get_project_in_default_workspace",
                new_callable=AsyncMock,
            ),
            patch(
                "app.api.routes.growth_audit.get_growth_audit_run_detail",
                new_callable=AsyncMock,
                side_effect=GrowthAuditRunNotFoundError("not found"),
            ),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_growth_audit_run_endpoint(project_id, run_id, session)

        assert exc_info.value.status_code == 404

    asyncio.run(run())
