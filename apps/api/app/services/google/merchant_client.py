"""Google Merchant Center API client (Merchant API v1)."""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

import httpx

from app.services.google.exceptions import (
    GoogleApiRequestError,
    GoogleIntegrationNotConfiguredError,
    GoogleIntegrationPermissionError,
    MerchantAccountError,
)

logger = logging.getLogger(__name__)

MERCHANT_ACCOUNTS_API_BASE = "https://merchantapi.googleapis.com/accounts/v1"
MERCHANT_PRODUCTS_API_BASE = "https://merchantapi.googleapis.com/products/v1"
REQUEST_TIMEOUT_SECONDS = 60.0

ADVANCED_ACCOUNT_TYPES = {"ADVANCED_ACCOUNT", "MULTI_CLIENT_ACCOUNT", "MCA"}


def _auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def _extract_account_id(name: str | None) -> str | None:
    if not name:
        return None
    normalized = name.strip()
    if normalized.startswith("accounts/"):
        return normalized.split("/", 1)[1].split("/")[0] or None
    return normalized or None


def _map_http_error(
    status_code: int,
    *,
    account_id: str | None = None,
    response_text: str | None = None,
) -> Exception:
    if status_code in (401, 403):
        return GoogleIntegrationPermissionError(
            "Permessi insufficienti per Google Merchant Center.",
            status_code=status_code,
            integration="merchant_center",
        )
    if status_code == 404:
        return MerchantAccountError(
            "Account Merchant Center non trovato o non accessibile.",
            account_id=account_id,
        )
    if status_code == 403 and response_text and "API has not been used" in response_text:
        return GoogleIntegrationNotConfiguredError(
            "Merchant API non abilitata o progetto GCP non registrato. "
            "Abilita Merchant API e completa registerGcp nel Merchant Center.",
            integration="merchant_center",
        )
    return GoogleApiRequestError(
        "Google Merchant Center ha rifiutato la richiesta.",
        status_code=status_code,
        error_code="google_merchant_http_error",
    )


async def _get_json(
    url: str,
    access_token: str,
    *,
    account_id: str | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.get(
                url,
                headers=_auth_headers(access_token),
                params=params,
            )
    except httpx.TimeoutException as exc:
        raise GoogleApiRequestError(
            "Timeout durante la chiamata a Google Merchant Center.",
            error_code="google_merchant_timeout",
        ) from exc
    except httpx.HTTPError as exc:
        raise GoogleApiRequestError(
            "Impossibile contattare Google Merchant Center.",
            error_code="google_merchant_network_error",
        ) from exc

    if response.status_code >= 400:
        raise _map_http_error(
            response.status_code,
            account_id=account_id,
            response_text=response.text,
        )

    try:
        payload = response.json()
    except ValueError as exc:
        raise GoogleApiRequestError(
            "Risposta Merchant Center non valida.",
            error_code="google_merchant_invalid_json",
        ) from exc

    if not isinstance(payload, dict):
        return {}
    return payload


def _normalize_account_entry(entry: dict[str, Any], *, relationship: str) -> dict[str, Any] | None:
    name = entry.get("name")
    if not isinstance(name, str) or not name.strip():
        return None
    account_id = _extract_account_id(name)
    if not account_id:
        return None
    account_name = entry.get("accountName")
    display_name = account_name if isinstance(account_name, str) and account_name.strip() else account_id
    account_type = entry.get("accountType") or entry.get("type")
    return {
        "accountId": account_id,
        "name": name,
        "displayName": display_name,
        "type": account_type,
        "relationship": relationship,
    }


async def _fetch_subaccounts(
    access_token: str,
    provider_name: str,
) -> list[dict[str, Any]]:
    url = f"{MERCHANT_ACCOUNTS_API_BASE}/{provider_name}:listSubaccounts"
    subaccounts: list[dict[str, Any]] = []
    page_token: str | None = None
    while True:
        params: dict[str, Any] = {"pageSize": 250}
        if page_token:
            params["pageToken"] = page_token
        payload = await _get_json(url, access_token, params=params)
        for entry in payload.get("accounts", []):
            if isinstance(entry, dict):
                normalized = _normalize_account_entry(entry, relationship="subaccount")
                if normalized:
                    subaccounts.append(normalized)
        page_token = payload.get("nextPageToken")
        if not isinstance(page_token, str) or not page_token:
            break
    return subaccounts


async def fetch_merchant_accounts(access_token: str) -> list[dict[str, Any]]:
    url = f"{MERCHANT_ACCOUNTS_API_BASE}/accounts"
    accounts: list[dict[str, Any]] = []
    page_token: str | None = None

    while True:
        params: dict[str, Any] = {"pageSize": 250}
        if page_token:
            params["pageToken"] = page_token
        payload = await _get_json(url, access_token, params=params)
        for entry in payload.get("accounts", []):
            if not isinstance(entry, dict):
                continue
            normalized = _normalize_account_entry(entry, relationship="primary")
            if not normalized:
                continue
            accounts.append(normalized)
            account_type = str(normalized.get("type") or "").upper()
            if account_type in ADVANCED_ACCOUNT_TYPES or "ADVANCED" in account_type:
                try:
                    subaccounts = await _fetch_subaccounts(access_token, normalized["name"])
                    accounts.extend(subaccounts)
                except Exception:
                    logger.warning(
                        "Unable to list subaccounts for merchant account_id=%s",
                        normalized.get("accountId"),
                    )
        page_token = payload.get("nextPageToken")
        if not isinstance(page_token, str) or not page_token:
            break

    deduped: dict[str, dict[str, Any]] = {}
    for account in accounts:
        deduped[account["accountId"]] = account
    result = list(deduped.values())
    logger.info("Fetched merchant accounts count=%s", len(result))
    return result


def _parse_price_value(value: Any) -> tuple[float | None, str | None]:
    if not isinstance(value, dict):
        return None, None
    amount = value.get("amountMicros") or value.get("amount")
    currency = value.get("currencyCode") or value.get("currency")
    if amount is None:
        return None, currency if isinstance(currency, str) else None
    try:
        if isinstance(amount, (int, float)):
            if isinstance(amount, int) and amount > 1_000_000:
                parsed = float(Decimal(amount) / Decimal(1_000_000))
            else:
                parsed = float(amount)
        elif isinstance(amount, str):
            parsed = float(amount)
        else:
            return None, currency if isinstance(currency, str) else None
        return parsed, currency if isinstance(currency, str) else None
    except (ValueError, ArithmeticError):
        return None, currency if isinstance(currency, str) else None


def _normalize_product_status(product_status: dict[str, Any] | None) -> tuple[str, list[dict], list[dict]]:
    if not product_status:
        return "unknown", [], []

    destination_statuses: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    aggregated = "unknown"

    for destination in product_status.get("destinationStatuses", []) or []:
        if not isinstance(destination, dict):
            continue
        destination_statuses.append(
            {
                "destination": destination.get("reportingContext") or destination.get("destination"),
                "status": destination.get("status"),
                "approvedCountries": destination.get("approvedCountries"),
                "pendingCountries": destination.get("pendingCountries"),
                "disapprovedCountries": destination.get("disapprovedCountries"),
            }
        )
        status_value = str(destination.get("status") or "").upper()
        if status_value in {"NOT_ELIGIBLE_OR_DISAPPROVED", "DISAPPROVED"}:
            aggregated = "disapproved"
        elif status_value in {"PENDING", "LIMITED"} and aggregated != "disapproved":
            aggregated = "limited"
        elif status_value in {"ELIGIBLE", "APPROVED"} and aggregated == "unknown":
            aggregated = "approved"

    for issue in product_status.get("itemLevelIssues", []) or []:
        if not isinstance(issue, dict):
            continue
        issues.append(
            {
                "code": issue.get("code"),
                "severity": issue.get("severity") or issue.get("servability"),
                "destination": issue.get("reportingContext") or issue.get("destination"),
                "description": issue.get("description") or issue.get("detail"),
                "detail": issue.get("detail"),
                "documentation": issue.get("documentation") or issue.get("documentationUri"),
            }
        )

    if aggregated == "unknown" and issues:
        severities = {str(issue.get("severity") or "").upper() for issue in issues}
        if "DISAPPROVED" in severities or "NOT_ELIGIBLE" in severities:
            aggregated = "disapproved"
        elif "PENDING" in severities or "LIMITED" in severities:
            aggregated = "limited"

    return aggregated, destination_statuses, issues


def _normalize_product_entry(entry: dict[str, Any]) -> dict[str, Any] | None:
    name = entry.get("name")
    offer_id = entry.get("offerId")
    if not isinstance(name, str) or not name.strip():
        return None
    if not isinstance(offer_id, str) or not offer_id.strip():
        offer_id = name.split("/")[-1] if "/" in name else name

    attributes = entry.get("attributes") if isinstance(entry.get("attributes"), dict) else {}
    product_status = entry.get("productStatus") if isinstance(entry.get("productStatus"), dict) else {}
    status, destination_statuses, issues = _normalize_product_status(product_status)

    price_value = attributes.get("price")
    price, currency = _parse_price_value(price_value)

    return {
        "merchantProductId": name,
        "offerId": offer_id,
        "title": attributes.get("title"),
        "link": attributes.get("link"),
        "availability": attributes.get("availability"),
        "price": price,
        "currency": currency,
        "brand": attributes.get("brand"),
        "gtin": attributes.get("gtin"),
        "mpn": attributes.get("mpn"),
        "imageLink": attributes.get("imageLink") or attributes.get("image_link"),
        "contentLanguage": entry.get("contentLanguage"),
        "targetCountry": entry.get("feedLabel") or attributes.get("targetCountry"),
        "channel": entry.get("channel"),
        "feedLabel": entry.get("feedLabel"),
        "condition": attributes.get("condition"),
        "status": status,
        "destinationStatuses": destination_statuses,
        "issues": issues,
    }


async def fetch_merchant_products_with_issues(
    access_token: str,
    *,
    account_id: str,
    page_size: int = 250,
) -> list[dict[str, Any]]:
    parent = f"accounts/{account_id}"
    url = f"{MERCHANT_PRODUCTS_API_BASE}/{parent}/products"
    products: list[dict[str, Any]] = []
    page_token: str | None = None

    while True:
        params: dict[str, Any] = {"pageSize": page_size}
        if page_token:
            params["pageToken"] = page_token
        payload = await _get_json(url, access_token, account_id=account_id, params=params)
        for entry in payload.get("products", []):
            if not isinstance(entry, dict):
                continue
            normalized = _normalize_product_entry(entry)
            if normalized:
                products.append(normalized)
        page_token = payload.get("nextPageToken")
        if not isinstance(page_token, str) or not page_token:
            break

    logger.info(
        "Fetched merchant products account_id=%s count=%s",
        account_id,
        len(products),
    )
    return products
