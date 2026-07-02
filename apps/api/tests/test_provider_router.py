"""Tests for AI provider router."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.services.ai.ai_client import AiRequestMetadata
from app.services.ai.provider_router import generate_structured_json_with_provider


def _metadata() -> AiRequestMetadata:
    return AiRequestMetadata(
        project_id=uuid4(),
        module="seo_skills",
        operation="run_skill",
        operation_key="seo_audit",
        context_profile="generic",
    )


def test_provider_router_uses_openai_when_provider_openai() -> None:
    async def run() -> None:
        metadata = _metadata()
        with patch(
            "app.services.ai.provider_router.generate_structured_json",
            new_callable=AsyncMock,
            return_value={"ok": True},
        ) as mock_openai:
            result = await generate_structured_json_with_provider(
                provider="openai",
                system_prompt="system",
                user_prompt="user",
                metadata=metadata,
                timeout=45.0,
                model="gpt-4o-mini",
                prompt_cache_key="cache-key",
            )

        assert result == {"ok": True}
        mock_openai.assert_awaited_once_with(
            system_prompt="system",
            user_prompt="user",
            metadata=metadata,
            timeout=45.0,
            model="gpt-4o-mini",
            prompt_cache_key="cache-key",
            json_schema=None,
            json_schema_name=None,
        )

    asyncio.run(run())


def test_provider_router_uses_claude_when_provider_claude() -> None:
    async def run() -> None:
        metadata = _metadata()
        with patch(
            "app.services.ai.provider_router.generate_claude_structured_json",
            new_callable=AsyncMock,
            return_value={"score": 90},
        ) as mock_claude:
            result = await generate_structured_json_with_provider(
                provider="claude",
                system_prompt="system",
                user_prompt="user",
                metadata=metadata,
                timeout=30.0,
                model="claude-3-5-sonnet-latest",
                prompt_cache_key="ignored",
            )

        assert result == {"score": 90}
        mock_claude.assert_awaited_once_with(
            system_prompt="system",
            user_prompt="user",
            metadata=metadata,
            timeout=30.0,
            model="claude-3-5-sonnet-latest",
        )

    asyncio.run(run())


def test_provider_router_defaults_to_openai_when_provider_none() -> None:
    async def run() -> None:
        metadata = _metadata()
        with patch(
            "app.services.ai.provider_router.generate_structured_json",
            new_callable=AsyncMock,
            return_value={"ok": True},
        ) as mock_openai:
            await generate_structured_json_with_provider(
                provider=None,
                system_prompt="system",
                user_prompt="user",
                metadata=metadata,
            )

        mock_openai.assert_awaited_once()

    asyncio.run(run())


def test_provider_router_raises_on_unknown_provider() -> None:
    async def run() -> None:
        with pytest.raises(ValueError, match="Unsupported AI provider: unknown"):
            await generate_structured_json_with_provider(
                provider="unknown",
                system_prompt="system",
                user_prompt="user",
                metadata=_metadata(),
            )

    asyncio.run(run())


def test_provider_router_passes_json_schema_to_openai() -> None:
    async def run() -> None:
        metadata = _metadata()
        schema = {"type": "object", "properties": {"ok": {"type": "boolean"}}, "required": ["ok"]}
        with patch(
            "app.services.ai.provider_router.generate_structured_json",
            new_callable=AsyncMock,
            return_value={"ok": True},
        ) as mock_openai:
            await generate_structured_json_with_provider(
                provider="openai",
                system_prompt="system",
                user_prompt="user",
                metadata=metadata,
                json_schema=schema,
                json_schema_name="seo_skill_output",
            )

        mock_openai.assert_awaited_once_with(
            system_prompt="system",
            user_prompt="user",
            metadata=metadata,
            timeout=60.0,
            model=None,
            prompt_cache_key=None,
            json_schema=schema,
            json_schema_name="seo_skill_output",
        )

    asyncio.run(run())


def test_provider_router_ignores_json_schema_for_claude() -> None:
    async def run() -> None:
        metadata = _metadata()
        schema = {"type": "object", "properties": {"ok": {"type": "boolean"}}, "required": ["ok"]}
        with patch(
            "app.services.ai.provider_router.generate_claude_structured_json",
            new_callable=AsyncMock,
            return_value={"ok": True},
        ) as mock_claude:
            await generate_structured_json_with_provider(
                provider="claude",
                system_prompt="system",
                user_prompt="user",
                metadata=metadata,
                json_schema=schema,
                json_schema_name="seo_skill_output",
            )

        mock_claude.assert_awaited_once_with(
            system_prompt="system",
            user_prompt="user",
            metadata=metadata,
            timeout=60.0,
            model=None,
        )

    asyncio.run(run())
