"""Tests for AI model settings service and routing insights schema."""

from __future__ import annotations

import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.schemas.ai_usage import AiRoutingInsights
from app.services.ai.model_settings_service import (
    compute_guardrail_warnings,
    seed_default_settings,
)
from app.services.ai.operation_registry import get_operation


def test_routing_insights_snake_case_validates() -> None:
    payload = {
        "cost_by_tier": {"cheap": 0.01},
        "requests_by_tier": {"cheap": 2},
        "premium_on_cheap_profile_count": 0,
        "explicit_override_count": 0,
        "unconfigured_model_warnings": [],
        "schema_fallback_retry_count": 0,
    }
    model = AiRoutingInsights.model_validate(payload)
    dumped = model.model_dump(by_alias=True)
    assert dumped["costByTier"]["cheap"] == 0.01
    assert dumped["requestsByTier"]["cheap"] == 2


def test_critical_operation_cheap_warning() -> None:
    op = get_operation("article_draft_generation")
    assert op is not None
    warnings = compute_guardrail_warnings(op, model_tier="cheap", model_name="gpt-4o-mini")
    assert any("critica" in w for w in warnings)


def test_unknown_model_pricing_warning() -> None:
    op = get_operation("product_image_alt")
    assert op is not None
    warnings = compute_guardrail_warnings(op, model_tier="cheap", model_name="unknown-model-xyz-999")
    assert any("pricing" in w.lower() for w in warnings)


def test_seed_default_settings_creates_rows() -> None:
    async def run() -> None:
        session = AsyncMock()
        session.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))
        )
        session.flush = AsyncMock()
        created = await seed_default_settings(session, project_id=None, source="env_seed")
        assert created > 0
        assert session.add.call_count == created

    asyncio.run(run())
