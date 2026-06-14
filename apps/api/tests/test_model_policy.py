"""Tests for centralized AI model routing policy."""

from __future__ import annotations

import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.services.ai.ai_client import AiRequestMetadata
from app.services.ai.model_policy import (
    AiModelTier,
    resolve_ai_model,
)
from app.services.ai.usage_service import UsageLogInput, record_usage_log


def test_image_alt_tier_cheap() -> None:
    async def run() -> None:
        session = AsyncMock()
        session.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))
        )
        session.flush = AsyncMock()
        resolved = await resolve_ai_model(
            session,
            AiRequestMetadata(
                project_id=uuid4(),
                module="product_seo",
                operation="generate_field",
                context_profile="image_alt",
                operation_key="product_image_alt",
            ),
            project_id=uuid4(),
            context_profile="image_alt",
        )
        assert resolved.tier == AiModelTier.CHEAP.value
        assert resolved.max_output_tokens == 120

    asyncio.run(run())


def test_article_draft_tier_premium() -> None:
    async def run() -> None:
        session = AsyncMock()
        session.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))
        )
        session.flush = AsyncMock()
        resolved = await resolve_ai_model(
            session,
            AiRequestMetadata(
                project_id=uuid4(),
                module="article_generator",
                operation="generate_article",
                context_profile="article_draft",
                operation_key="article_draft_generation",
            ),
            project_id=uuid4(),
        )
        assert resolved.tier == AiModelTier.PREMIUM.value

    asyncio.run(run())


def test_record_usage_log_persists_model_tier() -> None:
    async def run() -> None:
        session = AsyncMock()
        session.flush = AsyncMock()
        project_id = uuid4()
        await record_usage_log(
            session,
            UsageLogInput(
                project_id=project_id,
                model="gpt-4o-mini",
                module="product_seo",
                operation="generate_field",
                status="success",
                model_tier="cheap",
                model_policy_source="project_setting",
                operation_key="product_image_alt",
                max_output_tokens=120,
                temperature=Decimal("0.30"),
            ),
        )
        added = session.add.call_args[0][0]
        assert added.model_tier == "cheap"
        assert added.operation_key == "product_image_alt"

    asyncio.run(run())
