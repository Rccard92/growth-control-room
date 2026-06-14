"""AI usage logging, pricing and budget tests."""

from __future__ import annotations

import asyncio
from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.core.datetime import (
    date_range_bounds_utc_naive,
    day_end_exclusive_utc_naive,
    day_start_utc_naive,
    to_utc_naive,
    utc_now_naive,
)
from app.services.ai.exceptions import AiBudgetExceededError
from app.services.ai.pricing import estimate_usage_cost
from app.services.ai.usage_service import (
    UsageLogInput,
    _apply_log_filters,
    check_budget_before_request,
    estimate_operation_cost,
    get_budget_status,
    get_usage_summary,
    list_usage_logs,
    record_usage_log,
    sum_project_spend,
)
from sqlalchemy import select

from app.models.ai_usage_log import AiUsageLog


def test_cost_estimate_configured() -> None:
    cost = estimate_usage_cost(
        "gpt-4o-mini",
        input_tokens=1000,
        output_tokens=500,
        cached_input_tokens=200,
    )
    assert cost is not None
    assert cost.total_cost > Decimal("0")
    assert cost.pricing_configured is True


def test_cost_null_missing_pricing() -> None:
    assert estimate_usage_cost("unknown-model-xyz", input_tokens=100, output_tokens=50) is None


def test_record_usage_log() -> None:
    async def run() -> None:
        session = AsyncMock()
        session.flush = AsyncMock()
        project_id = uuid4()
        row = await record_usage_log(
            session,
            UsageLogInput(
                project_id=project_id,
                model="gpt-4o-mini",
                module="product_seo",
                operation="generate_field",
                status="success",
                input_tokens=100,
                output_tokens=50,
                total_tokens=150,
                estimated_total_cost=Decimal("0.0001"),
            ),
        )
        session.add.assert_called_once()
        session.flush.assert_awaited_once()
        assert row.module == "product_seo"

    asyncio.run(run())


def test_summary_by_module_operation_day() -> None:
    async def run() -> None:
        project_id = uuid4()
        now = utc_now_naive()
        rows = [
            SimpleNamespace(
                estimated_total_cost=Decimal("0.01"),
                input_tokens=100,
                output_tokens=50,
                cached_input_tokens=10,
                status="success",
                module="blog_brief",
                operation="generate_brief",
                model="gpt-4o-mini",
                created_at=now,
            ),
            SimpleNamespace(
                estimated_total_cost=Decimal("0.02"),
                input_tokens=200,
                output_tokens=80,
                cached_input_tokens=0,
                status="error",
                module="product_seo",
                operation="generate_field",
                model="gpt-4o-mini",
                created_at=now,
            ),
        ]

        session = AsyncMock()
        scalars = MagicMock()
        scalars.all.return_value = rows
        session.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(return_value=scalars)))

        summary = await get_usage_summary(session, project_id)
        assert summary["totalRequests"] == 2
        assert summary["failedRequests"] == 1
        assert summary["successfulRequests"] == 1
        assert len(summary["byModule"]) == 2
        assert len(summary["byOperation"]) == 2
        assert len(summary["byDay"]) == 1

    asyncio.run(run())


def test_daily_budget_blocks_request() -> None:
    async def run() -> None:
        project_id = uuid4()
        session = AsyncMock()

        with (
            patch("app.services.ai.usage_service.settings") as mock_settings,
            patch(
                "app.services.ai.usage_service.sum_project_spend",
                new=AsyncMock(return_value=Decimal("10")),
            ),
        ):
            mock_settings.ai_daily_budget_usd = 5.0
            mock_settings.ai_monthly_budget_usd = None
            with pytest.raises(AiBudgetExceededError):
                await check_budget_before_request(session, project_id)

    asyncio.run(run())


def test_log_success_request_mock_openai() -> None:
    async def run() -> None:
        from app.services.ai.ai_client import AiRequestMetadata, generate_structured_json

        project_id = uuid4()
        mock_response = SimpleNamespace(
            id="resp_123",
            choices=[
                SimpleNamespace(message=SimpleNamespace(content='{"ok": true}')),
            ],
            usage=SimpleNamespace(
                prompt_tokens=100,
                completion_tokens=20,
                total_tokens=120,
                prompt_tokens_details=SimpleNamespace(cached_tokens=10),
                completion_tokens_details=None,
            ),
        )

        session_factory = MagicMock()
        session = AsyncMock()
        session.commit = AsyncMock()
        session.__aenter__ = AsyncMock(return_value=session)
        session.__aexit__ = AsyncMock(return_value=None)
        session_factory.return_value = session

        with (
            patch("app.services.ai.ai_client.is_openai_configured", return_value=True),
            patch("app.services.ai.ai_client._client") as mock_client_factory,
            patch("app.services.ai.ai_client.get_session_factory", return_value=session_factory),
            patch("app.services.ai.ai_client._persist_log", new=AsyncMock()) as mock_persist,
            patch("app.services.ai.ai_client.check_budget_before_request", new=AsyncMock()),
        ):
            client = AsyncMock()
            client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_client_factory.return_value = client

            result = await generate_structured_json(
                system_prompt="system",
                user_prompt="user",
                metadata=AiRequestMetadata(
                    project_id=project_id,
                    module="blog_brief",
                    operation="generate_brief",
                ),
            )
            assert result == {"ok": True}
            mock_persist.assert_awaited()

    asyncio.run(run())


def test_log_failed_request() -> None:
    async def run() -> None:
        from app.services.ai.ai_client import AiRequestMetadata, generate_structured_json
        from app.services.ai.exceptions import OpenAIRequestError
        from openai import OpenAIError

        project_id = uuid4()
        session_factory = MagicMock()
        session = AsyncMock()
        session.commit = AsyncMock()
        session.__aenter__ = AsyncMock(return_value=session)
        session.__aexit__ = AsyncMock(return_value=None)
        session_factory.return_value = session

        with (
            patch("app.services.ai.ai_client.is_openai_configured", return_value=True),
            patch("app.services.ai.ai_client._client") as mock_client_factory,
            patch("app.services.ai.ai_client.get_session_factory", return_value=session_factory),
            patch("app.services.ai.ai_client._persist_log", new=AsyncMock()) as mock_persist,
            patch("app.services.ai.ai_client.check_budget_before_request", new=AsyncMock()),
        ):
            client = AsyncMock()
            client.chat.completions.create = AsyncMock(side_effect=OpenAIError("timeout"))
            mock_client_factory.return_value = client

            with pytest.raises(OpenAIRequestError):
                await generate_structured_json(
                    system_prompt="s",
                    user_prompt="u",
                    metadata=AiRequestMetadata(
                        project_id=project_id,
                        module="product_seo",
                        operation="generate_field",
                    ),
                )
            mock_persist.assert_awaited()

    asyncio.run(run())


def test_estimate_operation_cost() -> None:
    async def run() -> None:
        project_id = uuid4()
        session = AsyncMock()
        session.execute = AsyncMock(
            return_value=MagicMock(one=MagicMock(return_value=(5, Decimal("0.02"))))
        )
        result = await estimate_operation_cost(
            session, project_id, operation="batch_brief_item", count=3
        )
        assert result["estimatedTotalCost"] == pytest.approx(0.06)
        assert result["basedOnRequests"] == 5

    asyncio.run(run())


def test_to_utc_naive_strips_tzinfo() -> None:
    aware = datetime(2026, 6, 13, 12, 0, 0, tzinfo=timezone.utc)
    naive = to_utc_naive(aware)
    assert naive is not None
    assert naive.tzinfo is None
    assert naive.hour == 12


def test_date_range_bounds_end_exclusive() -> None:
    start, end = date_range_bounds_utc_naive(date(2026, 6, 1), date(2026, 6, 3))
    assert start == day_start_utc_naive(date(2026, 6, 1))
    assert end == day_end_exclusive_utc_naive(date(2026, 6, 3))
    assert end == day_start_utc_naive(date(2026, 6, 4))


def test_apply_log_filters_use_naive_datetimes() -> None:
    stmt = select(AiUsageLog)
    filtered = _apply_log_filters(
        stmt,
        project_id=uuid4(),
        start_date=date(2026, 6, 1),
        end_date=date(2026, 6, 10),
        module=None,
        operation=None,
        model=None,
        status=None,
    )
    compiled = str(filtered.compile(compile_kwargs={"literal_binds": True}))
    assert "tzinfo" not in compiled


def test_get_budget_status_empty_logs() -> None:
    async def run() -> None:
        project_id = uuid4()
        session = AsyncMock()
        with patch(
            "app.services.ai.usage_service.sum_project_spend",
            new=AsyncMock(return_value=Decimal("0")),
        ) as mock_sum:
            result = await get_budget_status(session, project_id)
            assert result["dailySpent"] == 0.0
            assert result["monthlySpent"] == 0.0
            assert result["blocked"] is False
            assert mock_sum.await_count == 2
            for call in mock_sum.await_args_list:
                since = call.kwargs["since"]
                assert since.tzinfo is None

    asyncio.run(run())


def test_sum_project_spend_converts_aware_since() -> None:
    async def run() -> None:
        project_id = uuid4()
        session = AsyncMock()
        session.execute = AsyncMock(
            return_value=MagicMock(scalar_one=MagicMock(return_value=0))
        )
        aware_since = datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc)
        await sum_project_spend(session, project_id, since=aware_since)
        session.execute.assert_awaited_once()

    asyncio.run(run())


def test_get_usage_summary_with_date_range() -> None:
    async def run() -> None:
        project_id = uuid4()
        session = AsyncMock()
        scalars = MagicMock()
        scalars.all.return_value = []
        session.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(return_value=scalars)))

        summary = await get_usage_summary(
            session,
            project_id,
            start_date=date(2026, 6, 1),
            end_date=date(2026, 6, 13),
        )
        assert summary["totalRequests"] == 0
        assert summary["totalEstimatedCost"] == 0.0

    asyncio.run(run())


def test_list_usage_logs_with_date_range() -> None:
    async def run() -> None:
        project_id = uuid4()
        session = AsyncMock()
        count_result = MagicMock(scalar_one=MagicMock(return_value=0))
        list_scalars = MagicMock()
        list_scalars.all.return_value = []
        list_result = MagicMock(scalars=MagicMock(return_value=list_scalars))
        session.execute = AsyncMock(side_effect=[count_result, list_result])

        rows, total = await list_usage_logs(
            session,
            project_id,
            start_date=date(2026, 6, 1),
            end_date=date(2026, 6, 13),
            limit=10,
            offset=0,
        )
        assert rows == []
        assert total == 0

    asyncio.run(run())
