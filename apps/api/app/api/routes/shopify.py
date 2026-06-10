from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.shopify import ShopifyOrder, ShopifyProduct
from app.schemas.shopify import (
    ShopifyConnectRequest,
    ShopifyConnectResponse,
    ShopifyDashboardResponse,
    ShopifyOrderRead,
    ShopifyOrderSummary,
    ShopifyProductRead,
    ShopifyProductSummary,
    ShopifyStatusResponse,
    ShopifySyncResponse,
    ShopifyTopProduct,
)
from app.services.projects import get_project_in_default_workspace
from app.services.shopify.client import ShopifyAPIError
from app.services.shopify.connect import connect_shopify, get_shopify_client_for_store, get_shopify_store_for_project
from app.services.shopify.dashboard import build_dashboard
from app.services.shopify.sync import sync_shopify_store

router = APIRouter(prefix="/projects", tags=["shopify"])


def _map_shopify_error(exc: ShopifyAPIError) -> HTTPException:
    code = exc.status_code or status.HTTP_400_BAD_REQUEST
    if code == 401:
        code = status.HTTP_401_UNAUTHORIZED
    elif code == 403:
        code = status.HTTP_403_FORBIDDEN
    return HTTPException(status_code=code, detail=exc.message)


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
        orders_synced=counts["orders_synced"],
        metrics_synced=counts["metrics_synced"],
        last_sync_at=store.last_sync_at,
    )


@router.get(
    "/{project_id}/shopify/dashboard",
    response_model=ShopifyDashboardResponse,
    response_model_by_alias=True,
)
async def shopify_dashboard(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> ShopifyDashboardResponse:
    await get_project_in_default_workspace(project_id, session)
    store = await get_shopify_store_for_project(project_id, session)

    if store is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shopify non connesso per questo progetto",
        )

    data = await build_dashboard(store, session)
    return ShopifyDashboardResponse(
        revenue=data["revenue"],
        orders_count=data["orders_count"],
        average_order_value=data["average_order_value"],
        products_count=data["products_count"],
        low_stock_products=[
            ShopifyProductSummary.model_validate(p) for p in data["low_stock_products"]
        ],
        top_products=[ShopifyTopProduct(**item) for item in data["top_products"]],
        recent_orders=[
            ShopifyOrderSummary.model_validate(o) for o in data["recent_orders"]
        ],
        last_sync_at=data["last_sync_at"],
    )


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
