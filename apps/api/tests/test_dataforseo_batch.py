"""DataForSEO batch search volume tests."""

from __future__ import annotations

import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://test:test@localhost:5432/test",
)

import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.schemas.dataforseo import DataForSeoTestRequest
from app.services.dataforseo.dataforseo_cost_estimator import estimate_dataforseo_cost
from app.services.dataforseo.dataforseo_sandbox_service import run_dataforseo_sandbox_test
from app.services.dataforseo.keyword_utils import resolve_search_volume_keywords
from app.services.dataforseo.search_volume_normalizer import (
    normalize_search_volume_batch_response,
    normalize_search_volume_result,
)


def test_resolve_keywords_dedup() -> None:
    resolved = resolve_search_volume_keywords(
        keyword="",
        keywords=["A", "a", " B ", "B", "c"],
    )
    assert resolved == ["A", "B", "c"]


def test_batch_blocks_more_than_10() -> None:
    with pytest.raises(ValueError, match="Massimo 10"):
        resolve_search_volume_keywords(
            keyword="",
            keywords=[f"kw-{index}" for index in range(11)],
        )


def test_batch_accepts_5_keywords() -> None:
    request = DataForSeoTestRequest.model_validate(
        {
            "testType": "search_volume_batch",
            "keywords": ["a", "b", "c", "d", "e"],
            "locationCode": 2380,
            "languageCode": "it",
        }
    )
    assert request.test_type == "search_volume_batch"
    assert request.keywords == ["a", "b", "c", "d", "e"]


def test_normalize_trend_stable() -> None:
    row = normalize_search_volume_result(
        {
            "keyword": "test",
            "search_volume": 100,
            "monthly_searches": [
                {"year": 2025, "month": 1, "search_volume": 100},
                {"year": 2025, "month": 2, "search_volume": 105},
            ],
        }
    )
    assert row["trend"]["direction"] == "stable"


def test_response_summary_average_cost() -> None:
    summary = normalize_search_volume_batch_response(
        {
            "cost_usd": 0.45,
            "tasks": [
                {
                    "result": [
                        {"keyword": "a", "search_volume": 10},
                        {"keyword": "b", "search_volume": 20},
                    ]
                }
            ],
        },
        ["a", "b"],
    )
    assert summary["averageCostPerKeywordUsd"] == 0.225
    assert summary["keywordCount"] == 2


def test_usage_log_items_count() -> None:
    async def run() -> None:
        project_id = uuid4()
        session = AsyncMock()
        session.flush = AsyncMock()

        mock_result = {
            "endpoint": "/keywords_data/google_ads/search_volume/live",
            "cost_usd": 0.45,
            "summary": {
                "keywordCount": 5,
                "averageCostPerKeywordUsd": 0.09,
                "results": [],
            },
            "rawPreview": {"tasks": []},
        }

        with patch(
            "app.services.dataforseo.dataforseo_sandbox_service.safe_test_keyword_search_volume_batch",
            new=AsyncMock(return_value=mock_result),
        ), patch(
            "app.services.dataforseo.dataforseo_sandbox_service.assert_dataforseo_budget_allows",
            new=AsyncMock(),
        ), patch(
            "app.services.dataforseo.dataforseo_sandbox_service.estimate_search_volume_batch_cost",
            new=AsyncMock(return_value=0.45),
        ):
            await run_dataforseo_sandbox_test(
                session,
                project_id=project_id,
                test_type="search_volume_batch",
                keyword="",
                keywords=["a", "b", "c", "d", "e"],
                location_code=2380,
                language_code="it",
            )

        saved_row = session.add.call_args.args[0]
        assert saved_row.items_count == 5
        assert saved_row.operation == "search_volume_batch"

    asyncio.run(run())


def test_estimator_uses_observed_costs() -> None:
    async def run() -> None:
        project_id = uuid4()
        session = AsyncMock()
        with patch(
            "app.services.dataforseo.dataforseo_cost_estimator.observed_unit_costs",
            new=AsyncMock(
                return_value={
                    "search_volume": 0.09,
                    "search_volume_batch": 0.09,
                    "keyword_ideas": None,
                    "serp": None,
                }
            ),
        ):
            result = await estimate_dataforseo_cost(
                session,
                project_id=project_id,
                mode="single_page",
            )

        assert result["estimateSource"] == "observed"
        assert result["observedUnitCosts"]["searchVolume"] == 0.09
        assert result["estimatedCostUsd"] == round(3 * 0.09 + 3 * 0.10 + 1 * 0.10, 4)

    asyncio.run(run())


def test_raw_preview_truncated() -> None:
    async def run() -> None:
        from app.services.dataforseo.dataforseo_client import safe_test_keyword_search_volume_batch

        huge_payload = {"tasks": [{"result": [{"keyword": "x", "data": "z" * 5000}]}]}
        with patch(
            "app.services.dataforseo.dataforseo_client.post_dataforseo",
            new=AsyncMock(return_value={**huge_payload, "cost_usd": 0.09, "raw": huge_payload}),
        ):
            result = await safe_test_keyword_search_volume_batch(["x"])

        assert result.get("rawPreview") is not None

    asyncio.run(run())
