"""Shopify OAuth scope verification against saved access tokens."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.shopify import ShopifyStore
from app.services.shopify.client import ShopifyAPIError, ShopifyGraphQLClient
from app.services.shopify.exceptions import ShopifyIntegrationPermissionError

REQUIRED_FOR_APPLY = ["write_products"]
REQUIRED_FOR_PUBLISH = ["write_content"]
REQUIRED_FOR_IMAGE_UPLOAD = ["write_files"]
# read_orders is in default SHOPIFY_SCOPES; reconnect only if token predates scope update.
REQUIRED_FOR_COMMERCE_ANALYSIS = ["read_orders", "read_products"]
COMMERCE_PERMISSION_MESSAGE = (
    "Permessi Shopify insufficienti per leggere vendite e revenue. "
    "Riconnetti Shopify con permessi ordini."
)
IMAGE_UPLOAD_FALLBACK_SCOPES = ["write_images"]
SCOPES_CACHE_TTL = timedelta(hours=1)


def configured_scopes() -> list[str]:
    return sorted(
        {s.strip() for s in settings.shopify_scopes.split(",") if s.strip()}
    )


def parse_scope_string(scope_value: str | None) -> list[str]:
    if not scope_value:
        return []
    return sorted({s.strip() for s in scope_value.split(",") if s.strip()})


async def fetch_granted_scopes(shop_domain: str, access_token: str) -> list[str]:
    client = ShopifyGraphQLClient(shop_domain, access_token)
    return await client.fetch_access_scopes()


def _scope_message(
    *,
    configured: list[str],
    granted: list[str],
    missing: list[str],
    verify_failed: bool,
) -> str:
    if verify_failed:
        return "Verifica permessi Shopify non riuscita. Riprova o riconnetti lo shop."
    if "write_products" in granted:
        return "write_products autorizzato sul token Shopify corrente."
    if "write_products" in configured:
        return (
            "Il token Shopify corrente non include write_products. "
            "Riconnetti Shopify per autorizzare i nuovi permessi."
        )
    return (
        "write_products non è configurato in SHOPIFY_SCOPES. "
        "Aggiorna la variabile su Railway e redeploy, poi riconnetti Shopify."
    )


def _has_image_upload_scope(granted: list[str]) -> bool:
    if "write_files" in granted:
        return True
    return any(scope in granted for scope in IMAGE_UPLOAD_FALLBACK_SCOPES)


def build_scope_result(
    *,
    shop_domain: str,
    configured: list[str],
    granted: list[str],
    verify_failed: bool = False,
) -> dict[str, Any]:
    missing_apply = [s for s in REQUIRED_FOR_APPLY if s not in granted]
    missing_publish = [s for s in REQUIRED_FOR_PUBLISH if s not in granted]
    missing_image_upload = [
        s for s in REQUIRED_FOR_IMAGE_UPLOAD if s not in granted and not _has_image_upload_scope(granted)
    ]
    can_write_products = "write_products" in granted and not verify_failed
    can_write_content = "write_content" in granted and not verify_failed
    can_write_files = _has_image_upload_scope(granted) and not verify_failed
    requires_reconnect = (
        not verify_failed
        and (
            ("write_products" in configured and "write_products" not in granted)
            or ("write_content" in configured and "write_content" not in granted)
            or (
                any(scope in configured for scope in REQUIRED_FOR_IMAGE_UPLOAD + IMAGE_UPLOAD_FALLBACK_SCOPES)
                and not _has_image_upload_scope(granted)
            )
        )
    )
    message = _scope_message(
        configured=configured,
        granted=granted,
        missing=missing_apply,
        verify_failed=verify_failed,
    )
    return {
        "shop_domain": shop_domain,
        "configured_scopes": configured,
        "granted_scopes": granted,
        "required_for_apply": list(REQUIRED_FOR_APPLY),
        "required_for_publish": list(REQUIRED_FOR_PUBLISH),
        "required_for_image_upload": list(REQUIRED_FOR_IMAGE_UPLOAD),
        "missing_scopes": missing_apply,
        "missing_publish_scopes": missing_publish,
        "missing_image_upload_scopes": missing_image_upload,
        "can_write_products": can_write_products,
        "can_write_content": can_write_content,
        "can_write_files": can_write_files,
        "requires_reconnect": requires_reconnect,
        "message": message,
    }


async def _load_access_token(store: ShopifyStore) -> tuple[str, str]:
    credential = store.integration.credential
    if credential is None or not credential.encrypted_payload:
        raise ShopifyAPIError("Credenziali Shopify non trovate per questo progetto")
    import json

    from app.services.encryption import decrypt_secret

    payload = json.loads(decrypt_secret(credential.encrypted_payload))
    shop_domain = payload["shop_domain"]
    access_token = payload["admin_access_token"]
    return shop_domain, access_token


def _cache_fresh(store: ShopifyStore) -> bool:
    if not store.scopes_checked_at or not store.granted_scopes:
        return False
    checked = store.scopes_checked_at
    if checked.tzinfo is None:
        checked = checked.replace(tzinfo=UTC)
    return datetime.now(UTC) - checked < SCOPES_CACHE_TTL


async def resolve_shopify_scopes(
    store: ShopifyStore,
    session: AsyncSession,
    *,
    force_refresh: bool = False,
) -> dict[str, Any]:
    configured = configured_scopes()
    if (
        not force_refresh
        and _cache_fresh(store)
        and store.granted_scopes is not None
    ):
        return build_scope_result(
            shop_domain=store.shop_domain,
            configured=configured,
            granted=sorted(store.granted_scopes),
        )

    try:
        shop_domain, access_token = await _load_access_token(store)
        granted = await fetch_granted_scopes(shop_domain, access_token)
        store.granted_scopes = granted
        store.scopes_checked_at = datetime.now(UTC)
        await session.flush()
        return build_scope_result(
            shop_domain=shop_domain,
            configured=configured,
            granted=granted,
        )
    except (ShopifyAPIError, httpx.HTTPError, KeyError, ValueError):
        cached = sorted(store.granted_scopes or [])
        if cached:
            return build_scope_result(
                shop_domain=store.shop_domain,
                configured=configured,
                granted=cached,
                verify_failed=True,
            )
        return build_scope_result(
            shop_domain=store.shop_domain,
            configured=configured,
            granted=[],
            verify_failed=True,
        )


async def can_apply_with_write_products(
    store: ShopifyStore,
    session: AsyncSession,
) -> dict[str, Any]:
    result = await resolve_shopify_scopes(store, session, force_refresh=True)
    if result["can_write_products"]:
        return {"allowed": True, **result}
    return {
        "allowed": False,
        "applied": False,
        "requires_scope": "write_products",
        "requires_reconnect": result["requires_reconnect"],
        "message": result["message"],
        **result,
    }


async def can_publish_with_write_content(
    store: ShopifyStore,
    session: AsyncSession,
) -> dict[str, Any]:
    result = await resolve_shopify_scopes(store, session, force_refresh=True)
    if result["can_write_content"]:
        return {"allowed": True, **result}
    return {
        "allowed": False,
        "requires_scope": "write_content",
        "requires_reconnect": result["requires_reconnect"],
        "message": (
            "Serve il permesso Shopify write_content. "
            "Riconnetti Shopify con gli scope aggiornati."
        ),
        **result,
    }


async def assert_commerce_scopes_granted(
    store: ShopifyStore,
    session: AsyncSession,
) -> list[str]:
    """Verify read_orders/read_products are granted; raise if missing."""
    result = await resolve_shopify_scopes(store, session, force_refresh=True)
    granted = result.get("granted_scopes") or []
    missing = [s for s in REQUIRED_FOR_COMMERCE_ANALYSIS if s not in granted]
    if missing:
        raise ShopifyIntegrationPermissionError(
            COMMERCE_PERMISSION_MESSAGE,
            missing_scopes=missing,
        )
    return granted


async def can_upload_shopify_files(
    store: ShopifyStore,
    session: AsyncSession,
) -> dict[str, Any]:
    result = await resolve_shopify_scopes(store, session, force_refresh=True)
    if result["can_write_files"]:
        return {"allowed": True, **result}
    return {
        "allowed": False,
        "requires_scope": "write_files",
        "missing_scopes": result.get("missing_image_upload_scopes") or [],
        "requires_reconnect": result["requires_reconnect"],
        "message": (
            "Per caricare immagini su Shopify serve il permesso write_files o write_images. "
            "Aggiorna gli scope della Custom App Shopify."
        ),
        **result,
    }
