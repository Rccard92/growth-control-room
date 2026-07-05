"""Google OAuth token helpers for project integrations."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.integration import Integration
from app.models.integration_credential import IntegrationCredential
from app.services.encryption import decrypt_secret, encrypt_secret
from app.services.google.exceptions import GoogleIntegrationNotConnectedError
from app.services.google.google_oauth import refresh_google_access_token

TOKEN_REFRESH_BUFFER_SECONDS = 60


def _parse_obtained_at(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _is_access_token_valid(payload: dict[str, Any]) -> bool:
    access_token = payload.get("access_token")
    if not isinstance(access_token, str) or not access_token.strip():
        return False

    expires_in = payload.get("expires_in")
    obtained_at = _parse_obtained_at(payload.get("obtained_at"))
    if obtained_at is None or not isinstance(expires_in, (int, float)):
        return True

    expires_at = obtained_at + timedelta(seconds=float(expires_in))
    return expires_at > datetime.now(UTC) + timedelta(seconds=TOKEN_REFRESH_BUFFER_SECONDS)


def _decrypt_credential_payload(credential: IntegrationCredential) -> dict[str, Any]:
    if not credential.encrypted_payload:
        return {}
    try:
        payload = json.loads(decrypt_secret(credential.encrypted_payload))
    except (json.JSONDecodeError, TypeError, ValueError):
        return {}
    return payload if isinstance(payload, dict) else {}


async def get_google_oauth_credential(
    session: AsyncSession,
    project_id: UUID,
    provider: str,
) -> IntegrationCredential | None:
    integration_result = await session.execute(
        select(Integration).where(
            Integration.project_id == project_id,
            Integration.provider == provider,
        )
    )
    integration = integration_result.scalar_one_or_none()
    if integration is None:
        return None

    credential_result = await session.execute(
        select(IntegrationCredential).where(
            IntegrationCredential.integration_id == integration.id
        )
    )
    return credential_result.scalar_one_or_none()


async def get_valid_google_access_token(
    session: AsyncSession,
    project_id: UUID,
    provider: str = "google_search_console",
) -> str:
    credential = await get_google_oauth_credential(session, project_id, provider)
    if credential is None or not credential.encrypted_payload:
        raise GoogleIntegrationNotConnectedError(
            "Account Google non collegato per questo progetto.",
            integration=provider,
        )

    payload = _decrypt_credential_payload(credential)
    if _is_access_token_valid(payload):
        access_token = payload.get("access_token")
        if isinstance(access_token, str) and access_token.strip():
            return access_token

    refresh_token = payload.get("refresh_token")
    if not isinstance(refresh_token, str) or not refresh_token.strip():
        raise GoogleIntegrationNotConnectedError(
            "Refresh token Google mancante. Ricollega l'account Google.",
            integration=provider,
        )

    refreshed = await refresh_google_access_token(refresh_token)
    merged_payload = {
        **payload,
        "access_token": refreshed.get("access_token"),
        "expires_in": refreshed.get("expires_in", payload.get("expires_in")),
        "token_type": refreshed.get("token_type", payload.get("token_type")),
        "scope": refreshed.get("scope", payload.get("scope")),
        "refresh_token": refresh_token,
        "obtained_at": datetime.now(UTC).isoformat(),
    }
    credential.encrypted_payload = encrypt_secret(json.dumps(merged_payload))
    session.add(credential)
    await session.flush()

    access_token = merged_payload.get("access_token")
    if not isinstance(access_token, str) or not access_token.strip():
        raise GoogleIntegrationNotConnectedError(
            "Impossibile ottenere un access token Google valido.",
            integration=provider,
        )
    return access_token
