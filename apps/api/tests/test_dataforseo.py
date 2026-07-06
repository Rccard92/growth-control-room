"""DataForSEO Cost Sandbox tests."""

from __future__ import annotations

import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://test:test@localhost:5432/test",
)

import asyncio
import logging
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.core.config import settings
from app.services.dataforseo.dataforseo_budget import assert_dataforseo_budget_allows
from app.services.dataforseo.dataforseo_client import post_dataforseo
from app.services.dataforseo.dataforseo_cost_estimator import estimate_dataforseo_cost
from app.services.dataforseo.dataforseo_sandbox_service import run_dataforseo_sandbox_test
from app.services.dataforseo.dataforseo_usage_service import (
    DataForSeoUsageLogInput,
    record_dataforseo_usage,
)
from app.services.dataforseo.exceptions import (
    DataForSeoBudgetExceededError,
    DataForSeoRealCallsDisabledError,
)
from app.api.routes import dataforseo as dataforseo_routes


@pytest.fixture(autouse=True)
def reset_dataforseo_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "dataforseo_login", None)
    monkeypatch.setattr(settings, "dataforseo_password", None)
    monkeypatch.setattr(settings, "dataforseo_enable_real_calls", False)
    monkeypatch.setattr(settings, "dataforseo_single_run_limit_usd", 0.20)
    monkeypatch.setattr(settings, "dataforseo_daily_budget_usd", 1.00)
    monkeypatch.setattr(settings, "dataforseo_monthly_budget_usd", 10.00)


def test_status_configured_false_without_env() -> None:
    async def run() -> None:
        project_id = uuid4()
        session = AsyncMock()
        with patch(
            "app.api.routes.dataforseo.get_project_in_default_workspace",
            new=AsyncMock(),
        ), patch(
            "app.api.routes.dataforseo.get_dataforseo_usage_today",
            new=AsyncMock(return_value=Decimal("0")),
        ), patch(
            "app.api.routes.dataforseo.get_dataforseo_usage_month",
            new=AsyncMock(return_value=Decimal("0")),
        ):
            response = await dataforseo_routes.get_dataforseo_status(project_id, session)
        assert response.configured is False
        assert response.real_calls_enabled is False

    asyncio.run(run())


def test_status_real_calls_disabled_by_default() -> None:
    assert settings.dataforseo_enable_real_calls is False


def test_test_endpoint_blocks_when_real_calls_disabled() -> None:
    async def run() -> None:
        project_id = uuid4()
        session = AsyncMock()
        request = SimpleNamespace(
            test_type="search_volume",
            keyword="polline biologico",
            location_code=2380,
            language_code="it",
        )
        with patch(
            "app.api.routes.dataforseo.get_project_in_default_workspace",
            new=AsyncMock(),
        ), patch(
            "app.api.routes.dataforseo.run_dataforseo_sandbox_test",
            new=AsyncMock(side_effect=DataForSeoRealCallsDisabledError("DataForSEO real calls disabled.")),
        ):
            with pytest.raises(HTTPException) as exc:
                await dataforseo_routes.run_dataforseo_test_endpoint(project_id, request, session)
        assert exc.value.status_code == 409
        assert "real calls disabled" in str(exc.value.detail).lower()

    asyncio.run(run())


def test_budget_blocks_when_estimated_exceeds_single_limit() -> None:
    async def run() -> None:
        project_id = uuid4()
        session = AsyncMock()
        settings.dataforseo_enable_real_calls = True
        with pytest.raises(DataForSeoBudgetExceededError):
            await assert_dataforseo_budget_allows(session, project_id, 0.50)

    asyncio.run(run())


def test_usage_log_created_on_mocked_call() -> None:
    async def run() -> None:
        session = AsyncMock()
        session.flush = AsyncMock()
        project_id = uuid4()
        row = await record_dataforseo_usage(
            session,
            DataForSeoUsageLogInput(
                project_id=project_id,
                endpoint="/keywords_data/google_ads/search_volume/live",
                operation="search_volume",
                status="success",
                cost_usd=Decimal("0.075"),
                metadata_json={"keyword": "polline biologico"},
                response_summary={"itemsCount": 1},
            ),
        )
        session.add.assert_called_once()
        assert row.operation == "search_volume"
        assert row.cost_usd == Decimal("0.075")

    asyncio.run(run())


def test_estimate_does_not_make_http_calls() -> None:
    async def run() -> None:
        project_id = uuid4()
        session = AsyncMock()
        with patch("httpx.AsyncClient") as client_mock:
            result = await estimate_dataforseo_cost(
                session,
                project_id=project_id,
                mode="single_page",
            )
            client_mock.assert_not_called()
        assert result["estimatedCostUsd"] > 0
        assert result["estimatedCalls"]["searchVolume"] == 3

    asyncio.run(run())


def test_client_does_not_log_password(caplog: pytest.LogCaptureFixture) -> None:
    async def run() -> None:
        settings.dataforseo_login = "test-login"
        settings.dataforseo_password = "super-secret-password"
        settings.dataforseo_enable_real_calls = True

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "tasks": [{"cost": 0.05, "status_code": 20000, "result": []}],
        }

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_client):
            with caplog.at_level(logging.INFO):
                await post_dataforseo(
                    "/keywords_data/google_ads/search_volume/live",
                    [{"keywords": ["test"]}],
                )

        logged = "\n".join(record.message for record in caplog.records)
        assert "super-secret-password" not in logged

    asyncio.run(run())


def test_mock_response_cost_is_saved() -> None:
    async def run() -> None:
        project_id = uuid4()
        session = AsyncMock()
        session.flush = AsyncMock()
        settings.dataforseo_login = "login"
        settings.dataforseo_password = "password"
        settings.dataforseo_enable_real_calls = True

        mock_result = {
            "endpoint": "/keywords_data/google_ads/search_volume/live",
            "cost_usd": 0.08,
            "summary": {"itemsCount": 1, "keyword": "polline biologico"},
            "rawPreview": {"tasks": []},
        }

        with patch(
            "app.services.dataforseo.dataforseo_sandbox_service.safe_test_keyword_search_volume",
            new=AsyncMock(return_value=mock_result),
        ), patch(
            "app.services.dataforseo.dataforseo_sandbox_service.assert_dataforseo_budget_allows",
            new=AsyncMock(),
        ):
            result = await run_dataforseo_sandbox_test(
                session,
                project_id=project_id,
                test_type="search_volume",
                keyword="polline biologico",
                location_code=2380,
                language_code="it",
            )

        assert result["costUsd"] == 0.08
        session.add.assert_called_once()
        saved_row = session.add.call_args.args[0]
        assert float(saved_row.cost_usd) == 0.08

    asyncio.run(run())


def test_no_real_http_calls_in_tests() -> None:
    async def run() -> None:
        settings.dataforseo_login = "login"
        settings.dataforseo_password = "password"
        settings.dataforseo_enable_real_calls = True

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"tasks": [{"cost": 0.05, "result": []}]}
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_client) as client_ctor:
            await post_dataforseo("/keywords_data/google_ads/search_volume/live", [{"keywords": ["x"]}])
            client_ctor.assert_called_once()
            mock_client.post.assert_awaited_once()

    asyncio.run(run())
