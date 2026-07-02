"""Tests for SEO skill run API routes."""

from __future__ import annotations

import asyncio
import os
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

from app.api.routes.seo_skills import (
    create_project_seo_skill_run,
    get_project_seo_skill_run,
    get_project_seo_skill_run_results,
    get_seo_skill_catalog,
    list_project_seo_skill_runs,
)
from app.models.seo_skills import SeoSkillRun, SeoSkillRunResult
from app.schemas.seo_skills import SeoSkillRunCreateRequest, SeoSkillCatalogCounts
from app.services.seo_skills.exceptions import SeoSkillRunValidationError


def _request(**overrides: object) -> SeoSkillRunCreateRequest:
    base = {
        "targetType": "url",
        "url": "https://example.com/page",
        "selectedSkills": ["seo_page"],
        "provider": "claude",
    }
    base.update(overrides)
    return SeoSkillRunCreateRequest.model_validate(base)


def _run_with_results(project_id, run_id=None) -> SeoSkillRun:
    run_id = run_id or uuid4()
    now = datetime.now(UTC)
    run = SeoSkillRun(
        id=run_id,
        project_id=project_id,
        target_type="url",
        url="https://example.com/page",
        status="pending",
        provider="claude",
        selected_skills=["seo_page"],
        progress_percent=0,
        created_at=now,
        updated_at=now,
    )
    run.results = [
        SeoSkillRunResult(
            id=uuid4(),
            run_id=run_id,
            project_id=project_id,
            skill_key="seo_page",
            status="pending",
            created_at=now,
            updated_at=now,
        )
    ]
    return run


def test_seo_skills_catalog_route_still_registered() -> None:
    from app.api.routes import seo_skills

    paths = {route.path for route in seo_skills.router.routes}
    assert "/projects/{project_id}/seo-skills/catalog" in paths
    assert "/projects/{project_id}/seo-skills/runs" in paths
    assert "/projects/{project_id}/seo-skills/runs/{run_id}" in paths
    assert "/projects/{project_id}/seo-skills/runs/{run_id}/results" in paths


def test_create_project_seo_skill_run_returns_run() -> None:
    async def run() -> None:
        project_id = uuid4()
        session = AsyncMock()
        created = _run_with_results(project_id)

        with (
            patch(
                "app.api.routes.seo_skills.get_project_in_default_workspace",
                new_callable=AsyncMock,
            ) as mock_project,
            patch(
                "app.api.routes.seo_skills.is_claude_configured",
                return_value=True,
            ),
            patch(
                "app.api.routes.seo_skills.start_seo_skill_run",
                new_callable=AsyncMock,
                return_value=created,
            ) as mock_start,
        ):
            response = await create_project_seo_skill_run(
                project_id,
                _request(),
                session=session,
            )

        mock_project.assert_awaited_once_with(project_id, session)
        mock_start.assert_awaited_once_with(session, project_id, _request())
        assert response.run.id == created.id
        assert response.run.target_type == "url"
        assert response.run.status == "pending"
        assert response.run.selected_skills == ["seo_page"]

    asyncio.run(run())


def test_create_project_seo_skill_run_claude_not_configured_returns_503() -> None:
    async def run() -> None:
        project_id = uuid4()
        session = AsyncMock()

        with (
            patch(
                "app.api.routes.seo_skills.get_project_in_default_workspace",
                new_callable=AsyncMock,
            ),
            patch(
                "app.api.routes.seo_skills.is_claude_configured",
                return_value=False,
            ),
            patch(
                "app.api.routes.seo_skills.start_seo_skill_run",
                new_callable=AsyncMock,
            ) as mock_start,
        ):
            with pytest.raises(HTTPException) as exc:
                await create_project_seo_skill_run(
                    project_id,
                    _request(provider="claude"),
                    session=session,
                )

        assert exc.value.status_code == 503
        assert exc.value.detail == "Claude provider is not configured"
        mock_start.assert_not_awaited()

    asyncio.run(run())


def test_create_project_seo_skill_run_validation_error_returns_422() -> None:
    async def run() -> None:
        project_id = uuid4()
        session = AsyncMock()

        with (
            patch(
                "app.api.routes.seo_skills.get_project_in_default_workspace",
                new_callable=AsyncMock,
            ),
            patch(
                "app.api.routes.seo_skills.is_claude_configured",
                return_value=True,
            ),
            patch(
                "app.api.routes.seo_skills.start_seo_skill_run",
                new_callable=AsyncMock,
                side_effect=SeoSkillRunValidationError(
                    "At least one SEO skill must be selected"
                ),
            ),
        ):
            with pytest.raises(HTTPException) as exc:
                await create_project_seo_skill_run(
                    project_id,
                    _request(selectedSkills=[]),
                    session=session,
                )

        assert exc.value.status_code == 422

    asyncio.run(run())


def test_list_project_seo_skill_runs_returns_project_runs() -> None:
    async def run() -> None:
        project_id = uuid4()
        session = AsyncMock()
        runs = [_run_with_results(project_id)]

        with (
            patch(
                "app.api.routes.seo_skills.get_project_in_default_workspace",
                new_callable=AsyncMock,
            ) as mock_project,
            patch(
                "app.api.routes.seo_skills.list_seo_skill_runs",
                new_callable=AsyncMock,
                return_value=runs,
            ) as mock_list,
        ):
            response = await list_project_seo_skill_runs(
                project_id,
                session=session,
                limit=20,
            )

        mock_project.assert_awaited_once_with(project_id, session)
        mock_list.assert_awaited_once_with(session, project_id, limit=20)
        assert len(response) == 1
        assert response[0].project_id == project_id

    asyncio.run(run())


def test_get_project_seo_skill_run_returns_run_and_results() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        session = AsyncMock()
        stored = _run_with_results(project_id, run_id=run_id)

        with (
            patch(
                "app.api.routes.seo_skills.get_project_in_default_workspace",
                new_callable=AsyncMock,
            ),
            patch(
                "app.api.routes.seo_skills.get_seo_skill_run",
                new_callable=AsyncMock,
                return_value=stored,
            ) as mock_get,
        ):
            response = await get_project_seo_skill_run(
                project_id,
                run_id,
                session=session,
            )

        mock_get.assert_awaited_once_with(session, project_id, run_id)
        assert response.run.id == run_id
        assert len(response.results) == 1
        assert response.results[0].skill_key == "seo_page"

    asyncio.run(run())


def test_get_project_seo_skill_run_not_found_returns_404() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        session = AsyncMock()

        with (
            patch(
                "app.api.routes.seo_skills.get_project_in_default_workspace",
                new_callable=AsyncMock,
            ),
            patch(
                "app.api.routes.seo_skills.get_seo_skill_run",
                new_callable=AsyncMock,
                return_value=None,
            ),
        ):
            with pytest.raises(HTTPException) as exc:
                await get_project_seo_skill_run(
                    project_id,
                    run_id,
                    session=session,
                )

        assert exc.value.status_code == 404

    asyncio.run(run())


def test_get_project_seo_skill_run_results_returns_only_results() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        session = AsyncMock()
        stored = _run_with_results(project_id, run_id=run_id)

        with (
            patch(
                "app.api.routes.seo_skills.get_project_in_default_workspace",
                new_callable=AsyncMock,
            ),
            patch(
                "app.api.routes.seo_skills.get_seo_skill_run",
                new_callable=AsyncMock,
                return_value=stored,
            ),
        ):
            response = await get_project_seo_skill_run_results(
                project_id,
                run_id,
                session=session,
            )

        assert len(response) == 1
        assert response[0].run_id == run_id
        assert response[0].skill_key == "seo_page"

    asyncio.run(run())


def test_get_seo_skill_catalog_still_works() -> None:
    async def run() -> None:
        project_id = uuid4()
        session = AsyncMock()

        with (
            patch(
                "app.api.routes.seo_skills.get_project_in_default_workspace",
                new_callable=AsyncMock,
            ) as mock_project,
            patch(
                "app.api.routes.seo_skills.load_seo_skill_catalog",
                return_value=[],
            ),
            patch(
                "app.api.routes.seo_skills._build_counts",
                return_value=SeoSkillCatalogCounts(
                    total=0,
                    available=0,
                    needs_config=0,
                    external_required=0,
                    planned=0,
                ),
            ),
        ):
            response = await get_seo_skill_catalog(project_id, session=session)

        mock_project.assert_awaited_once_with(project_id, session)
        assert response.skills == []

    asyncio.run(run())
