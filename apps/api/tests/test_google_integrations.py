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
    list_search_console_sites,
    select_search_console_site,
    start_google_oauth,
)
from app.schemas.google_integration import GoogleOAuthStartRequest, SelectSearchConsoleSiteRequest
from app.services.encryption import decrypt_secret, encrypt_secret
from app.services.google.google_config import get_google_config_status
from app.services.google.google_integrations import (
    GOOGLE_OAUTH_PROVIDERS,
    credential_has_refresh_token,
    get_google_integration_status,
    persist_google_oauth_tokens,
)
from app.models.integration import Integration
from app.models.integration_credential import IntegrationCredential
from app.models.project import Project
from app.services.google.exceptions import GoogleIntegrationNotConnectedError


def _make_persist_session(
    execute_responses: list[Integration | IntegrationCredential | None],
) -> tuple[AsyncMock, list[object]]:
    session = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    added: list[object] = []

    def add_side_effect(obj: object) -> None:
        added.append(obj)
        if isinstance(obj, Integration) and getattr(obj, "id", None) is None:
            obj.id = uuid4()

    session.add = MagicMock(side_effect=add_side_effect)

    execute_results = []
    for value in execute_responses:
        result_mock = MagicMock()
        result_mock.scalar_one_or_none = MagicMock(return_value=value)
        execute_results.append(result_mock)

    session.execute = AsyncMock(side_effect=execute_results)
    return session, added


def _build_existing_integration(
    *,
    project_id,
    provider: str,
) -> Integration:
    now = datetime.now(UTC)
    return Integration(
        id=uuid4(),
        project_id=project_id,
        provider=provider,
        status="connected",
        connected_at=now,
        created_at=now,
        updated_at=now,
    )


def _token_data(
    *,
    access_token: str = "access-123",
    refresh_token: str | None = "refresh-456",
) -> dict[str, object]:
    payload: dict[str, object] = {
        "access_token": access_token,
        "expires_in": 3600,
        "token_type": "Bearer",
        "scope": "scope",
    }
    if refresh_token is not None:
        payload["refresh_token"] = refresh_token
    return payload


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
        session, added = _make_persist_session([None] * (len(GOOGLE_OAUTH_PROVIDERS) * 2))

        await persist_google_oauth_tokens(session, project_id, _token_data())

        credentials = [obj for obj in added if isinstance(obj, IntegrationCredential)]
        assert len(credentials) == 3
        payload = json.loads(decrypt_secret(credentials[0].encrypted_payload))
        assert payload["refresh_token"] == "refresh-456"
        session.commit.assert_awaited_once()

    asyncio.run(run())


def test_persist_google_oauth_tokens_creates_integrations_and_credentials() -> None:
    async def run() -> None:
        project_id = uuid4()
        session, added = _make_persist_session([None] * (len(GOOGLE_OAUTH_PROVIDERS) * 2))

        await persist_google_oauth_tokens(session, project_id, _token_data())

        integrations = [obj for obj in added if isinstance(obj, Integration)]
        credentials = [obj for obj in added if isinstance(obj, IntegrationCredential)]

        assert len(integrations) == 3
        assert len(credentials) == 3
        assert {integration.provider for integration in integrations} == set(GOOGLE_OAUTH_PROVIDERS)
        assert all(integration.status == "connected" for integration in integrations)
        assert all(integration.connected_at is not None for integration in integrations)
        assert all(credential.encrypted_payload for credential in credentials)
        session.commit.assert_awaited_once()

    asyncio.run(run())


def test_persist_google_oauth_tokens_updates_existing_credential() -> None:
    async def run() -> None:
        project_id = uuid4()
        execute_responses: list[Integration | IntegrationCredential | None] = []
        existing_credentials: list[IntegrationCredential] = []

        for provider in GOOGLE_OAUTH_PROVIDERS:
            integration = _build_existing_integration(project_id=project_id, provider=provider)
            credential = IntegrationCredential(
                integration_id=integration.id,
                encrypted_payload=encrypt_secret(
                    json.dumps({"access_token": "old", "refresh_token": "old-refresh"})
                ),
            )
            existing_credentials.append(credential)
            execute_responses.extend([integration, credential])

        session, added = _make_persist_session(execute_responses)

        await persist_google_oauth_tokens(
            session,
            project_id,
            _token_data(access_token="new-access", refresh_token="new-refresh"),
        )

        new_credentials = [obj for obj in added if isinstance(obj, IntegrationCredential)]
        assert len(new_credentials) == 0

        for credential in existing_credentials:
            payload = json.loads(decrypt_secret(credential.encrypted_payload))
            assert payload["access_token"] == "new-access"
            assert payload["refresh_token"] == "new-refresh"

        session.commit.assert_awaited_once()

    asyncio.run(run())


def test_persist_google_oauth_tokens_preserves_refresh_token() -> None:
    async def run() -> None:
        project_id = uuid4()

        session_first, added_first = _make_persist_session(
            [None] * (len(GOOGLE_OAUTH_PROVIDERS) * 2)
        )
        await persist_google_oauth_tokens(
            session_first,
            project_id,
            _token_data(refresh_token="refresh-keep"),
        )

        integrations = [obj for obj in added_first if isinstance(obj, Integration)]
        credentials = [obj for obj in added_first if isinstance(obj, IntegrationCredential)]
        assert len(integrations) == 3
        assert len(credentials) == 3

        execute_responses: list[Integration | IntegrationCredential | None] = []
        for integration, credential in zip(integrations, credentials, strict=True):
            execute_responses.extend([integration, credential])

        session_second, added_second = _make_persist_session(execute_responses)
        await persist_google_oauth_tokens(
            session_second,
            project_id,
            _token_data(access_token="access-renewed", refresh_token=None),
        )

        new_credentials = [obj for obj in added_second if isinstance(obj, IntegrationCredential)]
        assert len(new_credentials) == 0

        for credential in credentials:
            payload = json.loads(decrypt_secret(credential.encrypted_payload))
            assert payload["access_token"] == "access-renewed"
            assert payload["refresh_token"] == "refresh-keep"

    asyncio.run(run())


def test_persist_google_oauth_tokens_uses_explicit_credential_query() -> None:
    async def run() -> None:
        project_id = uuid4()
        integrations = [
            _build_existing_integration(project_id=project_id, provider=provider)
            for provider in GOOGLE_OAUTH_PROVIDERS
        ]
        execute_responses: list[Integration | IntegrationCredential | None] = []
        for integration in integrations:
            assert "credential" not in integration.__dict__
            execute_responses.extend([integration, None])

        session, _added = _make_persist_session(execute_responses)

        await persist_google_oauth_tokens(session, project_id, _token_data())

        assert session.execute.await_count == len(GOOGLE_OAUTH_PROVIDERS) * 2

        credential_query_calls = 0
        for call in session.execute.await_args_list:
            statement = call.args[0]
            if getattr(statement, "column_descriptions", None):
                entities = [item["entity"] for item in statement.column_descriptions]
                if IntegrationCredential in entities:
                    credential_query_calls += 1

        assert credential_query_calls == len(GOOGLE_OAUTH_PROVIDERS)

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


def test_list_search_console_sites_returns_sites() -> None:
    async def run() -> None:
        project_id = uuid4()
        session = AsyncMock()

        with (
            patch(
                "app.api.routes.google_integrations.get_project_in_default_workspace",
                new_callable=AsyncMock,
            ),
            patch(
                "app.api.routes.google_integrations.get_valid_google_access_token",
                new_callable=AsyncMock,
                return_value="access-token",
            ),
            patch(
                "app.api.routes.google_integrations.fetch_search_console_sites",
                new_callable=AsyncMock,
                return_value=[
                    {"siteUrl": "https://example.com/", "permissionLevel": "siteOwner"},
                ],
            ),
        ):
            response = await list_search_console_sites(project_id, session)

        assert response.sites[0].site_url == "https://example.com/"
        assert response.sites[0].permission_level == "siteOwner"

    asyncio.run(run())


def test_list_search_console_sites_returns_503_when_not_connected() -> None:
    async def run() -> None:
        project_id = uuid4()
        session = AsyncMock()

        with (
            patch(
                "app.api.routes.google_integrations.get_project_in_default_workspace",
                new_callable=AsyncMock,
            ),
            patch(
                "app.api.routes.google_integrations.get_valid_google_access_token",
                new_callable=AsyncMock,
                side_effect=GoogleIntegrationNotConnectedError(
                    "Account Google non collegato.",
                    integration="google_search_console",
                ),
            ),
            pytest.raises(HTTPException) as exc,
        ):
            await list_search_console_sites(project_id, session)

        assert exc.value.status_code == 503

    asyncio.run(run())


def test_select_search_console_site_saves_property() -> None:
    async def run() -> None:
        project_id = uuid4()
        session = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        project = Project(
            id=project_id,
            workspace_id=uuid4(),
            name="Example",
            slug="example",
            search_console_site_url=None,
            status="active",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        with (
            patch(
                "app.api.routes.google_integrations.get_project_in_default_workspace",
                new_callable=AsyncMock,
                return_value=project,
            ),
            patch(
                "app.api.routes.google_integrations.get_valid_google_access_token",
                new_callable=AsyncMock,
                return_value="access-token",
            ),
            patch(
                "app.api.routes.google_integrations.fetch_search_console_sites",
                new_callable=AsyncMock,
                return_value=[
                    {"siteUrl": "https://example.com/", "permissionLevel": "siteOwner"},
                ],
            ),
        ):
            response = await select_search_console_site(
                project_id,
                SelectSearchConsoleSiteRequest(site_url="https://example.com/"),
                session,
            )

        assert response.site_url == "https://example.com/"
        assert project.search_console_site_url == "https://example.com/"
        session.commit.assert_awaited_once()

    asyncio.run(run())


def test_select_search_console_site_returns_422_for_unknown_property() -> None:
    async def run() -> None:
        project_id = uuid4()
        session = AsyncMock()
        project = Project(
            id=project_id,
            workspace_id=uuid4(),
            name="Example",
            slug="example",
            search_console_site_url=None,
            status="active",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        with (
            patch(
                "app.api.routes.google_integrations.get_project_in_default_workspace",
                new_callable=AsyncMock,
                return_value=project,
            ),
            patch(
                "app.api.routes.google_integrations.get_valid_google_access_token",
                new_callable=AsyncMock,
                return_value="access-token",
            ),
            patch(
                "app.api.routes.google_integrations.fetch_search_console_sites",
                new_callable=AsyncMock,
                return_value=[
                    {"siteUrl": "https://example.com/", "permissionLevel": "siteOwner"},
                ],
            ),
            pytest.raises(HTTPException) as exc,
        ):
            await select_search_console_site(
                project_id,
                SelectSearchConsoleSiteRequest(site_url="https://other.com/"),
                session,
            )

        assert exc.value.status_code == 422

    asyncio.run(run())
