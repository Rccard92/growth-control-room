import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.services.shopify.client import ShopifyAPIError, normalize_shop_domain
from app.services.shopify.connect import persist_shopify_connection
from app.services.shopify.oauth import (
    consume_oauth_state,
    ensure_shopify_oauth_configured,
    exchange_code_for_access_token,
    frontend_redirect_url,
    verify_shopify_hmac,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integrations/shopify/oauth", tags=["shopify-oauth"])


def _redirect_error(project_id: UUID | None, error_code: str) -> RedirectResponse:
    if project_id is None:
        return RedirectResponse(
            url=frontend_redirect_url(f"/projects?shopify_error={error_code}"),
            status_code=302,
        )
    return RedirectResponse(
        url=frontend_redirect_url(
            f"/projects/{project_id}/shopify?shopify_error={error_code}"
        ),
        status_code=302,
    )


@router.get("/callback")
async def shopify_oauth_callback(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    if not settings.shopify_oauth_configured:
        return RedirectResponse(
            url=frontend_redirect_url("/projects?shopify_error=oauth_not_configured"),
            status_code=302,
        )

    query_params = {key: value for key, value in request.query_params.multi_items()}
    state_value = query_params.get("state")
    code = query_params.get("code")
    shop = query_params.get("shop")
    project_id: UUID | None = None

    if not state_value or not code or not shop:
        return _redirect_error(project_id, "missing_params")

    oauth_state = await consume_oauth_state(session, state_value)
    if oauth_state is None:
        return _redirect_error(project_id, "invalid_state")

    project_id = oauth_state.project_id

    if not verify_shopify_hmac(query_params, settings.shopify_client_secret or ""):
        logger.warning("Shopify OAuth callback: HMAC non valido per project %s", project_id)
        return _redirect_error(project_id, "hmac_invalid")

    try:
        shop_domain = normalize_shop_domain(shop)
    except ShopifyAPIError:
        return _redirect_error(project_id, "invalid_shop")

    if shop_domain != oauth_state.shop_domain:
        logger.warning(
            "Shopify OAuth callback: shop mismatch (state=%s, callback=%s)",
            oauth_state.shop_domain,
            shop_domain,
        )
        return _redirect_error(project_id, "invalid_shop")

    try:
        access_token = await exchange_code_for_access_token(shop_domain, code)
        await persist_shopify_connection(
            project_id,
            shop_domain,
            access_token,
            session,
        )
    except ShopifyAPIError as exc:
        logger.exception(
            "Shopify OAuth callback: errore persistenza connessione per project %s",
            project_id,
        )
        error_code = "token_exchange_failed"
        if exc.status_code and exc.status_code >= 500:
            error_code = "shopify_unavailable"
        return _redirect_error(project_id, error_code)
    except Exception:
        logger.exception(
            "Shopify OAuth callback: errore imprevisto per project %s",
            project_id,
        )
        return _redirect_error(project_id, "connection_failed")

    return RedirectResponse(
        url=frontend_redirect_url(
            f"/projects/{project_id}/shopify?shopify_connected=1"
        ),
        status_code=302,
    )
