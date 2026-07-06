"""Tests for Keyword Intelligence cost estimation."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.services.dataforseo.dataforseo_cost_estimator import (
    compute_keyword_intelligence_cost,
    compute_search_volume_batch_cost_usd,
    estimate_keyword_intelligence_page_cost,
    resolve_keyword_intelligence_unit_costs,
)


def test_compute_keyword_intelligence_cost_with_observed_units() -> None:
    unit_costs = {
        "search_volume_batch": 0.09,
        "keyword_ideas": 0.09,
        "serp": 0.002,
    }
    result = compute_keyword_intelligence_cost(
        seed_queries=10,
        keyword_ideas_seeds=1,
        serp_keywords=3,
        unit_costs=unit_costs,
        estimate_source="observed",
    )

    assert result["totalUsd"] == 0.186
    assert result["totalUsd"] != 0.996
    assert result["breakdown"]["searchVolumeBatches"] == 1
    assert result["breakdown"]["searchVolumeUsd"] == 0.09
    assert result["estimateSource"] == "observed"


def test_search_volume_estimated_per_batch_not_per_keyword() -> None:
    unit_costs = {
        "search_volume_batch": 0.09,
        "keyword_ideas": 0.09,
        "serp": 0.002,
    }

    ten_seed = compute_keyword_intelligence_cost(
        seed_queries=10,
        keyword_ideas_seeds=0,
        serp_keywords=0,
        unit_costs=unit_costs,
        estimate_source="observed",
    )
    eleven_seed = compute_keyword_intelligence_cost(
        seed_queries=11,
        keyword_ideas_seeds=0,
        serp_keywords=0,
        unit_costs=unit_costs,
        estimate_source="observed",
    )

    assert ten_seed["breakdown"]["searchVolumeBatches"] == 1
    assert eleven_seed["breakdown"]["searchVolumeBatches"] == 2
    assert ten_seed["breakdown"]["searchVolumeUsd"] == 0.09
    assert eleven_seed["breakdown"]["searchVolumeUsd"] == 0.18


def test_search_volume_twenty_seeds_uses_two_batches() -> None:
    batches, cost = compute_search_volume_batch_cost_usd(
        seed_queries=20,
        batch_unit_cost=0.09,
    )
    assert batches == 2
    assert cost == 0.18


def test_resolve_unit_costs_uses_fallback_without_logs() -> None:
    async def run() -> None:
        session = AsyncMock()
        with patch(
            "app.services.dataforseo.dataforseo_cost_estimator.average_cost_by_operation",
            new=AsyncMock(return_value={}),
        ):
            unit_costs, has_observed = await resolve_keyword_intelligence_unit_costs(
                session,
                uuid4(),
            )

        assert has_observed is False
        assert unit_costs["search_volume_batch"] == 0.09
        assert unit_costs["keyword_ideas"] == 0.09
        assert unit_costs["serp"] == 0.002

    asyncio.run(run())


def test_estimate_page_cost_uses_observed_logs() -> None:
    async def run() -> None:
        project_id = uuid4()
        session = AsyncMock()
        with patch(
            "app.services.dataforseo.dataforseo_cost_estimator.average_cost_by_operation",
            new=AsyncMock(
                return_value={
                    "search_volume_batch": 0.09,
                    "keyword_ideas": 0.09,
                    "serp": 0.002,
                }
            ),
        ):
            result = await estimate_keyword_intelligence_page_cost(
                session,
                project_id,
                seed_queries=10,
                keyword_ideas_seeds=1,
                serp_keywords=3,
            )

        assert result["totalUsd"] == 0.186
        assert result["estimateSource"] == "observed"

    asyncio.run(run())


def test_estimate_page_cost_fallback_without_logs() -> None:
    async def run() -> None:
        session = AsyncMock()
        with patch(
            "app.services.dataforseo.dataforseo_cost_estimator.average_cost_by_operation",
            new=AsyncMock(return_value={}),
        ):
            result = await estimate_keyword_intelligence_page_cost(
                session,
                uuid4(),
                seed_queries=10,
                keyword_ideas_seeds=1,
                serp_keywords=3,
            )

        assert result["totalUsd"] == 0.186
        assert result["estimateSource"] == "fallback"

    asyncio.run(run())


def test_keyword_intelligence_budget_allows_correct_estimate() -> None:
    async def run() -> None:
        from decimal import Decimal

        from app.core.config import settings
        from app.services.dataforseo.dataforseo_budget import assert_dataforseo_budget_allows
        from app.services.dataforseo.exceptions import DataForSeoBudgetExceededError

        project_id = uuid4()
        session = AsyncMock()
        settings.dataforseo_enable_real_calls = True
        settings.dataforseo_single_run_limit_usd = 1.0

        with (
            patch(
                "app.services.dataforseo.dataforseo_budget.get_dataforseo_usage_today",
                new=AsyncMock(return_value=Decimal("0")),
            ),
            patch(
                "app.services.dataforseo.dataforseo_budget.get_dataforseo_usage_month",
                new=AsyncMock(return_value=Decimal("0")),
            ),
        ):
            await assert_dataforseo_budget_allows(session, project_id, 0.186)

            settings.dataforseo_single_run_limit_usd = 0.10
            with pytest.raises(DataForSeoBudgetExceededError):
                await assert_dataforseo_budget_allows(session, project_id, 0.186)

            with pytest.raises(DataForSeoBudgetExceededError):
                await assert_dataforseo_budget_allows(session, project_id, 0.996)

    asyncio.run(run())
