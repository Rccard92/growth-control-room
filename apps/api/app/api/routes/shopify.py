from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.shopify import ShopifyOrder, ShopifyProduct
from app.schemas.shopify import (
    ShopifyConnectRequest,
    ShopifyConnectResponse,
    ShopifyDashboardResponse,
    ShopifyOAuthStartResponse,
    ShopifyOrderRead,
    ShopifyProductRead,
    ShopifyReconciliationDebugResponse,
    ShopifyStatusResponse,
    ShopifySyncResponse,
)
from app.services.projects import get_project_in_default_workspace
from app.services.shopify.client import ShopifyAPIError, normalize_shop_domain
from app.services.shopify.connect import connect_shopify, get_shopify_client_for_store, get_shopify_store_for_project
from app.services.shopify.oauth import (
    build_authorization_url,
    create_oauth_state,
    ensure_shopify_oauth_configured,
)
from app.services.shopify.dashboard import build_dashboard
from app.services.shopify.period import resolve_period_pair
from app.services.shopify.reconciliation import build_reconciliation_debug
from app.services.shopify.sync import sync_shopify_store

router = APIRouter(prefix="/projects", tags=["shopify"])


def _map_shopify_error(exc: ShopifyAPIError) -> HTTPException:
    code = exc.status_code or status.HTTP_400_BAD_REQUEST
    if code == 401:
        code = status.HTTP_401_UNAUTHORIZED
    elif code == 403:
        code = status.HTTP_403_FORBIDDEN
    return HTTPException(status_code=code, detail=exc.message)


@router.get(
    "/{project_id}/integrations/shopify/oauth/start",
    response_model=ShopifyOAuthStartResponse,
    response_model_by_alias=True,
)
async def shopify_oauth_start(
    project_id: UUID,
    shop: str,
    session: AsyncSession = Depends(get_db),
) -> ShopifyOAuthStartResponse:
    ensure_shopify_oauth_configured()
    await get_project_in_default_workspace(project_id, session)
    try:
        shop_domain = normalize_shop_domain(shop)
    except ShopifyAPIError as exc:
        raise _map_shopify_error(exc) from exc

    oauth_state = await create_oauth_state(session, project_id, shop_domain)
    authorization_url = build_authorization_url(shop_domain, oauth_state.state)
    return ShopifyOAuthStartResponse(authorization_url=authorization_url)


@router.post(
    "/{project_id}/integrations/shopify/connect",
    response_model=ShopifyConnectResponse,
    response_model_by_alias=True,
)
async def shopify_connect(
    project_id: UUID,
    body: ShopifyConnectRequest,
    session: AsyncSession = Depends(get_db),
) -> ShopifyConnectResponse:
    await get_project_in_default_workspace(project_id, session)
    try:
        store = await connect_shopify(
            project_id,
            body.shop_domain,
            body.admin_access_token,
            session,
        )
    except ShopifyAPIError as exc:
        raise _map_shopify_error(exc) from exc

    return ShopifyConnectResponse(
        connected=True,
        shop_domain=store.shop_domain,
        shop_name=store.shop_name,
        connection_status=store.connection_status,
    )


@router.get(
    "/{project_id}/shopify/status",
    response_model=ShopifyStatusResponse,
    response_model_by_alias=True,
)
async def shopify_status(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> ShopifyStatusResponse:
    await get_project_in_default_workspace(project_id, session)
    store = await get_shopify_store_for_project(project_id, session)

    if store is None or store.connection_status != "connected":
        return ShopifyStatusResponse(connected=False)

    return ShopifyStatusResponse(
        connected=True,
        shop_domain=store.shop_domain,
        shop_name=store.shop_name,
        last_sync_at=store.last_sync_at,
    )


@router.post(
    "/{project_id}/shopify/sync",
    response_model=ShopifySyncResponse,
    response_model_by_alias=True,
)
async def shopify_sync(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> ShopifySyncResponse:
    await get_project_in_default_workspace(project_id, session)
    store = await get_shopify_store_for_project(project_id, session)

    if store is None or store.connection_status != "connected":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Shopify non connesso per questo progetto",
        )

    try:
        client = await get_shopify_client_for_store(store)
        counts = await sync_shopify_store(store, client, session)
    except ShopifyAPIError as exc:
        raise _map_shopify_error(exc) from exc

    await session.refresh(store)
    return ShopifySyncResponse(
        products_synced=counts["products_synced"],
        variants_synced=counts.get("variants_synced", 0),
        orders_synced=counts["orders_synced"],
        line_items_synced=counts.get("line_items_synced", 0),
        metrics_synced=counts["metrics_synced"],
        duration_seconds=counts.get("duration_seconds", 0.0),
        last_sync_at=store.last_sync_at,
    )


@router.get(
    "/{project_id}/shopify/dashboard",
    response_model=ShopifyDashboardResponse,
    response_model_by_alias=True,
)
async def shopify_dashboard(
    project_id: UUID,
    range: str | None = Query(None, alias="range"),
    start_date: date | None = Query(None, alias="start_date"),
    end_date: date | None = Query(None, alias="end_date"),
    session: AsyncSession = Depends(get_db),
) -> ShopifyDashboardResponse:
    await get_project_in_default_workspace(project_id, session)
    store = await get_shopify_store_for_project(project_id, session)

    if store is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shopify non connesso per questo progetto",
        )

    period, previous_period = resolve_period_pair(store, range, start_date, end_date)
    data = await build_dashboard(store, session, period=period, previous_period=previous_period)
    return ShopifyDashboardResponse.model_validate(data)


@router.get(
    "/{project_id}/shopify/reconciliation",
    response_model=ShopifyReconciliationDebugResponse,
    response_model_by_alias=True,
)
async def shopify_reconciliation(
    project_id: UUID,
    range: str | None = Query(None, alias="range"),
    start_date: date | None = Query(None, alias="start_date"),
    end_date: date | None = Query(None, alias="end_date"),
    session: AsyncSession = Depends(get_db),
) -> ShopifyReconciliationDebugResponse:
    await get_project_in_default_workspace(project_id, session)
    store = await get_shopify_store_for_project(project_id, session)

    if store is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shopify non connesso per questo progetto",
        )

    period, _previous_period = resolve_period_pair(store, range, start_date, end_date)
    data = await build_reconciliation_debug(session, store, period)
    return ShopifyReconciliationDebugResponse.model_validate(data)


@router.get(
    "/{project_id}/shopify/products",
    response_model=list[ShopifyProductRead],
    response_model_by_alias=True,
)
async def shopify_products(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> list[ShopifyProduct]:
    await get_project_in_default_workspace(project_id, session)
    store = await get_shopify_store_for_project(project_id, session)

    if store is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shopify non connesso per questo progetto",
        )

    result = await session.execute(
        select(ShopifyProduct)
        .where(ShopifyProduct.shopify_store_id == store.id)
        .order_by(ShopifyProduct.title.asc())
    )
    return list(result.scalars().all())


@router.get(
    "/{project_id}/shopify/orders",
    response_model=list[ShopifyOrderRead],
    response_model_by_alias=True,
)
async def shopify_orders(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> list[ShopifyOrder]:
    await get_project_in_default_workspace(project_id, session)
    store = await get_shopify_store_for_project(project_id, session)

    if store is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shopify non connesso per questo progetto",
        )

    result = await session.execute(
        select(ShopifyOrder)
        .where(ShopifyOrder.shopify_store_id == store.id)
        .order_by(ShopifyOrder.created_at_shopify.desc().nullslast())
    )
    return list(result.scalars().all())
