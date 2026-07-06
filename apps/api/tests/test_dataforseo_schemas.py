"""DataForSEO schema validation tests."""

from __future__ import annotations

import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://test:test@localhost:5432/test",
)

import asyncio
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.schemas.dataforseo import (
    DataForSeoEstimateRequest,
    DataForSeoTestRequest,
    DataForSeoTestResponse,
)
from app.services.dataforseo.exceptions import DataForSeoRealCallsDisabledError
from app.api.routes import dataforseo as dataforseo_routes


def test_test_request_accepts_camel_case() -> None:
    request = DataForSeoTestRequest.model_validate(
        {
            "testType": "search_volume",
            "keyword": "polline biologico",
            "locationCode": 2380,
            "languageCode": "it",
        }
    )

    assert request.test_type == "search_volume"
    assert request.keyword == "polline biologico"
    assert request.location_code == 2380
    assert request.language_code == "it"


def test_test_request_accepts_snake_case() -> None:
    request = DataForSeoTestRequest.model_validate(
        {
            "test_type": "search_volume",
            "keyword": "polline biologico",
            "location_code": 2380,
            "language_code": "it",
        }
    )

    assert request.test_type == "search_volume"
    assert request.keyword == "polline biologico"
    assert request.location_code == 2380
    assert request.language_code == "it"


def test_estimate_request_accepts_camel_case() -> None:
    run_id = uuid4()
    request = DataForSeoEstimateRequest.model_validate(
        {
            "mode": "single_page",
            "runId": str(run_id),
            "seedQueriesPerPage": 3,
            "keywordIdeasPerSeed": 10,
            "serpQueriesPerPage": 1,
        }
    )

    assert request.mode == "single_page"
    assert request.run_id == run_id
    assert request.seed_queries_per_page == 3
    assert request.keyword_ideas_per_seed == 10
    assert request.serp_queries_per_page == 1


def test_test_response_serializes_camel_case() -> None:
    response = DataForSeoTestResponse(
        test_type="search_volume_batch",
        keyword="polline biologico",
        keywords=["polline biologico", "miele di eucalipto"],
        cost_usd=0.18,
        average_cost_per_keyword_usd=0.09,
        endpoints=["/keywords_data/google_ads/search_volume/live"],
        response_summary={"keywordCount": 2},
        raw_preview={"truncated": True},
    )

    dumped = response.model_dump(by_alias=True)

    assert dumped["testType"] == "search_volume_batch"
    assert dumped["keywords"] == ["polline biologico", "miele di eucalipto"]
    assert dumped["averageCostPerKeywordUsd"] == 0.09
    assert dumped["costUsd"] == 0.18


def test_camel_case_request_hits_409_not_422() -> None:
    async def run() -> None:
        project_id = uuid4()
        session = AsyncMock()
        request = DataForSeoTestRequest.model_validate(
            {
                "testType": "search_volume",
                "keyword": "polline biologico",
                "locationCode": 2380,
                "languageCode": "it",
            }
        )
        with patch(
            "app.api.routes.dataforseo.get_project_in_default_workspace",
            new=AsyncMock(),
        ), patch(
            "app.api.routes.dataforseo.run_dataforseo_sandbox_test",
            new=AsyncMock(
                side_effect=DataForSeoRealCallsDisabledError("DataForSEO real calls disabled.")
            ),
        ):
            with pytest.raises(HTTPException) as exc:
                await dataforseo_routes.run_dataforseo_test_endpoint(
                    project_id,
                    request,
                    session,
                )
        assert exc.value.status_code == 409
        assert "real calls disabled" in str(exc.value.detail).lower()

    asyncio.run(run())
