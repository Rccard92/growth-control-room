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
    SeoApplyFieldsRequest,
    SeoApplyFieldsResponse,
    SeoApplyResponse,
    SeoCollectionDetailResponse,
    SeoCollectionListResponse,
    SeoContentDebugResponse,
    SeoEntityAnalysisRead,
    SeoEntitySyncResponse,
    SeoOptimizerSyncResponse,
    SeoProductDetailResponse,
    SeoProductListResponse,
    SeoProposalGenerateFieldRequest,
    SeoProposalGenerateFieldResponse,
    SeoProposalGenerateRequest,
    SeoProposalListResponse,
    SeoProposalManualRequest,
    SeoProposalPreviewResponse,
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
    reject_proposal,
)
from app.services.content.seo_apply_fields_service import apply_entity_fields
from app.services.content.seo_entity_detail_service import (
    get_collection_seo_detail,
    get_product_seo_detail,
)
from app.services.content.seo_entity_sync_service import (
    sync_single_collection,
    sync_single_product,
)
from app.services.content.seo_optimizer_list import (
    analysis_to_read,
    get_analysis_detail,
    list_collection_seo_items,
    list_product_seo_items,
    list_proposals,
)
from app.services.content.seo_content_debug_service import build_content_seo_debug
from app.services.content.seo_proposal_manual_service import create_manual_proposal
from app.services.content.seo_skill_loader import skill_meta_for_detail_response
from app.services.content.seo_proposal_preview_service import build_proposal_preview
from app.services.content.seo_proposal_engine import generate_seo_proposal
from app.services.content.seo_proposal_field_engine import generate_seo_proposal_field
from app.services.content.seo_proposal_read import proposal_to_read_dict
from app.services.content.seo_proposal_diff import proposal_changed_fields
from app.services.projects import get_project_in_default_workspace
from app.services.shopify.client import ShopifyAPIError
from app.services.shopify.connect import get_shopify_client_for_store, get_shopify_store_for_project
from app.services.shopify.content_sync import sync_shopify_collections_only
from app.services.shopify.scopes import resolve_shopify_scopes
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
    warnings: list[str] = []
    message: str | None = None

    try:
        client = await get_shopify_client_for_store(store)
        product_result = await sync_shopify_store(store, client, session)
        products_synced = product_result["products_synced"]
        duration += product_result.get("duration_seconds", 0)

        collection_result = await sync_shopify_collections_only(store, client, session)
        collections_synced = collection_result.collections_synced
        duration += collection_result.duration_seconds
        warnings.extend(collection_result.warnings)
        if collection_result.errors and collections_synced == 0:
            message = collection_result.errors[0]
        elif collection_result.warnings:
            message = collection_result.warnings[0]
    except ShopifyAPIError as exc:
        raise _map_shopify_error(exc) from exc

    return SeoOptimizerSyncResponse(
        products_synced=products_synced,
        collections_synced=collections_synced,
        duration_seconds=round(duration, 2),
        warnings=warnings,
        message=message,
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
        message=result.message,
    )


@router.get(
    "/{project_id}/content/seo/debug",
    response_model=SeoContentDebugResponse,
    response_model_by_alias=True,
)
async def content_seo_debug(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> SeoContentDebugResponse:
    await get_project_in_default_workspace(project_id, session)
    store = _require_connected_store(await get_shopify_store_for_project(project_id, session))
    data = await build_content_seo_debug(store, session)
    return SeoContentDebugResponse.model_validate(data)


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
    scope_info = await resolve_shopify_scopes(store, session)
    return SeoProductListResponse(
        items=items,
        openai_configured=is_openai_configured(),
        write_products_available=scope_info["can_write_products"],
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
    scope_info = await resolve_shopify_scopes(store, session)
    return SeoCollectionListResponse(
        items=items,
        openai_configured=is_openai_configured(),
        write_products_available=scope_info["can_write_products"],
    )


def _proposal_from_dict(data: dict | None) -> SeoProposalRead | None:
    if not data:
        return None
    current = data.get("currentValues") or data.get("current_values")
    proposed = data.get("proposedValues") or data.get("proposed_values")
    changed = data.get("changedFields") or data.get("changed_fields")
    if changed is None:
        changed = proposal_changed_fields(current, proposed)
    return SeoProposalRead.model_validate(
        {
            "id": data["id"],
            "entity_type": data.get("entityType") or data.get("entity_type"),
            "entity_id": data.get("entityId") or data.get("entity_id"),
            "entity_gid": data.get("entityGid") or data.get("entity_gid"),
            "status": data["status"],
            "source": data["source"],
            "current_values": current,
            "proposed_values": proposed,
            "reasoning": data.get("reasoning"),
            "risk_level": data.get("riskLevel") or data.get("risk_level"),
            "approved_at": data.get("approvedAt") or data.get("approved_at"),
            "applied_at": data.get("appliedAt") or data.get("applied_at"),
            "created_at": data.get("createdAt") or data.get("created_at"),
            "changed_fields": changed,
        }
    )


def _proposal_read(proposal) -> SeoProposalRead:
    return SeoProposalRead.model_validate(proposal_to_read_dict(proposal))


def _build_product_detail(data: dict) -> SeoProductDetailResponse:
    history = data.get("proposal_history") or []
    return SeoProductDetailResponse(
        product=data["product"],
        analysis=data.get("analysis"),
        score_breakdown=data.get("score_breakdown"),
        skill_meta=skill_meta_for_detail_response("product"),
        current_values=data["current_values"],
        images=data.get("images") or [],
        metafields=data.get("metafields") or [],
        quantity_sold=data.get("quantity_sold", 0),
        revenue=data.get("revenue", 0),
        stock=data.get("stock"),
        latest_proposal=_proposal_from_dict(data.get("latest_proposal")),
        proposal_history=[_proposal_from_dict(p) for p in history if p],
        change_logs=data.get("change_logs") or [],
    )


def _build_collection_detail(data: dict) -> SeoCollectionDetailResponse:
    history = data.get("proposal_history") or []
    return SeoCollectionDetailResponse(
        collection=data["collection"],
        analysis=data.get("analysis"),
        score_breakdown=data.get("score_breakdown"),
        skill_meta=skill_meta_for_detail_response("collection"),
        current_values=data["current_values"],
        image=data.get("image"),
        latest_proposal=_proposal_from_dict(data.get("latest_proposal")),
        proposal_history=[_proposal_from_dict(p) for p in history if p],
        change_logs=data.get("change_logs") or [],
    )


@router.get(
    "/{project_id}/content/seo/products/{product_id}",
    response_model=SeoProductDetailResponse,
    response_model_by_alias=True,
)
async def get_product_seo_detail_route(
    project_id: UUID,
    product_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> SeoProductDetailResponse:
    await get_project_in_default_workspace(project_id, session)
    store = _require_connected_store(await get_shopify_store_for_project(project_id, session))
    data = await get_product_seo_detail(store, session, product_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Prodotto non trovato")
    return _build_product_detail(data)


@router.get(
    "/{project_id}/content/seo/collections/{collection_id}",
    response_model=SeoCollectionDetailResponse,
    response_model_by_alias=True,
)
async def get_collection_seo_detail_route(
    project_id: UUID,
    collection_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> SeoCollectionDetailResponse:
    await get_project_in_default_workspace(project_id, session)
    store = _require_connected_store(await get_shopify_store_for_project(project_id, session))
    data = await get_collection_seo_detail(store, session, collection_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Collection non trovata")
    return _build_collection_detail(data)


@router.post(
    "/{project_id}/content/seo/products/{product_id}/sync-shopify",
    response_model=SeoEntitySyncResponse,
    response_model_by_alias=True,
)
async def sync_product_seo_from_shopify(
    project_id: UUID,
    product_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> SeoEntitySyncResponse:
    await get_project_in_default_workspace(project_id, session)
    store = _require_connected_store(await get_shopify_store_for_project(project_id, session))
    try:
        client = await get_shopify_client_for_store(store)
        result = await sync_single_product(store, client, session, product_id)
    except ShopifyAPIError as exc:
        raise _map_shopify_error(exc) from exc

    detail = _build_product_detail(result["detail"])
    return SeoEntitySyncResponse(
        entity_type="product",
        entity_id=str(product_id),
        detail=detail.model_dump(by_alias=True),
        message=result["message"],
    )


@router.post(
    "/{project_id}/content/seo/collections/{collection_id}/sync-shopify",
    response_model=SeoEntitySyncResponse,
    response_model_by_alias=True,
)
async def sync_collection_seo_from_shopify(
    project_id: UUID,
    collection_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> SeoEntitySyncResponse:
    await get_project_in_default_workspace(project_id, session)
    store = _require_connected_store(await get_shopify_store_for_project(project_id, session))
    try:
        client = await get_shopify_client_for_store(store)
        result = await sync_single_collection(store, client, session, collection_id)
    except ShopifyAPIError as exc:
        raise _map_shopify_error(exc) from exc

    detail = _build_collection_detail(result["detail"])
    return SeoEntitySyncResponse(
        entity_type="collection",
        entity_id=str(collection_id),
        detail=detail.model_dump(by_alias=True),
        message=result["message"],
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
    return analysis_to_read(analysis)


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
    return analysis_to_read(analysis)


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
        items=[_proposal_read(p) for p in proposals]
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
            mode=body.mode,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return _proposal_read(proposal)


@router.post(
    "/{project_id}/content/seo/proposals/generate-field",
    response_model=SeoProposalGenerateFieldResponse,
    response_model_by_alias=True,
)
async def generate_proposal_field(
    project_id: UUID,
    body: SeoProposalGenerateFieldRequest,
    session: AsyncSession = Depends(get_db),
) -> SeoProposalGenerateFieldResponse:
    await get_project_in_default_workspace(project_id, session)
    store = _require_connected_store(await get_shopify_store_for_project(project_id, session))

    if body.use_ai and not is_openai_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI non configurata. Aggiungi OPENAI_API_KEY per generare proposte automatiche.",
        )

    try:
        result = await generate_seo_proposal_field(
            store,
            session,
            entity_type=body.entity_type,
            entity_id=body.entity_id,
            field=body.field,
            image_id=body.image_id,
            metafield_id=body.metafield_id,
            use_ai=body.use_ai,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return SeoProposalGenerateFieldResponse.model_validate(result)


@router.post(
    "/{project_id}/content/seo/proposals/manual",
    response_model=SeoProposalRead,
    response_model_by_alias=True,
)
async def create_manual_seo_proposal(
    project_id: UUID,
    body: SeoProposalManualRequest,
    session: AsyncSession = Depends(get_db),
) -> SeoProposalRead:
    await get_project_in_default_workspace(project_id, session)
    store = _require_connected_store(await get_shopify_store_for_project(project_id, session))
    try:
        proposal = await create_manual_proposal(
            store,
            session,
            entity_type=body.entity_type,
            entity_id=body.entity_id,
            proposed_values=body.proposed_values,
            changed_fields=body.changed_fields,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _proposal_read(proposal)


@router.post(
    "/{project_id}/content/seo/proposals/{proposal_id}/preview",
    response_model=SeoProposalPreviewResponse,
    response_model_by_alias=True,
)
async def preview_seo_proposal(
    project_id: UUID,
    proposal_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> SeoProposalPreviewResponse:
    await get_project_in_default_workspace(project_id, session)
    store = _require_connected_store(await get_shopify_store_for_project(project_id, session))
    proposal = await get_proposal_for_store(store, session, proposal_id)
    if proposal is None:
        raise HTTPException(status_code=404, detail="Proposta non trovata")
    preview = build_proposal_preview(proposal)
    return SeoProposalPreviewResponse.model_validate(preview)


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
    return _proposal_read(proposal)


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
    return _proposal_read(proposal)


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
    return _proposal_read(proposal)


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

    try:
        client = await get_shopify_client_for_store(store)
        result = await apply_proposal(store, client, proposal, session)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return SeoApplyResponse.model_validate(result)


@router.post(
    "/{project_id}/content/seo/entities/apply-fields",
    response_model=SeoApplyFieldsResponse,
    response_model_by_alias=True,
)
async def apply_seo_entity_fields(
    project_id: UUID,
    body: SeoApplyFieldsRequest,
    session: AsyncSession = Depends(get_db),
) -> SeoApplyFieldsResponse:
    await get_project_in_default_workspace(project_id, session)
    store = _require_connected_store(await get_shopify_store_for_project(project_id, session))

    try:
        client = await get_shopify_client_for_store(store)
        result = await apply_entity_fields(
            store,
            client,
            session,
            entity_type=body.entity_type,
            entity_id=body.entity_id,
            fields=body.fields,
            changed_fields=body.changed_fields,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return SeoApplyFieldsResponse.model_validate(result)
