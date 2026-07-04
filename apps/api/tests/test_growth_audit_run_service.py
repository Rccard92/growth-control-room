"""Tests for Growth Audit run service."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.models.growth_audit import GrowthAuditEvent, GrowthAuditPage, GrowthAuditRun
from app.schemas.growth_audit import GrowthAuditRunCreateRequest
from app.services.growth_audit.exceptions import (
    GrowthAuditRunNotFoundError,
    GrowthAuditValidationError,
)
from app.services.growth_audit.run_service import (
    create_growth_audit_run,
    get_growth_audit_run,
    process_growth_audit_run,
    schedule_growth_audit_run,
    start_growth_audit_run,
)


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


def _build_run(*, project_id, run_id=None, status="queued") -> GrowthAuditRun:
    run_id = run_id or uuid4()
    now = datetime.now(UTC)
    run = GrowthAuditRun(
        id=run_id,
        project_id=project_id,
        root_url="https://example.com",
        normalized_domain="example.com",
        status=status,
        phase="queued",
        audit_mode="full_site_mvp",
        provider="openai",
        progress_percent=0,
        pages_discovered=1,
        config={"includeAiAnalysis": False},
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
            page_type="unknown",
            source="seed",
            status="discovered",
            priority="high",
            depth=0,
            discovered_at=now,
            created_at=now,
            updated_at=now,
        )
    ]
    run.events = []
    return run


def test_create_growth_audit_run_creates_seed_page_and_event() -> None:
    async def run() -> None:
        session = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        created = await create_growth_audit_run(session, uuid4(), _request())

        assert created.status == "queued"
        assert created.pages_discovered == 1
        assert created.normalized_domain == "example.com"
        assert session.add.call_count >= 3
        session.commit.assert_awaited_once()

    asyncio.run(run())


def test_create_growth_audit_run_requires_root_url() -> None:
    async def run() -> None:
        session = AsyncMock()
        with pytest.raises(GrowthAuditValidationError):
            await create_growth_audit_run(
                session,
                uuid4(),
                _request(rootUrl=""),
            )

    asyncio.run(run())


def test_process_growth_audit_run_completes_with_summary() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        audit_run = _build_run(project_id=project_id, run_id=run_id)

        session = AsyncMock()
        session.commit = AsyncMock()

        execute_result = MagicMock()
        execute_result.scalar_one_or_none.return_value = audit_run
        session.execute = AsyncMock(return_value=execute_result)

        session_factory = MagicMock()
        session_factory.return_value.__aenter__ = AsyncMock(return_value=session)
        session_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "app.services.growth_audit.run_service.get_session_factory",
            return_value=session_factory,
        ):
            await process_growth_audit_run(run_id)

        assert audit_run.status == "completed"
        assert audit_run.progress_percent == 100
        assert audit_run.summary is not None
        assert "message" in audit_run.summary

    asyncio.run(run())


def test_get_growth_audit_run_filters_by_project() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        audit_run = _build_run(project_id=project_id, run_id=run_id)

        session = AsyncMock()
        execute_result = MagicMock()
        execute_result.scalar_one_or_none.return_value = audit_run
        session.execute = AsyncMock(return_value=execute_result)

        found = await get_growth_audit_run(session, project_id, run_id)
        assert found is audit_run

        execute_result.scalar_one_or_none.return_value = None
        missing = await get_growth_audit_run(session, uuid4(), run_id)
        assert missing is None

    asyncio.run(run())


def test_schedule_growth_audit_run_creates_task() -> None:
    run_id = uuid4()
    with patch("app.services.growth_audit.run_service.asyncio.create_task") as mock_task:
        schedule_growth_audit_run(run_id)
        mock_task.assert_called_once()


def test_start_growth_audit_run_schedules_processing() -> None:
    async def run() -> None:
        session = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        with (
            patch(
                "app.services.growth_audit.run_service.schedule_growth_audit_run",
            ) as mock_schedule,
        ):
            created = await start_growth_audit_run(session, uuid4(), _request())
            mock_schedule.assert_called_once_with(created.id)

    asyncio.run(run())


def test_get_growth_audit_run_detail_not_found() -> None:
    async def run() -> None:
        from app.services.growth_audit.run_service import get_growth_audit_run_detail

        session = AsyncMock()
        execute_result = MagicMock()
        execute_result.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(return_value=execute_result)

        with pytest.raises(GrowthAuditRunNotFoundError):
            await get_growth_audit_run_detail(session, uuid4(), uuid4())

    asyncio.run(run())
