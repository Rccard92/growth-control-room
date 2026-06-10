import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlencode
from uuid import UUID

import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.shopify_oauth_state import ShopifyOAuthState
from app.services.shopify.client import ShopifyAPIError

OAUTH_STATE_TTL_MINUTES = 10


def ensure_shopify_oauth_configured() -> None:
    if settings.shopify_oauth_configured:
        return
    missing = ", ".join(settings.shopify_oauth_missing_vars)
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={
            "error": "oauth_not_configured",
            "message": (
                "Shopify OAuth non configurato. Imposta le variabili d'ambiente: "
                f"{missing}"
            ),
            "missing_vars": settings.shopify_oauth_missing_vars,
        },
    )


async def create_oauth_state(
    session: AsyncSession,
    project_id: UUID,
    shop_domain: str,
) -> ShopifyOAuthState:
    state_value = secrets.token_urlsafe(32)
    expires_at = datetime.now(UTC) + timedelta(minutes=OAUTH_STATE_TTL_MINUTES)
    oauth_state = ShopifyOAuthState(
        project_id=project_id,
        shop_domain=shop_domain,
        state=state_value,
        expires_at=expires_at,
    )
    session.add(oauth_state)
    await session.flush()
    return oauth_state


async def consume_oauth_state(
    session: AsyncSession,
    state_value: str,
) -> ShopifyOAuthState | None:
    now = datetime.now(UTC)
    result = await session.execute(
        select(ShopifyOAuthState).where(ShopifyOAuthState.state == state_value)
    )
    oauth_state = result.scalar_one_or_none()
    if oauth_state is None:
        return None
    if oauth_state.consumed_at is not None:
        return None
    if oauth_state.expires_at < now:
        return None

    oauth_state.consumed_at = now
    await session.flush()
    return oauth_state


def verify_shopify_hmac(query_params: dict[str, str], secret: str) -> bool:
    provided_hmac = query_params.get("hmac")
    if not provided_hmac:
        return False

    filtered = {
        key: value
        for key, value in query_params.items()
        if key not in {"hmac", "signature"} and value
    }
    message = "&".join(f"{key}={filtered[key]}" for key in sorted(filtered))
    digest = hmac.new(
        secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(digest, provided_hmac)


def build_authorization_url(shop_domain: str, state: str) -> str:
    params = {
        "client_id": settings.shopify_client_id,
        "scope": settings.shopify_scopes,
        "redirect_uri": settings.shopify_redirect_uri,
        "state": state,
    }
    return f"https://{shop_domain}/admin/oauth/authorize?{urlencode(params)}"


async def exchange_code_for_access_token(shop_domain: str, code: str) -> str:
    url = f"https://{shop_domain}/admin/oauth/access_token"
    payload = {
        "client_id": settings.shopify_client_id,
        "client_secret": settings.shopify_client_secret,
        "code": code,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
    except httpx.HTTPError as exc:
        raise ShopifyAPIError(
            "Impossibile contattare Shopify per completare l'autorizzazione",
            status_code=status.HTTP_502_BAD_GATEWAY,
        ) from exc

    if response.status_code >= 400:
        raise ShopifyAPIError(
            "Shopify ha rifiutato lo scambio del codice OAuth",
            status_code=response.status_code,
        )

    data: dict[str, Any] = response.json()
    access_token = data.get("access_token")
    if not access_token or not isinstance(access_token, str):
        raise ShopifyAPIError(
            "Risposta OAuth Shopify non valida: access token mancante",
            status_code=status.HTTP_502_BAD_GATEWAY,
        )

    return access_token


def frontend_redirect_url(path: str) -> str:
    base = (settings.frontend_url or "").rstrip("/")
    return f"{base}{path}"
