import json
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.integration import Integration
from app.models.integration_credential import IntegrationCredential
from app.models.shopify import ShopifyStore
from app.services.encryption import decrypt_secret, encrypt_secret
from app.services.shopify.client import ShopifyAPIError, ShopifyGraphQLClient, normalize_shop_domain


async def get_shopify_store_for_project(
    project_id: UUID,
    session: AsyncSession,
) -> ShopifyStore | None:
    result = await session.execute(
        select(ShopifyStore)
        .where(ShopifyStore.project_id == project_id)
        .options(
            selectinload(ShopifyStore.integration).selectinload(Integration.credential)
        )
    )
    return result.scalar_one_or_none()


async def get_shopify_client_for_store(
    store: ShopifyStore,
) -> ShopifyGraphQLClient:
    credential = store.integration.credential
    if credential is None or not credential.encrypted_payload:
        raise ShopifyAPIError("Credenziali Shopify non trovate per questo progetto")

    payload = json.loads(decrypt_secret(credential.encrypted_payload))
    return ShopifyGraphQLClient(
        shop_domain=payload["shop_domain"],
        access_token=payload["admin_access_token"],
    )


async def persist_shopify_connection(
    project_id: UUID,
    shop_domain: str,
    access_token: str,
    session: AsyncSession,
    *,
    shop_info: dict | None = None,
) -> ShopifyStore:
    normalized_domain = normalize_shop_domain(shop_domain)
    if shop_info is None:
        client = ShopifyGraphQLClient(normalized_domain, access_token)
        shop_info = await client.fetch_shop()

    result = await session.execute(
        select(Integration)
        .where(
            Integration.project_id == project_id,
            Integration.provider == "shopify",
        )
        .options(selectinload(Integration.credential))
    )
    integration = result.scalar_one_or_none()
    now = datetime.now(UTC)

    if integration is None:
        integration = Integration(
            project_id=project_id,
            provider="shopify",
            status="connected",
            connected_at=now,
        )
        session.add(integration)
        await session.flush()
    else:
        integration.status = "connected"
        integration.connected_at = now

    credential_payload = json.dumps(
        {
            "shop_domain": normalized_domain,
            "admin_access_token": access_token.strip(),
        }
    )

    if integration.credential is None:
        integration.credential = IntegrationCredential(
            integration_id=integration.id,
            encrypted_payload=encrypt_secret(credential_payload),
        )
        session.add(integration.credential)
    else:
        integration.credential.encrypted_payload = encrypt_secret(credential_payload)

    store_result = await session.execute(
        select(ShopifyStore).where(ShopifyStore.project_id == project_id)
    )
    store = store_result.scalar_one_or_none()

    if store is None:
        store = ShopifyStore(
            project_id=project_id,
            integration_id=integration.id,
            shop_domain=normalized_domain,
        )
        session.add(store)
    else:
        store.integration_id = integration.id
        store.shop_domain = normalized_domain

    store.shop_name = shop_info.get("name")
    store.currency = shop_info.get("currencyCode")
    store.timezone = shop_info.get("ianaTimezone")
    store.connection_status = "connected"

    await session.flush()
    await session.refresh(store)
    return store


async def connect_shopify(
    project_id: UUID,
    shop_domain: str,
    admin_access_token: str,
    session: AsyncSession,
) -> ShopifyStore:
    normalized_domain = normalize_shop_domain(shop_domain)
    client = ShopifyGraphQLClient(normalized_domain, admin_access_token)
    shop_info = await client.fetch_shop()
    return await persist_shopify_connection(
        project_id,
        normalized_domain,
        admin_access_token,
        session,
        shop_info=shop_info,
    )
