"""Editorial plan service rule-based generation tests."""

import asyncio
from datetime import date
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.content_seo_editorial import EditorialPlanGenerateRequest
from app.services.content.editorial_plan_service import (
    _build_title,
    _initial_status,
    _iter_dates,
    generate_editorial_calendar,
)


def _base_request(**overrides) -> EditorialPlanGenerateRequest:
    payload = {
        "startDate": "2026-06-01",
        "endDate": "2026-06-14",
        "frequency": "weekly",
        "preferredWeekdays": ["monday"],
        "contentTypes": ["educational_article", "recipe"],
        "objectives": ["seo_traffic"],
        "commercialIntensity": "balanced",
    }
    payload.update(overrides)
    return EditorialPlanGenerateRequest.model_validate(payload)


def test_iter_dates_daily() -> None:
    request = _base_request(frequency="daily", endDate="2026-06-03")
    dates = _iter_dates(request)
    assert dates == [date(2026, 6, 1), date(2026, 6, 2), date(2026, 6, 3)]


def test_iter_dates_every_2_days() -> None:
    request = _base_request(frequency="every_2_days", endDate="2026-06-07")
    dates = _iter_dates(request)
    assert dates == [date(2026, 6, 1), date(2026, 6, 3), date(2026, 6, 5), date(2026, 6, 7)]


def test_iter_dates_custom_weekdays() -> None:
    request = _base_request(
        frequency="custom",
        preferredWeekdays=["tuesday", "thursday"],
        endDate="2026-06-10",
    )
    dates = _iter_dates(request)
    assert date(2026, 6, 2) in dates
    assert date(2026, 6, 4) in dates
    assert date(2026, 6, 3) not in dates


def test_iter_dates_twice_weekly_with_weekdays() -> None:
    request = _base_request(
        frequency="twice_weekly",
        preferredWeekdays=["tuesday", "friday"],
        endDate="2026-06-07",
    )
    dates = _iter_dates(request)
    assert date(2026, 6, 2) in dates
    assert date(2026, 6, 5) in dates
    assert all(d.weekday() in {1, 4} for d in dates)


def test_request_validation_twice_weekly_without_weekdays() -> None:
    with pytest.raises(ValidationError, match="giorno preferito"):
        EditorialPlanGenerateRequest.model_validate(
            {
                "startDate": "2026-06-01",
                "endDate": "2026-06-07",
                "frequency": "twice_weekly",
                "contentTypes": ["recipe"],
                "objective": "seo_traffic",
                "commercialIntensity": "soft",
            }
        )


def test_request_validation_end_before_start() -> None:
    with pytest.raises(ValidationError, match="data fine"):
        _base_request(startDate="2026-06-10", endDate="2026-06-01")


def test_request_validation_empty_content_types() -> None:
    with pytest.raises(ValidationError, match="tipologia"):
        _base_request(contentTypes=[])


def test_request_validation_custom_without_weekdays() -> None:
    with pytest.raises(ValidationError, match="giorno preferito"):
        _base_request(frequency="custom", preferredWeekdays=[])


def test_initial_status_with_keywords() -> None:
    request = _base_request(primaryKeywords=["olio evo"])
    assert _initial_status(request) == "brief_pending"


def test_initial_status_without_keywords() -> None:
    request = _base_request()
    assert _initial_status(request) == "idea"


def test_build_title_no_openai_placeholder() -> None:
    title = _build_title(
        "product_guide",
        keyword="skincare naturale",
        product_title="Crema viso",
        brand_name="Acme",
        planned=date(2026, 6, 15),
        index=0,
    )
    assert "Crema viso" in title
    assert title == "Guida completa: Crema viso"


def test_build_title_seasonal_month_italian() -> None:
    title = _build_title(
        "seasonal_article",
        keyword="estate",
        product_title=None,
        brand_name=None,
        planned=date(2026, 6, 1),
        index=0,
    )
    assert "Giugno" in title


def test_generate_editorial_calendar_dry_run() -> None:
    request = _base_request(
        frequency="daily",
        endDate="2026-06-03",
        primaryKeywords=["keyword test"],
        contentTypes=["educational_article", "recipe"],
    )
    project_id = uuid4()
    mock_session = AsyncMock()

    async def run():
        with (
            patch(
                "app.services.content.editorial_plan_service._load_products",
                new=AsyncMock(return_value=[]),
            ),
            patch(
                "app.services.content.editorial_plan_service._brand_name",
                new=AsyncMock(return_value="Brand Test"),
            ),
        ):
            rows = await generate_editorial_calendar(
                mock_session,
                project_id,
                request,
                dry_run=True,
            )
            assert len(rows) == 3
            assert rows[0].content_type == "educational_article"
            assert rows[1].content_type == "recipe"
            assert rows[0].status == "brief_pending"
            assert rows[0].id is not None
            mock_session.commit.assert_not_called()

    asyncio.run(run())


def test_generate_editorial_calendar_mixed_content_types_rotation() -> None:
    request = _base_request(
        frequency="daily",
        endDate="2026-06-04",
        contentTypes=["educational_article", "product_guide", "recipe"],
    )
    project_id = uuid4()
    mock_session = AsyncMock()

    async def run():
        with (
            patch(
                "app.services.content.editorial_plan_service._load_products",
                new=AsyncMock(return_value=[]),
            ),
            patch(
                "app.services.content.editorial_plan_service._brand_name",
                new=AsyncMock(return_value=None),
            ),
        ):
            rows = await generate_editorial_calendar(
                mock_session,
                project_id,
                request,
                dry_run=True,
            )
            types = [row.content_type for row in rows]
            assert types == ["educational_article", "product_guide", "recipe", "educational_article"]

    asyncio.run(run())


def test_objectives_normalization_from_legacy_objective() -> None:
    request = EditorialPlanGenerateRequest.model_validate(
        {
            "startDate": "2026-06-01",
            "endDate": "2026-06-03",
            "frequency": "daily",
            "contentTypes": ["recipe"],
            "objective": "push_products",
            "commercialIntensity": "balanced",
        }
    )
    assert request.objectives == ["push_products"]


def test_objectives_default_when_empty() -> None:
    request = EditorialPlanGenerateRequest.model_validate(
        {
            "startDate": "2026-06-01",
            "endDate": "2026-06-03",
            "frequency": "daily",
            "contentTypes": ["recipe"],
            "commercialIntensity": "balanced",
        }
    )
    assert request.objectives == ["education"]


def test_generate_editorial_calendar_objectives_rotation() -> None:
    request = _base_request(
        frequency="daily",
        endDate="2026-06-04",
        objectives=["education", "seo_traffic", "answer_objections"],
    )
    project_id = uuid4()
    mock_session = AsyncMock()

    async def run():
        with (
            patch(
                "app.services.content.editorial_plan_service._load_products",
                new=AsyncMock(return_value=[]),
            ),
            patch(
                "app.services.content.editorial_plan_service._brand_name",
                new=AsyncMock(return_value=None),
            ),
        ):
            rows = await generate_editorial_calendar(
                mock_session,
                project_id,
                request,
                dry_run=True,
            )
            objectives = [row.objective for row in rows]
            assert objectives == [
                "education",
                "seo_traffic",
                "answer_objections",
                "education",
            ]

    asyncio.run(run())


def test_generate_editorial_calendar_without_keywords() -> None:
    request = _base_request(
        frequency="daily",
        endDate="2026-06-02",
        primaryKeywords=[],
    )
    project_id = uuid4()
    mock_session = AsyncMock()

    async def run():
        with (
            patch(
                "app.services.content.editorial_plan_service._load_products",
                new=AsyncMock(return_value=[]),
            ),
            patch(
                "app.services.content.editorial_plan_service._brand_name",
                new=AsyncMock(return_value=None),
            ),
        ):
            rows = await generate_editorial_calendar(
                mock_session,
                project_id,
                request,
                dry_run=True,
            )
            assert len(rows) == 2
            assert rows[0].primary_keyword is None
            assert rows[0].status == "idea"

    asyncio.run(run())
