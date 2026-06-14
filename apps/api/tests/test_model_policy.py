"""Tests for centralized AI model routing policy."""

from __future__ import annotations

import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.services.ai.ai_client import AiRequestMetadata
from app.services.ai.model_policy import (
    AiModelTier,
    resolve_ai_model,
)
from app.services.ai.usage_service import UsageLogInput, record_usage_log


def test_image_alt_tier_cheap() -> None:
    resolved = resolve_ai_model(
        AiRequestMetadata(
            project_id=uuid4(),
            module="product_seo",
            operation="generate_field",
            context_profile="image_alt",
        ),
        context_profile="image_alt",
    )
    assert resolved.tier == AiModelTier.CHEAP.value
    assert resolved.max_output_tokens == 120
    assert resolved.temperature == pytest.approx(0.3)


def test_product_seo_field_tier_cheap() -> None:
    resolved = resolve_ai_model(
        AiRequestMetadata(
            project_id=uuid4(),
            module="product_seo",
            operation="generate_field",
            context_profile="product_seo_field",
        ),
    )
    assert resolved.tier == AiModelTier.CHEAP.value


def test_product_seo_full_tier_standard() -> None:
    resolved = resolve_ai_model(
        AiRequestMetadata(
            project_id=uuid4(),
            module="product_seo",
            operation="generate_proposal",
            context_profile="product_seo_full",
        ),
    )
    assert resolved.tier == AiModelTier.STANDARD.value
    assert resolved.max_output_tokens == 2500


def test_blog_brief_tier_standard() -> None:
    resolved = resolve_ai_model(
        AiRequestMetadata(
            project_id=uuid4(),
            module="blog_brief",
            operation="generate_brief",
            context_profile="blog_brief",
        ),
    )
    assert resolved.tier == AiModelTier.STANDARD.value


def test_article_draft_tier_premium() -> None:
    resolved = resolve_ai_model(
        AiRequestMetadata(
            project_id=uuid4(),
            module="article_generator",
            operation="generate_article",
            context_profile="article_draft",
        ),
    )
    assert resolved.tier == AiModelTier.PREMIUM.value
    assert resolved.max_output_tokens == 8000


def test_compliance_review_not_cheap() -> None:
    resolved = resolve_ai_model(
        AiRequestMetadata(
            project_id=uuid4(),
            module="brand_intelligence",
            operation="compliance_review",
            context_profile="compliance_review",
        ),
    )
    assert resolved.tier != AiModelTier.CHEAP.value


def test_unknown_profile_fallback_standard() -> None:
    resolved = resolve_ai_model(
        AiRequestMetadata(
            project_id=uuid4(),
            module="custom",
            operation="custom_op",
            context_profile="unknown_profile_xyz",
        ),
    )
    assert resolved.tier == AiModelTier.STANDARD.value
    assert resolved.policy_source == "context_profile"


def test_explicit_override_with_warning(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.services.ai.model_policy.settings.ai_allow_model_override",
        True,
    )
    monkeypatch.setattr(
        "app.services.ai.model_policy.settings.openai_model_premium",
        "gpt-4o",
    )
    resolved = resolve_ai_model(
        AiRequestMetadata(
            project_id=uuid4(),
            module="product_seo",
            operation="generate_field",
            context_profile="image_alt",
        ),
        requested_model="gpt-4o",
    )
    assert resolved.policy_source == "explicit_override"
    assert resolved.model == "gpt-4o"
    assert resolved.warning is not None


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
                model_policy_source="context_profile",
                max_output_tokens=120,
                temperature=Decimal("0.30"),
            ),
        )
        added = session.add.call_args[0][0]
        assert added.model_tier == "cheap"
        assert added.model_policy_source == "context_profile"
        assert added.max_output_tokens == 120

    asyncio.run(run())
