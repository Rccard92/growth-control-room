import json
import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.integration import Integration
from app.models.integration_credential import IntegrationCredential
from app.models.project import Project
from app.schemas.google_integration import GoogleIntegrationStatusResponse, GoogleServiceStatus
from app.services.encryption import decrypt_secret, encrypt_secret
from app.services.google.exceptions import GoogleIntegrationReconnectRequiredError
from app.services.google.google_config import (
    get_google_config_status,
    is_crux_configured,
    is_google_ads_developer_token_configured,
    is_google_oauth_configured,
    is_pagespeed_configured,
)
from app.services.google.google_scope_utils import (
    CONTENT_SCOPE,
    GOOGLE_PROVIDER_SCOPES,
    SIBLING_OAUTH_PROVIDERS,
    normalize_oauth_mode,
    normalize_oauth_provider,
    parse_scope_string,
    providers_covered_by_scopes,
    resolve_persist_targets,
)

GOOGLE_OAUTH_PROVIDERS = ("google_search_console", "ga4", "google_ads", "merchant_center")

logger = logging.getLogger(__name__)


def _api_key_service_status(configured: bool) -> GoogleServiceStatus:
    if configured:
        return GoogleServiceStatus(status="connected", configured=True)
    return GoogleServiceStatus(
        status="missing_credentials",
        configured=False,
        message="API key non configurata nel server.",
    )


def credential_has_refresh_token(credential: IntegrationCredential | None) -> bool:
    if credential is None or not credential.encrypted_payload:
        return False
    try:
        payload = json.loads(decrypt_secret(credential.encrypted_payload))
    except (json.JSONDecodeError, TypeError):
        return False
    refresh_token = payload.get("refresh_token")
    return isinstance(refresh_token, str) and bool(refresh_token.strip())


def credential_scope_set(credential: IntegrationCredential | None) -> set[str]:
    if credential is None or not credential.encrypted_payload:
        return set()
    try:
        payload = json.loads(decrypt_secret(credential.encrypted_payload))
    except (json.JSONDecodeError, TypeError, ValueError):
        return set()
    return parse_scope_string(payload.get("scope"))


async def _get_integration_map(
    session: AsyncSession,
    project_id: UUID,
) -> dict[str, Integration]:
    result = await session.execute(
        select(Integration)
        .where(
            Integration.project_id == project_id,
            Integration.provider.in_(GOOGLE_OAUTH_PROVIDERS),
        )
        .options(selectinload(Integration.credential))
    )
    return {integration.provider: integration for integration in result.scalars().all()}


def _oauth_service_status(
    integration: Integration | None,
    *,
    require_developer_token: bool = False,
) -> GoogleServiceStatus:
    if not is_google_oauth_configured():
        return GoogleServiceStatus(
            status="missing_credentials",
            configured=False,
            message="OAuth Google non configurato nel server.",
        )

    has_refresh = credential_has_refresh_token(integration.credential if integration else None)
    if has_refresh:
        if require_developer_token and not is_google_ads_developer_token_configured():
            return GoogleServiceStatus(
                status="setup_incomplete",
                configured=True,
                message="Developer Token Google Ads mancante.",
            )
        return GoogleServiceStatus(status="connected", configured=True)

    return GoogleServiceStatus(
        status="needs_setup",
        configured=True,
        message="Collega il tuo account Google per abilitare questa integrazione.",
    )


def _has_oauth_connected(integrations: dict[str, Integration]) -> bool:
    for provider in SIBLING_OAUTH_PROVIDERS:
        integration = integrations.get(provider)
        if credential_has_refresh_token(integration.credential if integration else None):
            return True
    return False


def _has_merchant_content_scope(integrations: dict[str, Integration]) -> bool:
    merchant = integrations.get("merchant_center")
    if credential_has_refresh_token(merchant.credential if merchant else None):
        scopes = credential_scope_set(merchant.credential if merchant else None)
        if CONTENT_SCOPE in scopes or not scopes:
            return True

    for provider in SIBLING_OAUTH_PROVIDERS:
        integration = integrations.get(provider)
        if not integration or not integration.credential:
            continue
        if CONTENT_SCOPE in credential_scope_set(integration.credential):
            return True
    return False


def _build_merchant_center_status(
    integrations: dict[str, Integration],
    merchant_account_id: str | None,
) -> GoogleServiceStatus:
    merchant_center = integrations.get("merchant_center")
    has_merchant_credential = credential_has_refresh_token(
        merchant_center.credential if merchant_center else None
    )
    oauth_connected = _has_oauth_connected(integrations)

    if not oauth_connected:
        return GoogleServiceStatus(
            status="needs_setup",
            configured=True,
            message="Collega Google per accedere a Merchant Center.",
        )

    if not has_merchant_credential and not _has_merchant_content_scope(integrations):
        return GoogleServiceStatus(
            status="needs_reconnect",
            configured=True,
            message="Ricollega Google per concedere i permessi Merchant Center.",
        )

    if merchant_account_id:
        return GoogleServiceStatus(
            status="connected",
            configured=True,
            message="Account Merchant Center configurato.",
        )

    return GoogleServiceStatus(
        status="needs_setup",
        configured=True,
        message="Seleziona un account Merchant Center.",
    )


async def get_google_integration_status(
    session: AsyncSession,
    project_id: UUID,
) -> GoogleIntegrationStatusResponse:
    config_status = get_google_config_status()
    integrations = await _get_integration_map(session, project_id)

    search_console = integrations.get("google_search_console")
    analytics = integrations.get("ga4")
    google_ads = integrations.get("google_ads")

    project_result = await session.execute(
        select(Project.google_merchant_account_id).where(Project.id == project_id)
    )
    merchant_account_id = project_result.scalar_one_or_none()

    merchant_status = _build_merchant_center_status(integrations, merchant_account_id)

    return GoogleIntegrationStatusResponse(
        pagespeed=_api_key_service_status(is_pagespeed_configured()),
        crux=_api_key_service_status(is_crux_configured()),
        oauth=GoogleServiceStatus(
            status="connected" if config_status["oauth"]["configured"] else "missing_credentials",
            configured=config_status["oauth"]["configured"],
            message=None
            if config_status["oauth"]["configured"]
            else "OAuth Google non configurato nel server.",
        ),
        search_console=_oauth_service_status(search_console),
        analytics=_oauth_service_status(analytics),
        google_ads=_oauth_service_status(google_ads, require_developer_token=True),
        merchant_center=merchant_status,
    )


async def _upsert_provider_credential(
    session: AsyncSession,
    *,
    project_id: UUID,
    provider: str,
    shared_payload: dict[str, Any],
    now: datetime,
) -> None:
    result = await session.execute(
        select(Integration).where(
            Integration.project_id == project_id,
            Integration.provider == provider,
        )
    )
    integration = result.scalar_one_or_none()

    if integration is None:
        integration = Integration(
            project_id=project_id,
            provider=provider,
            status="connected",
            connected_at=now,
        )
        session.add(integration)
        await session.flush()
    else:
        integration.status = "connected"
        integration.connected_at = now
        await session.flush()

    credential_result = await session.execute(
        select(IntegrationCredential).where(
            IntegrationCredential.integration_id == integration.id
        )
    )
    existing_credential = credential_result.scalar_one_or_none()

    payload = dict(shared_payload)
    if (
        not payload.get("refresh_token")
        and existing_credential
        and existing_credential.encrypted_payload
    ):
        try:
            existing = json.loads(decrypt_secret(existing_credential.encrypted_payload))
            if existing.get("refresh_token"):
                payload["refresh_token"] = existing["refresh_token"]
        except (json.JSONDecodeError, TypeError, ValueError):
            pass

    encrypted_payload = encrypt_secret(json.dumps(payload))

    if existing_credential is None:
        credential = IntegrationCredential(
            integration_id=integration.id,
            encrypted_payload=encrypted_payload,
        )
        session.add(credential)
    else:
        existing_credential.encrypted_payload = encrypted_payload


async def persist_google_oauth_tokens(
    session: AsyncSession,
    project_id: UUID,
    token_data: dict[str, Any],
    *,
    requested_provider: str | None = None,
    mode: str | None = None,
) -> None:
    now = datetime.now(UTC)
    obtained_at = now.isoformat()
    normalized_provider = normalize_oauth_provider(requested_provider)
    normalized_mode = normalize_oauth_mode(mode)
    granted_scopes = parse_scope_string(token_data.get("scope"))

    targets = resolve_persist_targets(
        granted_scopes,
        requested_provider=normalized_provider,
        mode=normalized_mode,
    )

    if not targets:
        logger.warning(
            "Skipping Google OAuth persist: no target providers project_id=%s provider=%s mode=%s scopes=%s",
            project_id,
            normalized_provider,
            normalized_mode,
            token_data.get("scope"),
        )
        return

    shared_payload = {
        "access_token": token_data.get("access_token"),
        "refresh_token": token_data.get("refresh_token"),
        "expires_in": token_data.get("expires_in"),
        "token_type": token_data.get("token_type"),
        "scope": token_data.get("scope"),
        "obtained_at": obtained_at,
    }

    for provider in targets:
        if provider not in GOOGLE_PROVIDER_SCOPES:
            continue
        logger.info(
            "Persisting Google OAuth credential project_id=%s provider=%s",
            project_id,
            provider,
        )
        await _upsert_provider_credential(
            session,
            project_id=project_id,
            provider=provider,
            shared_payload=shared_payload,
            now=now,
        )

    await session.commit()


async def ensure_google_provider_credential_from_existing_scope(
    session: AsyncSession,
    project_id: UUID,
    provider: str,
) -> None:
    if provider != "merchant_center":
        return

    integrations = await _get_integration_map(session, project_id)
    merchant = integrations.get("merchant_center")
    if credential_has_refresh_token(merchant.credential if merchant else None):
        return

    source_credential: IntegrationCredential | None = None
    for sibling_provider in SIBLING_OAUTH_PROVIDERS:
        sibling = integrations.get(sibling_provider)
        if sibling and sibling.credential and credential_has_refresh_token(sibling.credential):
            scopes = credential_scope_set(sibling.credential)
            if CONTENT_SCOPE in scopes:
                source_credential = sibling.credential
                break

    if source_credential is None:
        raise GoogleIntegrationReconnectRequiredError(
            "Ricollega Google per concedere i permessi Merchant Center.",
            provider="merchant_center",
        )

    now = datetime.now(UTC)
    result = await session.execute(
        select(Integration).where(
            Integration.project_id == project_id,
            Integration.provider == "merchant_center",
        )
    )
    integration = result.scalar_one_or_none()
    if integration is None:
        integration = Integration(
            project_id=project_id,
            provider="merchant_center",
            status="connected",
            connected_at=now,
        )
        session.add(integration)
        await session.flush()
    else:
        integration.status = "connected"
        integration.connected_at = now
        await session.flush()

    credential_result = await session.execute(
        select(IntegrationCredential).where(
            IntegrationCredential.integration_id == integration.id
        )
    )
    existing_credential = credential_result.scalar_one_or_none()

    if existing_credential is None:
        session.add(
            IntegrationCredential(
                integration_id=integration.id,
                encrypted_payload=source_credential.encrypted_payload,
            )
        )
    else:
        existing_credential.encrypted_payload = source_credential.encrypted_payload

    await session.commit()
