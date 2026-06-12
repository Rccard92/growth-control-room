from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.content_seo import (
    ContentSeoAnalyzeResponse,
    ContentSeoDashboardResponse,
    ContentSeoSyncResponse,
)
from app.schemas.seo_optimizer import (
    SeoAnalyzeCountResponse,
    SeoApplyResponse,
    SeoCollectionListResponse,
    SeoEntityAnalysisRead,
    SeoOptimizerSyncResponse,
    SeoProductListResponse,
    SeoProposalGenerateRequest,
    SeoProposalListResponse,
    SeoProposalRead,
)
from app.services.ai.openai_client import is_openai_configured
from app.services.content.analyze import run_content_seo_analyze
from app.services.content.collection_seo_analyzer import analyze_collections_for_store
from app.services.content.dashboard import build_content_seo_dashboard
from app.services.content.product_seo_analyzer import analyze_products_for_store
from app.services.content.seo_apply_service import (
    apply_proposal,
    approve_proposal,
    get_proposal_for_store,
    has_write_products_scope,
    reject_proposal,
)
from app.services.content.seo_optimizer_list import (
    get_analysis_detail,
    list_collection_seo_items,
    list_product_seo_items,
    list_proposals,
)
from app.services.content.seo_proposal_engine import generate_seo_proposal
from app.services.projects import get_project_in_default_workspace
from app.services.shopify.client import ShopifyAPIError
from app.services.shopify.connect import get_shopify_client_for_store, get_shopify_store_for_project
from app.services.shopify.content_sync import sync_shopify_collections_only
from app.services.shopify.sync import sync_shopify_store

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


@router.post(
    "/{project_id}/content/seo/sync-shopify",
    response_model=SeoOptimizerSyncResponse,
    response_model_by_alias=True,
)
async def content_seo_sync_shopify(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> SeoOptimizerSyncResponse:
    await get_project_in_default_workspace(project_id, session)
    store = _require_connected_store(await get_shopify_store_for_project(project_id, session))

    products_synced = 0
    collections_synced = 0
    duration = 0.0

    try:
        client = await get_shopify_client_for_store(store)
        product_result = await sync_shopify_store(store, client, session)
        products_synced = product_result["products_synced"]
        duration += product_result.get("duration_seconds", 0)

        collection_result = await sync_shopify_collections_only(store, client, session)
        collections_synced = collection_result.collections_synced
        duration += collection_result.duration_seconds
    except ShopifyAPIError as exc:
        raise _map_shopify_error(exc) from exc

    return SeoOptimizerSyncResponse(
        products_synced=products_synced,
        collections_synced=collections_synced,
        duration_seconds=round(duration, 2),
    )


@router.post(
    "/{project_id}/content/seo/analyze",
    response_model=ContentSeoAnalyzeResponse,
    response_model_by_alias=True,
    deprecated=True,
)
async def content_seo_analyze_legacy(
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


@router.post(
    "/{project_id}/content/seo/products/analyze",
    response_model=SeoAnalyzeCountResponse,
    response_model_by_alias=True,
)
async def analyze_products(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> SeoAnalyzeCountResponse:
    await get_project_in_default_workspace(project_id, session)
    store = _require_connected_store(await get_shopify_store_for_project(project_id, session))
    result = await analyze_products_for_store(store, session)
    return SeoAnalyzeCountResponse(
        products_analyzed=result.products_analyzed,
        critical=result.critical,
        warnings=result.warnings,
        opportunities=result.opportunities,
    )


@router.post(
    "/{project_id}/content/seo/collections/analyze",
    response_model=SeoAnalyzeCountResponse,
    response_model_by_alias=True,
)
async def analyze_collections(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> SeoAnalyzeCountResponse:
    await get_project_in_default_workspace(project_id, session)
    store = _require_connected_store(await get_shopify_store_for_project(project_id, session))
    result = await analyze_collections_for_store(store, session)
    return SeoAnalyzeCountResponse(
        collections_analyzed=result.collections_analyzed,
        critical=result.critical,
        warnings=result.warnings,
        opportunities=result.opportunities,
    )


@router.get(
    "/{project_id}/content/seo/products",
    response_model=SeoProductListResponse,
    response_model_by_alias=True,
)
async def list_products_seo(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> SeoProductListResponse:
    await get_project_in_default_workspace(project_id, session)
    store = _require_connected_store(await get_shopify_store_for_project(project_id, session))
    items = await list_product_seo_items(store, session)
    return SeoProductListResponse(
        items=items,
        openai_configured=is_openai_configured(),
        write_products_available=has_write_products_scope(),
    )


@router.get(
    "/{project_id}/content/seo/collections",
    response_model=SeoCollectionListResponse,
    response_model_by_alias=True,
)
async def list_collections_seo(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> SeoCollectionListResponse:
    await get_project_in_default_workspace(project_id, session)
    store = _require_connected_store(await get_shopify_store_for_project(project_id, session))
    items = await list_collection_seo_items(store, session)
    return SeoCollectionListResponse(
        items=items,
        openai_configured=is_openai_configured(),
        write_products_available=has_write_products_scope(),
    )


@router.get(
    "/{project_id}/content/seo/products/{entity_id}/analysis",
    response_model=SeoEntityAnalysisRead,
    response_model_by_alias=True,
)
async def get_product_analysis(
    project_id: UUID,
    entity_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> SeoEntityAnalysisRead:
    await get_project_in_default_workspace(project_id, session)
    store = _require_connected_store(await get_shopify_store_for_project(project_id, session))
    analysis = await get_analysis_detail(store, session, "product", entity_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analisi non trovata")
    return SeoEntityAnalysisRead.model_validate(analysis)


@router.get(
    "/{project_id}/content/seo/collections/{entity_id}/analysis",
    response_model=SeoEntityAnalysisRead,
    response_model_by_alias=True,
)
async def get_collection_analysis(
    project_id: UUID,
    entity_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> SeoEntityAnalysisRead:
    await get_project_in_default_workspace(project_id, session)
    store = _require_connected_store(await get_shopify_store_for_project(project_id, session))
    analysis = await get_analysis_detail(store, session, "collection", entity_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analisi non trovata")
    return SeoEntityAnalysisRead.model_validate(analysis)


@router.get(
    "/{project_id}/content/seo/proposals",
    response_model=SeoProposalListResponse,
    response_model_by_alias=True,
)
async def list_seo_proposals(
    project_id: UUID,
    status_filter: str | None = Query(default=None, alias="status"),
    session: AsyncSession = Depends(get_db),
) -> SeoProposalListResponse:
    await get_project_in_default_workspace(project_id, session)
    store = _require_connected_store(await get_shopify_store_for_project(project_id, session))
    proposals = await list_proposals(store, session, status=status_filter)
    return SeoProposalListResponse(
        items=[SeoProposalRead.model_validate(p) for p in proposals]
    )


@router.post(
    "/{project_id}/content/seo/proposals/generate",
    response_model=SeoProposalRead,
    response_model_by_alias=True,
)
async def generate_proposal(
    project_id: UUID,
    body: SeoProposalGenerateRequest,
    session: AsyncSession = Depends(get_db),
) -> SeoProposalRead:
    await get_project_in_default_workspace(project_id, session)
    store = _require_connected_store(await get_shopify_store_for_project(project_id, session))

    if body.use_ai and not is_openai_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI non configurata. Aggiungi OPENAI_API_KEY per generare proposte automatiche.",
        )

    try:
        proposal = await generate_seo_proposal(
            store,
            session,
            entity_type=body.entity_type,
            entity_id=body.entity_id,
            use_ai=body.use_ai,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return SeoProposalRead.model_validate(proposal)


@router.get(
    "/{project_id}/content/seo/proposals/{proposal_id}",
    response_model=SeoProposalRead,
    response_model_by_alias=True,
)
async def get_proposal(
    project_id: UUID,
    proposal_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> SeoProposalRead:
    await get_project_in_default_workspace(project_id, session)
    store = _require_connected_store(await get_shopify_store_for_project(project_id, session))
    proposal = await get_proposal_for_store(store, session, proposal_id)
    if proposal is None:
        raise HTTPException(status_code=404, detail="Proposta non trovata")
    return SeoProposalRead.model_validate(proposal)


@router.post(
    "/{project_id}/content/seo/proposals/{proposal_id}/approve",
    response_model=SeoProposalRead,
    response_model_by_alias=True,
)
async def approve_seo_proposal(
    project_id: UUID,
    proposal_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> SeoProposalRead:
    await get_project_in_default_workspace(project_id, session)
    store = _require_connected_store(await get_shopify_store_for_project(project_id, session))
    proposal = await get_proposal_for_store(store, session, proposal_id)
    if proposal is None:
        raise HTTPException(status_code=404, detail="Proposta non trovata")
    try:
        proposal = await approve_proposal(proposal, session)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return SeoProposalRead.model_validate(proposal)


@router.post(
    "/{project_id}/content/seo/proposals/{proposal_id}/reject",
    response_model=SeoProposalRead,
    response_model_by_alias=True,
)
async def reject_seo_proposal(
    project_id: UUID,
    proposal_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> SeoProposalRead:
    await get_project_in_default_workspace(project_id, session)
    store = _require_connected_store(await get_shopify_store_for_project(project_id, session))
    proposal = await get_proposal_for_store(store, session, proposal_id)
    if proposal is None:
        raise HTTPException(status_code=404, detail="Proposta non trovata")
    try:
        proposal = await reject_proposal(proposal, session)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return SeoProposalRead.model_validate(proposal)


@router.post(
    "/{project_id}/content/seo/proposals/{proposal_id}/apply",
    response_model=SeoApplyResponse,
    response_model_by_alias=True,
)
async def apply_seo_proposal(
    project_id: UUID,
    proposal_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> SeoApplyResponse:
    await get_project_in_default_workspace(project_id, session)
    store = _require_connected_store(await get_shopify_store_for_project(project_id, session))
    proposal = await get_proposal_for_store(store, session, proposal_id)
    if proposal is None:
        raise HTTPException(status_code=404, detail="Proposta non trovata")

    if not has_write_products_scope():
        from app.services.content.seo_apply_service import write_products_required_response

        return SeoApplyResponse.model_validate(write_products_required_response())

    try:
        client = await get_shopify_client_for_store(store)
        result = await apply_proposal(store, client, proposal, session)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return SeoApplyResponse.model_validate(result)
