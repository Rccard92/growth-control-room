import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.google_integration import (
    GoogleAnalyticsPropertiesResponse,
    GoogleAnalyticsProperty,
    GoogleIntegrationStatusResponse,
    GoogleOAuthStartRequest,
    GoogleOAuthStartResponse,
    GoogleSearchConsoleSite,
    GoogleSearchConsoleSitesResponse,
    GoogleMerchantAccount,
    GoogleMerchantAccountsResponse,
    SelectGoogleMerchantAccountRequest,
    SelectGoogleMerchantAccountResponse,
    SelectGoogleAnalyticsPropertyRequest,
    SelectGoogleAnalyticsPropertyResponse,
    SelectSearchConsoleSiteRequest,
    SelectSearchConsoleSiteResponse,
)
from app.schemas.project import ProjectRead
from app.services.google.exceptions import (
    GoogleAnalyticsPropertyError,
    GoogleApiRequestError,
    GoogleIntegrationNotConfiguredError,
    GoogleIntegrationNotConnectedError,
    GoogleIntegrationPermissionError,
    GoogleIntegrationReconnectRequiredError,
    GoogleSearchConsolePropertyError,
    MerchantAccountError,
)
from app.services.google.google_integrations import (
    ensure_google_provider_credential_from_existing_scope,
    get_google_integration_status,
    persist_google_oauth_tokens,
)
from app.services.google.google_oauth import (
    build_google_oauth_authorization_url,
    ensure_google_oauth_configured,
    exchange_google_oauth_code,
    frontend_redirect_url,
    verify_google_oauth_state,
)
from app.services.google.google_scope_utils import (
    get_google_scopes_for_reconnect,
    normalize_oauth_mode,
    normalize_oauth_provider,
    resolve_oauth_prompt,
)
from app.services.google.google_tokens import get_valid_google_access_token
from app.services.google.analytics_client import fetch_ga4_account_summaries
from app.services.google.merchant_client import fetch_merchant_accounts
from app.services.google.search_console_client import fetch_search_console_sites
from app.services.projects import get_project_in_default_workspace

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["google-integrations"])
callback_router = APIRouter(prefix="/google/oauth", tags=["google-oauth"])


def _redirect_error(project_id: UUID | None, error_code: str) -> RedirectResponse:
    if project_id is None:
        return RedirectResponse(
            url=frontend_redirect_url(f"/projects?google_error={error_code}"),
            status_code=302,
        )
    return RedirectResponse(
        url=frontend_redirect_url(
            f"/projects/{project_id}/integrations?google_error={error_code}"
        ),
        status_code=302,
    )


def _map_google_integration_error(exc: Exception) -> HTTPException:
    if isinstance(exc, GoogleIntegrationReconnectRequiredError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "google_reconnect_required",
                "provider": exc.provider,
                "message": str(exc),
            },
        )
    if isinstance(exc, GoogleIntegrationNotConnectedError):
        return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    if isinstance(exc, GoogleIntegrationNotConfiguredError):
        return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    if isinstance(exc, GoogleIntegrationPermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, GoogleSearchConsolePropertyError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, GoogleAnalyticsPropertyError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, MerchantAccountError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, GoogleApiRequestError):
        return HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))
    if isinstance(exc, HTTPException):
        return exc
    logger.exception("Unexpected Google integration error")
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Operazione Google non riuscita.",
    )


@router.get(
    "/{project_id}/google/search-console/sites",
    response_model=GoogleSearchConsoleSitesResponse,
    response_model_by_alias=True,
)
async def list_search_console_sites(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> GoogleSearchConsoleSitesResponse:
    await get_project_in_default_workspace(project_id, session)
    try:
        access_token = await get_valid_google_access_token(
            session,
            project_id,
            provider="google_search_console",
        )
        sites = await fetch_search_console_sites(access_token)
    except Exception as exc:
        raise _map_google_integration_error(exc) from exc

    return GoogleSearchConsoleSitesResponse(
        sites=[
            GoogleSearchConsoleSite(
                site_url=site["siteUrl"],
                permission_level=site.get("permissionLevel"),
            )
            for site in sites
        ]
    )


@router.post(
    "/{project_id}/google/search-console/select-site",
    response_model=SelectSearchConsoleSiteResponse,
    response_model_by_alias=True,
)
async def select_search_console_site(
    project_id: UUID,
    body: SelectSearchConsoleSiteRequest,
    session: AsyncSession = Depends(get_db),
) -> SelectSearchConsoleSiteResponse:
    project = await get_project_in_default_workspace(project_id, session)
    site_url = body.site_url.strip()
    if not site_url:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="siteUrl obbligatorio.",
        )

    try:
        access_token = await get_valid_google_access_token(
            session,
            project_id,
            provider="google_search_console",
        )
        available_sites = await fetch_search_console_sites(access_token)
        available_urls = {site["siteUrl"] for site in available_sites}
        if available_urls and site_url not in available_urls:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="La proprietà Search Console selezionata non è disponibile per questo account.",
            )
    except HTTPException:
        raise
    except Exception as exc:
        raise _map_google_integration_error(exc) from exc

    project.search_console_site_url = site_url
    session.add(project)
    await session.commit()
    await session.refresh(project)

    return SelectSearchConsoleSiteResponse(
        site_url=project.search_console_site_url or site_url,
        message="Proprietà Search Console salvata.",
    )


@router.get(
    "/{project_id}/google/analytics/properties",
    response_model=GoogleAnalyticsPropertiesResponse,
    response_model_by_alias=True,
)
async def list_google_analytics_properties(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> GoogleAnalyticsPropertiesResponse:
    await get_project_in_default_workspace(project_id, session)
    try:
        access_token = await get_valid_google_access_token(
            session,
            project_id,
            provider="ga4",
        )
        properties = await fetch_ga4_account_summaries(access_token)
    except Exception as exc:
        raise _map_google_integration_error(exc) from exc

    return GoogleAnalyticsPropertiesResponse(
        properties=[
            GoogleAnalyticsProperty(
                property_id=item["propertyId"],
                property_name=item["property"],
                display_name=item["propertyDisplayName"],
                account_display_name=item.get("accountDisplayName"),
            )
            for item in properties
        ]
    )


@router.post(
    "/{project_id}/google/analytics/select-property",
    response_model=SelectGoogleAnalyticsPropertyResponse,
    response_model_by_alias=True,
)
async def select_google_analytics_property(
    project_id: UUID,
    body: SelectGoogleAnalyticsPropertyRequest,
    session: AsyncSession = Depends(get_db),
) -> SelectGoogleAnalyticsPropertyResponse:
    project = await get_project_in_default_workspace(project_id, session)
    property_id = body.property_id.strip()
    property_name = body.property_name.strip()
    display_name = body.display_name.strip()
    if not property_id or not property_name or not display_name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="propertyId, propertyName e displayName sono obbligatori.",
        )

    try:
        access_token = await get_valid_google_access_token(
            session,
            project_id,
            provider="ga4",
        )
        available_properties = await fetch_ga4_account_summaries(access_token)
        available_ids = {item["propertyId"] for item in available_properties}
        if available_ids and property_id not in available_ids:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="La proprietà GA4 selezionata non è disponibile per questo account.",
            )
    except HTTPException:
        raise
    except Exception as exc:
        raise _map_google_integration_error(exc) from exc

    project.google_analytics_property_id = property_id
    project.google_analytics_property_name = display_name
    session.add(project)
    await session.commit()
    await session.refresh(project)

    return SelectGoogleAnalyticsPropertyResponse(
        property_id=project.google_analytics_property_id or property_id,
        property_name=property_name,
        display_name=project.google_analytics_property_name or display_name,
        message="Proprietà GA4 salvata.",
    )


@router.get(
    "/{project_id}/google/merchant/accounts",
    response_model=GoogleMerchantAccountsResponse,
    response_model_by_alias=True,
)
async def list_merchant_accounts(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> GoogleMerchantAccountsResponse:
    await get_project_in_default_workspace(project_id, session)
    try:
        await ensure_google_provider_credential_from_existing_scope(
            session,
            project_id,
            provider="merchant_center",
        )
        access_token = await get_valid_google_access_token(
            session,
            project_id,
            provider="merchant_center",
        )
        accounts = await fetch_merchant_accounts(access_token)
    except Exception as exc:
        raise _map_google_integration_error(exc) from exc

    return GoogleMerchantAccountsResponse(
        accounts=[
            GoogleMerchantAccount(
                account_id=account["accountId"],
                name=account["name"],
                display_name=account["displayName"],
                type=account.get("type"),
                relationship=account.get("relationship"),
            )
            for account in accounts
        ]
    )


@router.post(
    "/{project_id}/google/merchant/select-account",
    response_model=SelectGoogleMerchantAccountResponse,
    response_model_by_alias=True,
)
async def select_merchant_account(
    project_id: UUID,
    body: SelectGoogleMerchantAccountRequest,
    session: AsyncSession = Depends(get_db),
) -> SelectGoogleMerchantAccountResponse:
    project = await get_project_in_default_workspace(project_id, session)
    account_id = body.account_id.strip()
    account_name = body.account_name.strip()
    if not account_id or not account_name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="accountId e accountName sono obbligatori.",
        )

    try:
        access_token = await get_valid_google_access_token(
            session,
            project_id,
            provider="merchant_center",
        )
        available_accounts = await fetch_merchant_accounts(access_token)
        available_ids = {account["accountId"] for account in available_accounts}
        if available_ids and account_id not in available_ids:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="L'account Merchant selezionato non è disponibile per questo account Google.",
            )
    except HTTPException:
        raise
    except Exception as exc:
        raise _map_google_integration_error(exc) from exc

    project.google_merchant_account_id = account_id
    project.google_merchant_account_name = account_name
    session.add(project)
    await session.commit()
    await session.refresh(project)

    return SelectGoogleMerchantAccountResponse(
        account_id=project.google_merchant_account_id or account_id,
        message="Account Merchant Center salvato.",
    )


@router.get(
    "/{project_id}/google/status",
    response_model=GoogleIntegrationStatusResponse,
    response_model_by_alias=True,
)
async def get_google_status(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> GoogleIntegrationStatusResponse:
    await get_project_in_default_workspace(project_id, session)
    return await get_google_integration_status(session, project_id)


@router.post(
    "/{project_id}/google/oauth/start",
    response_model=GoogleOAuthStartResponse,
    response_model_by_alias=True,
)
async def start_google_oauth(
    project_id: UUID,
    body: GoogleOAuthStartRequest | None = None,
    session: AsyncSession = Depends(get_db),
) -> GoogleOAuthStartResponse:
    await get_project_in_default_workspace(project_id, session)
    ensure_google_oauth_configured()

    request_body = body or GoogleOAuthStartRequest()
    provider = normalize_oauth_provider(request_body.provider)
    if request_body.services and not request_body.provider:
        provider = "all"
    mode = normalize_oauth_mode(request_body.mode)
    scopes = get_google_scopes_for_reconnect(provider)
    prompt = resolve_oauth_prompt(mode)

    authorization_url = build_google_oauth_authorization_url(
        project_id,
        scopes=scopes,
        provider=provider,
        mode=mode,
        prompt=prompt,
    )
    return GoogleOAuthStartResponse(authorization_url=authorization_url)


@callback_router.get("/callback")
async def google_oauth_callback(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    query_params = dict(request.query_params)
    error = query_params.get("error")
    state_value = query_params.get("state")
    code = query_params.get("code")
    project_id: UUID | None = None
    oauth_state = None

    if state_value:
        oauth_state = verify_google_oauth_state(state_value)
        if oauth_state is not None:
            project_id = oauth_state.project_id

    if error:
        logger.warning("Google OAuth callback error: %s", error)
        return _redirect_error(project_id, error)

    if not state_value or not code or project_id is None or oauth_state is None:
        return _redirect_error(project_id, "invalid_state")

    try:
        await get_project_in_default_workspace(project_id, session)
        token_data = await exchange_google_oauth_code(code)
        await persist_google_oauth_tokens(
            session,
            project_id,
            token_data,
            requested_provider=oauth_state.provider,
            mode=oauth_state.mode,
        )
    except HTTPException as exc:
        logger.warning("Google OAuth callback failed for project %s: %s", project_id, exc.detail)
        return _redirect_error(project_id, "connection_failed")
    except Exception:
        logger.exception("Google OAuth callback unexpected error for project %s", project_id)
        return _redirect_error(project_id, "connection_failed")

    return RedirectResponse(
        url=frontend_redirect_url(f"/projects/{project_id}/integrations?google_connected=1"),
        status_code=302,
    )
