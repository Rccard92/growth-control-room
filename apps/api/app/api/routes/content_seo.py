from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.content_seo import (
    ContentSeoAnalyzeResponse,
    ContentSeoDashboardResponse,
    ContentSeoSyncResponse,
)
from app.services.content.analyze import run_content_seo_analyze
from app.services.content.dashboard import build_content_seo_dashboard
from app.services.projects import get_project_in_default_workspace
from app.services.shopify.client import ShopifyAPIError
from app.services.shopify.connect import get_shopify_client_for_store, get_shopify_store_for_project
from app.services.shopify.content_sync import sync_shopify_content

router = APIRouter(prefix="/projects", tags=["content-seo"])


def _map_shopify_error(exc: ShopifyAPIError) -> HTTPException:
    code = exc.status_code or status.HTTP_400_BAD_REQUEST
    if code == 401:
        code = status.HTTP_401_UNAUTHORIZED
    elif code == 403:
        code = status.HTTP_403_FORBIDDEN
    return HTTPException(status_code=code, detail=exc.message)


def _require_connected_store(store):
    if store is None or store.connection_status != "connected":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shopify non collegato per questo progetto",
        )
    return store


@router.post(
    "/{project_id}/content/seo/sync-shopify",
    response_model=ContentSeoSyncResponse,
    response_model_by_alias=True,
)
async def content_seo_sync_shopify(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> ContentSeoSyncResponse:
    await get_project_in_default_workspace(project_id, session)
    store = _require_connected_store(await get_shopify_store_for_project(project_id, session))

    try:
        client = await get_shopify_client_for_store(store)
        result = await sync_shopify_content(store, client, session)
    except ShopifyAPIError as exc:
        raise _map_shopify_error(exc) from exc

    return ContentSeoSyncResponse(
        collections_synced=result.collections_synced,
        pages_synced=result.pages_synced,
        blogs_synced=result.blogs_synced,
        articles_synced=result.articles_synced,
        duration_seconds=result.duration_seconds,
    )


@router.post(
    "/{project_id}/content/seo/analyze",
    response_model=ContentSeoAnalyzeResponse,
    response_model_by_alias=True,
)
async def content_seo_analyze(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> ContentSeoAnalyzeResponse:
    await get_project_in_default_workspace(project_id, session)
    store = _require_connected_store(await get_shopify_store_for_project(project_id, session))

    result = await run_content_seo_analyze(store, session)
    return ContentSeoAnalyzeResponse(
        issues_created=result.issues_created,
        opportunities_created=result.opportunities_created,
        critical_issues=result.critical_issues,
        high_priority_opportunities=result.high_priority_opportunities,
    )


@router.get(
    "/{project_id}/content/seo/dashboard",
    response_model=ContentSeoDashboardResponse,
    response_model_by_alias=True,
)
async def content_seo_dashboard(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> ContentSeoDashboardResponse:
    await get_project_in_default_workspace(project_id, session)
    store = await get_shopify_store_for_project(project_id, session)
    if store is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shopify non collegato per questo progetto",
        )

    data = await build_content_seo_dashboard(store, session)
    return ContentSeoDashboardResponse.model_validate(data)
