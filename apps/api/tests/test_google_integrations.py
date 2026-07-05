"""Tests for Google integrations API and services."""

from __future__ import annotations

import asyncio
import json
import os
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

from app.api.routes.google_integrations import (
    get_google_status,
    google_oauth_callback,
    start_google_oauth,
)
from app.schemas.google_integration import GoogleOAuthStartRequest
from app.services.encryption import decrypt_secret
from app.services.google.google_config import get_google_config_status
from app.services.google.google_integrations import (
    credential_has_refresh_token,
    get_google_integration_status,
    persist_google_oauth_tokens,
)
from app.models.integration import Integration
from app.models.integration_credential import IntegrationCredential


def test_get_google_config_status_with_env(monkeypatch) -> None:
    monkeypatch.setattr("app.services.google.google_config.settings.google_pagespeed_api_key", "ps-key")
    monkeypatch.setattr("app.services.google.google_config.settings.google_crux_api_key", "crux-key")
    monkeypatch.setattr(
        "app.services.google.google_config.settings.google_oauth_client_id",
        "client-id",
    )
    monkeypatch.setattr(
        "app.services.google.google_config.settings.google_oauth_client_secret",
        "client-secret",
    )
    monkeypatch.setattr(
        "app.services.google.google_config.settings.google_oauth_redirect_uri",
        "https://api.example.com/google/oauth/callback",
    )
    monkeypatch.setattr("app.services.google.google_config.settings.frontend_url", "https://app.example.com")
    monkeypatch.setattr("app.services.google.google_config.settings.google_ads_developer_token", None)

    status = get_google_config_status()
    assert status["pagespeed"]["configured"] is True
    assert status["crux"]["configured"] is True
    assert status["oauth"]["configured"] is True
    assert status["googleAdsDeveloperToken"]["configured"] is False


def test_get_google_status_does_not_expose_secrets() -> None:
    async def run() -> None:
        project_id = uuid4()
        session = AsyncMock()
        session.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(return_value=iter([]))))

        with (
            patch(
                "app.api.routes.google_integrations.get_project_in_default_workspace",
                new_callable=AsyncMock,
            ),
            patch(
                "app.api.routes.google_integrations.get_google_integration_status",
                new_callable=AsyncMock,
            ) as status_mock,
        ):
            status_mock.return_value = MagicMock(
                model_dump=lambda by_alias=True: {
                    "pagespeed": {"status": "connected", "configured": True},
                    "crux": {"status": "connected", "configured": True},
                    "oauth": {"status": "connected", "configured": True},
                    "searchConsole": {"status": "needs_setup", "configured": True},
                    "analytics": {"status": "needs_setup", "configured": True},
                    "googleAds": {
                        "status": "setup_incomplete",
                        "configured": True,
                        "message": "Developer Token Google Ads mancante.",
                    },
                }
            )
            response = await get_google_status(project_id, session)
            payload = response.model_dump(by_alias=True)

        assert "access_token" not in json.dumps(payload)
        assert "refresh_token" not in json.dumps(payload)
        assert payload["googleAds"]["status"] == "setup_incomplete"

    asyncio.run(run())


def test_start_google_oauth_returns_authorization_url() -> None:
    async def run() -> None:
        project_id = uuid4()
        session = AsyncMock()

        with (
            patch(
                "app.api.routes.google_integrations.get_project_in_default_workspace",
                new_callable=AsyncMock,
            ),
            patch(
                "app.api.routes.google_integrations.ensure_google_oauth_configured",
            ),
            patch(
                "app.api.routes.google_integrations.build_google_oauth_authorization_url",
                return_value="https://accounts.google.com/o/oauth2/v2/auth?client_id=test",
            ),
        ):
            response = await start_google_oauth(project_id, GoogleOAuthStartRequest(), session)

        assert response.authorization_url.startswith("https://accounts.google.com/")

    asyncio.run(run())


def test_start_google_oauth_missing_env_returns_503() -> None:
    async def run() -> None:
        project_id = uuid4()
        session = AsyncMock()

        with (
            patch(
                "app.api.routes.google_integrations.get_project_in_default_workspace",
                new_callable=AsyncMock,
            ),
            patch(
                "app.api.routes.google_integrations.ensure_google_oauth_configured",
                side_effect=HTTPException(status_code=503, detail={"error": "google_oauth_not_configured"}),
            ),
            pytest.raises(HTTPException) as exc,
        ):
            await start_google_oauth(project_id, GoogleOAuthStartRequest(), session)

        assert exc.value.status_code == 503

    asyncio.run(run())


def test_google_oauth_callback_error_redirect() -> None:
    async def run() -> None:
        request = MagicMock()
        request.query_params = {"error": "access_denied", "state": "bad"}
        session = AsyncMock()

        with patch(
            "app.api.routes.google_integrations.verify_google_oauth_state",
            return_value=None,
        ):
            response = await google_oauth_callback(request, session)

        assert response.status_code == 302
        assert "google_error=access_denied" in response.headers["location"]

    asyncio.run(run())


def test_google_oauth_callback_invalid_state_redirect() -> None:
    async def run() -> None:
        request = MagicMock()
        request.query_params = {"code": "abc", "state": "invalid"}
        session = AsyncMock()

        with patch(
            "app.api.routes.google_integrations.verify_google_oauth_state",
            return_value=None,
        ):
            response = await google_oauth_callback(request, session)

        assert response.status_code == 302
        assert "google_error=invalid_state" in response.headers["location"]

    asyncio.run(run())


def test_google_oauth_callback_success_redirect() -> None:
    async def run() -> None:
        project_id = uuid4()
        request = MagicMock()
        request.query_params = {"code": "auth-code", "state": "valid-state"}
        session = AsyncMock()

        with (
            patch(
                "app.api.routes.google_integrations.verify_google_oauth_state",
                return_value=project_id,
            ),
            patch(
                "app.api.routes.google_integrations.get_project_in_default_workspace",
                new_callable=AsyncMock,
            ),
            patch(
                "app.api.routes.google_integrations.exchange_google_oauth_code",
                new_callable=AsyncMock,
                return_value={
                    "access_token": "access-123",
                    "refresh_token": "refresh-456",
                    "expires_in": 3600,
                    "token_type": "Bearer",
                    "scope": "scope",
                },
            ),
            patch(
                "app.api.routes.google_integrations.persist_google_oauth_tokens",
                new_callable=AsyncMock,
            ) as persist_mock,
            patch(
                "app.api.routes.google_integrations.frontend_redirect_url",
                side_effect=lambda path: f"https://app.example.com{path}",
            ),
        ):
            response = await google_oauth_callback(request, session)

        persist_mock.assert_awaited_once()
        assert response.status_code == 302
        assert "google_connected=1" in response.headers["location"]

    asyncio.run(run())


def test_google_ads_setup_incomplete_without_developer_token(monkeypatch) -> None:
    async def run() -> None:
        project_id = uuid4()
        now = datetime.now(UTC)
        integration_id = uuid4()
        encrypted = __import__(
            "app.services.encryption", fromlist=["encrypt_secret"]
        ).encrypt_secret(
            json.dumps({"refresh_token": "refresh-456", "access_token": "access-123"})
        )
        integration = Integration(
            id=integration_id,
            project_id=project_id,
            provider="google_ads",
            status="connected",
            connected_at=now,
            created_at=now,
            updated_at=now,
        )
        integration.credential = IntegrationCredential(
            integration_id=integration_id,
            encrypted_payload=encrypted,
        )

        session = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [integration]
        session.execute = AsyncMock(return_value=result_mock)

        monkeypatch.setattr(
            "app.services.google.google_integrations.is_google_oauth_configured",
            lambda: True,
        )
        monkeypatch.setattr(
            "app.services.google.google_integrations.is_google_ads_developer_token_configured",
            lambda: False,
        )
        monkeypatch.setattr(
            "app.services.google.google_integrations.is_pagespeed_configured",
            lambda: True,
        )
        monkeypatch.setattr(
            "app.services.google.google_integrations.is_crux_configured",
            lambda: True,
        )

        status = await get_google_integration_status(session, project_id)
        assert status.google_ads.status == "setup_incomplete"
        assert "Developer Token" in (status.google_ads.message or "")

    asyncio.run(run())


def test_persist_google_oauth_tokens_saves_refresh_token() -> None:
    async def run() -> None:
        project_id = uuid4()
        session = AsyncMock()
        session.flush = AsyncMock()
        session.commit = AsyncMock()

        result_mock = MagicMock()
        result_mock.scalar_one_or_none = MagicMock(return_value=None)
        session.execute = AsyncMock(return_value=result_mock)

        added: list[object] = []
        session.add = MagicMock(side_effect=lambda obj: added.append(obj))

        await persist_google_oauth_tokens(
            session,
            project_id,
            {
                "access_token": "access-123",
                "refresh_token": "refresh-456",
                "expires_in": 3600,
                "token_type": "Bearer",
                "scope": "scope",
            },
        )

        credentials = [obj for obj in added if isinstance(obj, IntegrationCredential)]
        assert len(credentials) == 3
        payload = json.loads(decrypt_secret(credentials[0].encrypted_payload))
        assert payload["refresh_token"] == "refresh-456"
        session.commit.assert_awaited_once()

    asyncio.run(run())


def test_credential_has_refresh_token() -> None:
    payload = json.dumps({"refresh_token": "refresh-456", "access_token": "access-123"})
    credential = IntegrationCredential(
        integration_id=uuid4(),
        encrypted_payload=__import__(
            "app.services.encryption", fromlist=["encrypt_secret"]
        ).encrypt_secret(payload),
    )
    assert credential_has_refresh_token(credential) is True
