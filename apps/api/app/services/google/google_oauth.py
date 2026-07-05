import base64
import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlencode
from uuid import UUID

import httpx
from fastapi import HTTPException, status

from app.core.config import settings
from app.services.google.google_scope_utils import (
    get_google_scopes_for_reconnect,
    normalize_oauth_mode,
    normalize_oauth_provider,
    resolve_oauth_prompt,
)

GOOGLE_OAUTH_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"

OAUTH_STATE_TTL_MINUTES = 10


@dataclass(frozen=True)
class GoogleOAuthState:
    project_id: UUID
    provider: str | None = None
    mode: str = "connect"


def ensure_google_oauth_configured() -> None:
    if settings.google_oauth_configured:
        return
    missing = ", ".join(settings.google_oauth_missing_vars)
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={
            "error": "google_oauth_not_configured",
            "message": (
                "Google OAuth non configurato. Imposta le variabili d'ambiente: "
                f"{missing}"
            ),
            "missing_vars": settings.google_oauth_missing_vars,
        },
    )


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _sign_state_payload(payload_b64: str) -> str:
    secret = (settings.google_oauth_client_secret or "").encode("utf-8")
    digest = hmac.new(secret, payload_b64.encode("utf-8"), hashlib.sha256).hexdigest()
    return digest


def create_google_oauth_state(
    project_id: UUID,
    *,
    provider: str | None = None,
    mode: str | None = None,
) -> str:
    payload = {
        "project_id": str(project_id),
        "nonce": secrets.token_urlsafe(16),
        "exp": int((datetime.now(UTC) + timedelta(minutes=OAUTH_STATE_TTL_MINUTES)).timestamp()),
        "provider": normalize_oauth_provider(provider) if provider else None,
        "mode": normalize_oauth_mode(mode),
    }
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = _sign_state_payload(payload_b64)
    return f"{payload_b64}.{signature}"


def verify_google_oauth_state(state_value: str) -> GoogleOAuthState | None:
    if not state_value or "." not in state_value:
        return None
    payload_b64, signature = state_value.rsplit(".", 1)
    expected = _sign_state_payload(payload_b64)
    if not hmac.compare_digest(expected, signature):
        return None
    try:
        payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
        exp = int(payload.get("exp", 0))
        if exp < int(datetime.now(UTC).timestamp()):
            return None
        provider_raw = payload.get("provider")
        mode_raw = payload.get("mode")
        return GoogleOAuthState(
            project_id=UUID(str(payload["project_id"])),
            provider=normalize_oauth_provider(provider_raw) if provider_raw else None,
            mode=normalize_oauth_mode(mode_raw),
        )
    except (ValueError, KeyError, json.JSONDecodeError):
        return None


def build_google_oauth_authorization_url(
    project_id: UUID,
    *,
    scopes: list[str] | None = None,
    provider: str | None = None,
    mode: str | None = None,
    prompt: str | None = None,
) -> str:
    ensure_google_oauth_configured()
    normalized_provider = normalize_oauth_provider(provider)
    normalized_mode = normalize_oauth_mode(mode)
    resolved_scopes = scopes or get_google_scopes_for_reconnect(normalized_provider)
    resolved_prompt = prompt or resolve_oauth_prompt(normalized_mode)
    state_provider = None if normalized_provider == "all" else normalized_provider
    params = {
        "client_id": settings.google_oauth_client_id,
        "redirect_uri": settings.google_oauth_redirect_uri,
        "response_type": "code",
        "access_type": "offline",
        "prompt": resolved_prompt,
        "include_granted_scopes": "true",
        "scope": " ".join(resolved_scopes),
        "state": create_google_oauth_state(
            project_id,
            provider=state_provider,
            mode=normalized_mode,
        ),
    }
    return f"{GOOGLE_OAUTH_AUTHORIZE_URL}?{urlencode(params)}"


async def exchange_google_oauth_code(code: str) -> dict[str, Any]:
    ensure_google_oauth_configured()
    payload = {
        "code": code,
        "client_id": settings.google_oauth_client_id,
        "client_secret": settings.google_oauth_client_secret,
        "redirect_uri": settings.google_oauth_redirect_uri,
        "grant_type": "authorization_code",
    }
    return await _post_token_request(payload)


async def refresh_google_access_token(refresh_token: str) -> dict[str, Any]:
    ensure_google_oauth_configured()
    payload = {
        "refresh_token": refresh_token,
        "client_id": settings.google_oauth_client_id,
        "client_secret": settings.google_oauth_client_secret,
        "grant_type": "refresh_token",
    }
    return await _post_token_request(payload)


async def _post_token_request(payload: dict[str, str]) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(GOOGLE_OAUTH_TOKEN_URL, data=payload)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": "google_token_exchange_failed",
                "message": "Impossibile contattare Google OAuth.",
            },
        ) from exc

    if response.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": "google_token_exchange_failed",
                "message": "Google ha rifiutato lo scambio del codice OAuth.",
            },
        )

    data: dict[str, Any] = response.json()
    if not data.get("access_token"):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": "google_token_exchange_failed",
                "message": "Risposta OAuth Google non valida.",
            },
        )
    return data


def frontend_redirect_url(path: str) -> str:
    base = (settings.frontend_url or "").rstrip("/")
    return f"{base}{path}"
