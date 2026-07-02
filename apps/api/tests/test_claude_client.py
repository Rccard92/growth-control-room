"""Tests for Anthropic Claude client."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from anthropic import APIError

from app.services.ai.ai_client import AiRequestMetadata
from app.services.ai.claude_client import (
    ClaudeNotConfiguredError,
    ClaudeRequestError,
    generate_claude_structured_json,
    is_claude_configured,
)


def _metadata() -> AiRequestMetadata:
    return AiRequestMetadata(
        project_id=uuid4(),
        module="seo_skills",
        operation="run_skill",
        operation_key="seo_audit",
        context_profile="generic",
    )


def test_is_claude_configured_false_without_key() -> None:
    with patch("app.services.ai.claude_client.settings") as mock_settings:
        mock_settings.anthropic_api_key = None
        assert is_claude_configured() is False


def test_generate_claude_structured_json_parses_valid_json() -> None:
    async def run() -> None:
        metadata = _metadata()
        response = MagicMock()
        response.id = "msg_123"
        response.content = [MagicMock(text='{"score": 88, "findings": []}')]
        response.usage = MagicMock(input_tokens=10, output_tokens=20)

        with (
            patch("app.services.ai.claude_client.settings") as mock_settings,
            patch("app.services.ai.claude_client._persist_log", new_callable=AsyncMock),
            patch("app.services.ai.claude_client._client") as mock_client_factory,
        ):
            mock_settings.anthropic_api_key = "test-key"
            mock_settings.claude_model = "claude-3-5-sonnet-latest"
            mock_settings.claude_timeout_seconds = 90.0
            mock_settings.ai_log_prompt_preview = False

            client = MagicMock()
            client.messages.create = AsyncMock(return_value=response)
            mock_client_factory.return_value = client

            result = await generate_claude_structured_json(
                system_prompt="system",
                user_prompt="user",
                metadata=metadata,
            )

        assert result == {"score": 88, "findings": []}

    asyncio.run(run())


def test_generate_claude_structured_json_parses_fenced_json() -> None:
    async def run() -> None:
        metadata = _metadata()
        response = MagicMock()
        response.id = "msg_124"
        response.content = [MagicMock(text='```json\n{"ok": true}\n```')]
        response.usage = MagicMock(input_tokens=5, output_tokens=5)

        with (
            patch("app.services.ai.claude_client.settings") as mock_settings,
            patch("app.services.ai.claude_client._persist_log", new_callable=AsyncMock),
            patch("app.services.ai.claude_client._client") as mock_client_factory,
        ):
            mock_settings.anthropic_api_key = "test-key"
            mock_settings.claude_model = "claude-3-5-sonnet-latest"
            mock_settings.claude_timeout_seconds = 90.0
            mock_settings.ai_log_prompt_preview = False

            client = MagicMock()
            client.messages.create = AsyncMock(return_value=response)
            mock_client_factory.return_value = client

            result = await generate_claude_structured_json(
                system_prompt="system",
                user_prompt="user",
                metadata=metadata,
            )

        assert result == {"ok": True}

    asyncio.run(run())


def test_generate_claude_structured_json_raises_on_invalid_json() -> None:
    async def run() -> None:
        metadata = _metadata()
        response = MagicMock()
        response.id = "msg_125"
        response.content = [MagicMock(text="not-json")]
        response.usage = MagicMock(input_tokens=5, output_tokens=5)

        with (
            patch("app.services.ai.claude_client.settings") as mock_settings,
            patch("app.services.ai.claude_client._persist_log", new_callable=AsyncMock),
            patch("app.services.ai.claude_client._client") as mock_client_factory,
        ):
            mock_settings.anthropic_api_key = "test-key"
            mock_settings.claude_model = "claude-3-5-sonnet-latest"
            mock_settings.claude_timeout_seconds = 90.0
            mock_settings.ai_log_prompt_preview = False

            client = MagicMock()
            client.messages.create = AsyncMock(return_value=response)
            mock_client_factory.return_value = client

            try:
                await generate_claude_structured_json(
                    system_prompt="system",
                    user_prompt="user",
                    metadata=metadata,
                )
                raise AssertionError("expected ClaudeRequestError")
            except ClaudeRequestError as exc:
                assert "JSON valido" in exc.message

    asyncio.run(run())


def test_generate_claude_structured_json_api_error_does_not_expose_api_key() -> None:
    async def run() -> None:
        metadata = _metadata()
        api_key = "super-secret-anthropic-key"
        api_exc = APIError(
            "request failed",
            request=MagicMock(),
            body={"error": {"message": "rate limited"}},
        )

        with (
            patch("app.services.ai.claude_client.settings") as mock_settings,
            patch("app.services.ai.claude_client._persist_log", new_callable=AsyncMock),
            patch("app.services.ai.claude_client._client") as mock_client_factory,
        ):
            mock_settings.anthropic_api_key = api_key
            mock_settings.claude_model = "claude-3-5-sonnet-latest"
            mock_settings.claude_timeout_seconds = 90.0
            mock_settings.ai_log_prompt_preview = False

            client = MagicMock()
            client.messages.create = AsyncMock(side_effect=api_exc)
            mock_client_factory.return_value = client

            try:
                await generate_claude_structured_json(
                    system_prompt="system",
                    user_prompt="user",
                    metadata=metadata,
                )
                raise AssertionError("expected ClaudeRequestError")
            except ClaudeRequestError as exc:
                assert api_key not in exc.message
                assert api_key not in str(exc)

    asyncio.run(run())


def test_generate_claude_structured_json_raises_when_not_configured() -> None:
    async def run() -> None:
        with patch("app.services.ai.claude_client.settings") as mock_settings:
            mock_settings.anthropic_api_key = None
            try:
                await generate_claude_structured_json(
                    system_prompt="system",
                    user_prompt="user",
                    metadata=_metadata(),
                )
                raise AssertionError("expected ClaudeNotConfiguredError")
            except ClaudeNotConfiguredError as exc:
                assert "ANTHROPIC_API_KEY" in str(exc)

    asyncio.run(run())
