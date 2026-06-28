"""Tests for editorial item AI usage endpoint and helpers."""

import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.services.content.editorial_ai_usage_service import (
    build_ai_generation_snapshot_from_log,
    get_editorial_item_ai_usage,
)


def _make_log(**overrides):
    defaults = {
        "id": uuid4(),
        "model": "gpt-5.4",
        "model_tier": "premium",
        "operation_key": "blog_brief_generation",
        "context_profile": "blog_brief",
        "estimated_total_cost": Decimal("0.012"),
        "input_tokens": 1200,
        "output_tokens": 800,
        "created_at": datetime(2026, 6, 14, 18, 42, tzinfo=timezone.utc),
        "status": "success",
        "error_message": None,
        "context_hash": "abc123",
        "prompt_hash": "def456",
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_build_ai_generation_snapshot_from_log() -> None:
    log = _make_log()
    snap = build_ai_generation_snapshot_from_log(log)
    assert snap["model"] == "gpt-5.4"
    assert snap["operation_key"] == "blog_brief_generation"
    assert snap["estimated_total_cost"] == 0.012
    assert snap["generator_version"] == "0.5.14-alpha"


def test_build_ai_generation_snapshot_null_cost() -> None:
    log = _make_log(estimated_total_cost=None)
    snap = build_ai_generation_snapshot_from_log(log)
    assert snap["estimated_total_cost"] is None


def test_get_editorial_item_ai_usage_no_logs() -> None:
    project_id = uuid4()
    item_id = uuid4()
    mock_session = AsyncMock()

    async def run() -> None:
        with patch(
            "app.services.content.editorial_ai_usage_service._fetch_latest_log",
            new=AsyncMock(return_value=None),
        ):
            mock_session.execute = AsyncMock(
                return_value=SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: []))
            )
            result = await get_editorial_item_ai_usage(mock_session, project_id, item_id)
            assert result.brief is None
            assert result.article is None
            assert result.logs == []

    asyncio.run(run())


def test_get_editorial_item_ai_usage_with_brief_log() -> None:
    project_id = uuid4()
    item_id = uuid4()
    mock_session = AsyncMock()
    brief_log = _make_log()

    async def run() -> None:
        fetch_mock = AsyncMock(side_effect=[brief_log, None])
        with patch(
            "app.services.content.editorial_ai_usage_service._fetch_latest_log",
            new=fetch_mock,
        ):
            mock_session.execute = AsyncMock(
                return_value=SimpleNamespace(
                    scalars=lambda: SimpleNamespace(all=lambda: [brief_log])
                )
            )
            result = await get_editorial_item_ai_usage(mock_session, project_id, item_id)
            assert result.brief is not None
            assert result.brief.model == "gpt-5.4"
            assert result.brief.operation_key == "blog_brief_generation"
            assert result.brief.estimated_total_cost == 0.012
            assert result.article is None

    asyncio.run(run())
