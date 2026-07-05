"""Tests for Google OAuth token helpers."""

from __future__ import annotations

import asyncio
import json
import os
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

from app.models.integration import Integration
from app.models.integration_credential import IntegrationCredential
from app.services.encryption import encrypt_secret
from app.services.google.exceptions import GoogleIntegrationNotConnectedError
from app.services.google.google_tokens import (
    _is_access_token_valid,
    get_valid_google_access_token,
)


def test_is_access_token_valid_when_fresh() -> None:
    payload = {
        "access_token": "token-123",
        "expires_in": 3600,
        "obtained_at": datetime.now(UTC).isoformat(),
    }
    assert _is_access_token_valid(payload) is True


def test_is_access_token_valid_when_expired() -> None:
    payload = {
        "access_token": "token-123",
        "expires_in": 60,
        "obtained_at": (datetime.now(UTC) - timedelta(hours=2)).isoformat(),
    }
    assert _is_access_token_valid(payload) is False


def test_get_valid_google_access_token_raises_without_credential() -> None:
    async def run() -> None:
        project_id = uuid4()
        session = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none = MagicMock(return_value=None)
        session.execute = AsyncMock(return_value=result_mock)

        with pytest.raises(GoogleIntegrationNotConnectedError):
            await get_valid_google_access_token(session, project_id)

    asyncio.run(run())


def test_get_valid_google_access_token_refreshes_when_expired() -> None:
    async def run() -> None:
        project_id = uuid4()
        integration_id = uuid4()
        credential = IntegrationCredential(
            integration_id=integration_id,
            encrypted_payload=encrypt_secret(
                json.dumps(
                    {
                        "access_token": "old-token",
                        "refresh_token": "refresh-456",
                        "expires_in": 60,
                        "obtained_at": (datetime.now(UTC) - timedelta(hours=2)).isoformat(),
                    }
                )
            ),
        )
        integration = Integration(
            id=integration_id,
            project_id=project_id,
            provider="google_search_console",
            status="connected",
        )

        integration_result = MagicMock()
        integration_result.scalar_one_or_none = MagicMock(return_value=integration)
        credential_result = MagicMock()
        credential_result.scalar_one_or_none = MagicMock(return_value=credential)
        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[integration_result, credential_result])
        session.add = MagicMock()
        session.flush = AsyncMock()

        with patch(
            "app.services.google.google_tokens.refresh_google_access_token",
            new=AsyncMock(
                return_value={
                    "access_token": "new-token",
                    "expires_in": 3600,
                    "token_type": "Bearer",
                }
            ),
        ):
            token = await get_valid_google_access_token(session, project_id)

        assert token == "new-token"
        session.flush.assert_awaited_once()

    asyncio.run(run())
