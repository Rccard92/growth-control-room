import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.google_integration import (
    GoogleIntegrationStatusResponse,
    GoogleOAuthStartRequest,
    GoogleOAuthStartResponse,
)
from app.services.google.google_integrations import (
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
    authorization_url = build_google_oauth_authorization_url(project_id)
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

    if state_value:
        project_id = verify_google_oauth_state(state_value)

    if error:
        logger.warning("Google OAuth callback error: %s", error)
        return _redirect_error(project_id, error)

    if not state_value or not code or project_id is None:
        return _redirect_error(project_id, "invalid_state")

    try:
        await get_project_in_default_workspace(project_id, session)
        token_data = await exchange_google_oauth_code(code)
        await persist_google_oauth_tokens(session, project_id, token_data)
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
