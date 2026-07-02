"""Tests for AI client error handling and user-facing messages."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from openai import BadRequestError
import pytest

from app.services.ai.ai_client import (
    AiRequestMetadata,
    OpenAIRequestError,
    generate_structured_json,
)
from app.services.ai.exceptions import OpenAIRequestError as OpenAIRequestErrorCls


def test_openai_request_error_exposes_code() -> None:
    err = OpenAIRequestErrorCls("test", code="model_incompatible")
    assert err.code == "model_incompatible"
    assert err.message == "test"


def test_bad_request_error_message_is_readable() -> None:
    async def run() -> None:
        project_id = uuid4()
        metadata = AiRequestMetadata(
            project_id=project_id,
            module="product_seo",
            operation="generate_field",
            operation_key="product_image_alt",
            context_profile="image_alt",
        )

        bad_exc = BadRequestError(
            "Unsupported parameter: 'max_tokens'",
            response=MagicMock(status_code=400),
            body={"error": {"message": "Unsupported parameter: 'max_tokens'"}},
        )

        session_factory = MagicMock()
        session = AsyncMock()
        session.commit = AsyncMock()
        session.__aenter__ = AsyncMock(return_value=session)
        session.__aexit__ = AsyncMock(return_value=False)
        session_factory.return_value = session

        with (
            patch("app.services.ai.ai_client.get_session_factory", return_value=session_factory),
            patch("app.services.ai.ai_client.check_budget_before_request", new_callable=AsyncMock),
            patch(
                "app.services.ai.ai_client.resolve_ai_model",
                new_callable=AsyncMock,
                return_value=MagicMock(
                    model="gpt-5.4-mini",
                    tier="cheap",
                    max_output_tokens=120,
                    temperature=0.3,
                    reasoning_effort=None,
                    fallback_model=None,
                    operation_key="product_image_alt",
                    policy_source="project_setting",
                    warning=None,
                    model_copy=lambda update=None: MagicMock(
                        model="gpt-5.4-mini",
                        tier="cheap",
                        max_output_tokens=120,
                        temperature=0.3,
                        reasoning_effort=None,
                        fallback_model=None,
                        operation_key="product_image_alt",
                        policy_source="project_setting",
                        warning=None,
                    ),
                ),
            ),
            patch("app.services.ai.ai_client._client") as mock_client_factory,
            patch("app.services.ai.ai_client._persist_log", new_callable=AsyncMock) as mock_log,
        ):
            client = MagicMock()
            client.chat.completions.create = AsyncMock(side_effect=bad_exc)
            mock_client_factory.return_value = client

            try:
                await generate_structured_json(
                    system_prompt="system",
                    user_prompt="user",
                    metadata=metadata,
                )
                raise AssertionError("expected OpenAIRequestError")
            except OpenAIRequestError as exc:
                assert "Errore AI" in exc.message
                assert "max_tokens" in exc.message or "parametri" in exc.message.lower()
                assert exc.code == "model_incompatible"

            mock_log.assert_awaited()

    asyncio.run(run())


def test_empty_openai_response_maps_to_user_message() -> None:
    from app.services.ai.ai_client import (
        _SchemaParseError,
        _parse_json_object_response,
        _user_message_for_parse_error,
    )
    from app.services.seo_skills.error_messages import OPENAI_EMPTY_RESPONSE_USER_MESSAGE

    response = MagicMock()
    response.choices = [MagicMock(message=MagicMock(content=""))]

    with pytest.raises(_SchemaParseError) as exc_info:
        _parse_json_object_response(response)

    assert exc_info.value.empty_content is True
    assert _user_message_for_parse_error(exc_info.value) == OPENAI_EMPTY_RESPONSE_USER_MESSAGE
