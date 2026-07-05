"""Tests for Project API routes and schemas."""

from __future__ import annotations

import asyncio
import os
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

from app.api.routes.projects import create_project, update_project
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate, normalize_public_site_url


def test_normalize_public_site_url_adds_https_and_strips_trailing_slash() -> None:
    assert normalize_public_site_url("solmielato.it") == "https://solmielato.it"
    assert normalize_public_site_url("https://solmielato.it/") == "https://solmielato.it"
    assert normalize_public_site_url("  ") is None
    assert normalize_public_site_url("") is None


def test_normalize_public_site_url_allows_myshopify_domain() -> None:
    assert normalize_public_site_url("https://shop.myshopify.com") == "https://shop.myshopify.com"


def test_project_read_serializes_public_site_url() -> None:
    now = datetime.now(UTC)
    project_id = uuid4()
    project = Project(
        id=project_id,
        workspace_id=uuid4(),
        name="Solmielato",
        slug="solmielato",
        description=None,
        public_site_url="https://solmielato.it",
        status="active",
        created_at=now,
        updated_at=now,
    )
    payload = ProjectRead.model_validate(project).model_dump(by_alias=True)
    assert payload["publicSiteUrl"] == "https://solmielato.it"


def test_project_create_accepts_public_site_url() -> None:
    body = ProjectCreate.model_validate(
        {
            "name": "Solmielato",
            "publicSiteUrl": "solmielato.it",
        }
    )
    assert body.public_site_url == "https://solmielato.it"


def test_project_update_empty_public_site_url_becomes_none() -> None:
    body = ProjectUpdate.model_validate({"publicSiteUrl": "   "})
    assert body.public_site_url is None


def test_update_project_persists_public_site_url() -> None:
    async def run() -> None:
        project_id = uuid4()
        now = datetime.now(UTC)
        project = Project(
            id=project_id,
            workspace_id=uuid4(),
            name="Solmielato",
            slug="solmielato",
            description=None,
            public_site_url=None,
            status="active",
            created_at=now,
            updated_at=now,
        )
        session = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        async def refresh_side_effect(obj: Project) -> None:
            obj.public_site_url = "https://solmielato.it"

        session.refresh.side_effect = refresh_side_effect

        with patch(
            "app.api.routes.projects.get_project_in_default_workspace",
            new_callable=AsyncMock,
            return_value=project,
        ):
            result = await update_project(
                project_id,
                ProjectUpdate.model_validate({"publicSiteUrl": "https://solmielato.it"}),
                session,
            )

        assert result.public_site_url == "https://solmielato.it"
        session.commit.assert_awaited_once()
        session.refresh.assert_awaited_once()

    asyncio.run(run())


def test_update_project_clears_public_site_url_with_empty_string() -> None:
    async def run() -> None:
        project_id = uuid4()
        now = datetime.now(UTC)
        project = Project(
            id=project_id,
            workspace_id=uuid4(),
            name="Solmielato",
            slug="solmielato",
            description=None,
            public_site_url="https://solmielato.it",
            status="active",
            created_at=now,
            updated_at=now,
        )
        session = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        async def refresh_side_effect(obj: Project) -> None:
            obj.public_site_url = None

        session.refresh.side_effect = refresh_side_effect

        with patch(
            "app.api.routes.projects.get_project_in_default_workspace",
            new_callable=AsyncMock,
            return_value=project,
        ):
            result = await update_project(
                project_id,
                ProjectUpdate.model_validate({"publicSiteUrl": ""}),
                session,
            )

        assert result.public_site_url is None

    asyncio.run(run())


def test_create_project_passes_public_site_url_to_model() -> None:
    async def run() -> None:
        session = AsyncMock()
        session.add = lambda _obj: None
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        workspace = type("Workspace", (), {"id": uuid4()})()

        with (
            patch(
                "app.api.routes.projects.get_default_workspace",
                new_callable=AsyncMock,
                return_value=workspace,
            ),
            patch(
                "app.api.routes.projects.unique_project_slug",
                new_callable=AsyncMock,
                return_value="solmielato",
            ),
        ):
            body = ProjectCreate.model_validate(
                {
                    "name": "Solmielato",
                    "publicSiteUrl": "solmielato.it",
                }
            )
            created = await create_project(body, session)

        assert created.public_site_url == "https://solmielato.it"

    asyncio.run(run())
