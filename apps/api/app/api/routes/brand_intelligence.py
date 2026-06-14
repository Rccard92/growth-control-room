from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.brand_brief import (
    BrandIntelligenceBriefListItem,
    BrandIntelligenceBriefRead,
    BrandIntelligenceBriefUpdate,
    GenerateBriefResponse,
)
from app.schemas.brand_identity_visual import (
    BrandIdentityApplyProposalRequest,
    BrandIdentityApplyProposalResponse,
    BrandIdentityImportResponse,
    BrandIdentityRead,
    BrandIdentityUpdate,
    BrandVisualIdentityRead,
    BrandVisualIdentityUpdate,
    VisualApplyProposalRequest,
    VisualApplyProposalResponse,
    VisualExtractRequest,
    VisualExtractResponse,
)
from app.schemas.brand_product_knowledge import (
    BrandProductKnowledgeGeneralApplyProposalRequest,
    BrandProductKnowledgeGeneralApplyProposalResponse,
    BrandProductKnowledgeGeneralImportResponse,
    BrandProductKnowledgeGeneralRead,
    BrandProductKnowledgeGeneralUpdate,
    BrandProductKnowledgeItemFromShopifyRequest,
    BrandProductKnowledgeItemRead,
    BrandProductKnowledgeItemUpdate,
    BrandProductKnowledgeItemsApplyImportRequest,
    BrandProductKnowledgeItemsApplyImportResponse,
    BrandProductKnowledgeItemsImportResponse,
    BrandProductKnowledgeShopifyProductOption,
    BrandProductKnowledgeShopifyProductsResponse,
)
from app.schemas.brand_safe_claims import (
    BrandSafeClaimsApplyProposalRequest,
    BrandSafeClaimsApplyProposalResponse,
    BrandSafeClaimsImportResponse,
    BrandSafeClaimsRead,
    BrandSafeClaimsUpdate,
)
from app.schemas.brand_faq_objections import (
    BrandFaqObjectionsApplyProposalRequest,
    BrandFaqObjectionsApplyProposalResponse,
    BrandFaqObjectionsImportResponse,
    BrandFaqObjectionsRead,
    BrandFaqObjectionsUpdate,
)
from app.schemas.brand_profile_v1 import (
    BrandProfileApplyProposalRequest,
    BrandProfileEnrichRequest,
    BrandProfileEnrichResponse,
)
from app.schemas.brand_intelligence import (
    BrandAiGuardrailCreate,
    BrandAiGuardrailRead,
    BrandAiGuardrailUpdate,
    BrandApplyFactsRequest,
    BrandApplyFactsResponse,
    BrandAssetCreate,
    BrandAssetRead,
    BrandAssetUpdate,
    BrandAudienceInsightCreate,
    BrandAudienceInsightRead,
    BrandAudienceInsightUpdate,
    BrandClaimRuleCreate,
    BrandClaimRuleRead,
    BrandClaimRuleUpdate,
    BrandContentPillarCreate,
    BrandContentPillarRead,
    BrandContentPillarUpdate,
    BrandContextBundleResponse,
    BrandExtractBatchRequest,
    BrandExtractedFactRead,
    BrandExtractedFactUpdate,
    BrandExternalSourceRead,
    BrandExternalSourcesAddRequest,
    BrandExternalSourcesFetchResponse,
    BrandImportBatchCreateRequest,
    BrandImportBatchCreateResponse,
    BrandImportBatchListItem,
    BrandImportBatchRefreshContextRequest,
    BrandImportBatchRefreshContextResponse,
    BrandImportBatchSourcesUpdateRequest,
    BrandImportBatchSourcesUpdateResponse,
    BrandImportBatchStartResponse,
    BrandImportBatchStatusResponse,
    BrandIntelligenceOverviewResponse,
    BrandKnowledgeScoreResponse,
    BrandProductKnowledgeCreate,
    BrandProductKnowledgeRead,
    BrandProductKnowledgeUpdate,
    BrandProfileRead,
    BrandProfileUpdate,
    BrandSectionDraftApplyBatchRequest,
    BrandSectionDraftApplyResponse,
    BrandSectionDraftListItem,
    BrandSectionDraftRead,
    BrandSectionDraftRegenerateRequest,
    BrandSectionDraftSynthesizeResponse,
    BrandSectionDraftUpdate,
    BrandSeoStrategyRead,
    BrandSeoStrategyUpdate,
    BrandSourceDocumentRead,
    BrandSourceDocumentsUploadResponse,
    BrandVoiceRead,
    BrandVoiceUpdate,
)
from app.services.brand_intelligence import service as bi_service
from app.services.brand_intelligence import sources_service
from app.services.brand_intelligence.brief_service import (
    approve_brief,
    archive_brief,
    build_brand_intelligence_brief_read,
    get_brief,
    list_briefs,
    patch_brief,
)
from app.services.brand_intelligence.brief_synthesis import generate_brief_from_batch
from app.services.brand_intelligence.batch_processor import schedule_batch_processing
from app.services.brand_intelligence.batch_service import (
    create_import_batch_with_sources,
    get_batch_status,
    list_batches,
    mark_batch_started,
)
from app.services.brand_intelligence.external_sources_service import (
    add_external_sources_to_batch,
    fetch_batch_external_sources,
    list_external_sources_for_batch,
    parse_sources_json,
    upsert_batch_sources,
)
from app.services.brand_intelligence.refresh_context_service import schedule_refresh_context
from app.services.brand_intelligence.document_extraction import run_ai_extraction
from app.services.brand_intelligence.draft_apply import (
    apply_section_draft,
    apply_section_drafts_batch,
)
from app.services.brand_intelligence.section_drafts_service import (
    get_section_draft,
    list_section_drafts,
    patch_section_draft,
    regenerate_section_draft,
)
from app.services.brand_intelligence.identity_import import import_identity_from_file
from app.services.brand_intelligence.identity_service import (
    apply_identity_proposal,
    get_identity,
    upsert_identity,
)
from app.services.brand_intelligence.profile_enrichment import (
    apply_brand_profile_proposal,
    enrich_brand_profile,
)
from app.services.brand_intelligence.product_knowledge_general_import import import_general_from_file
from app.services.brand_intelligence.product_knowledge_general_service import (
    apply_general_proposal,
    get_general,
    upsert_general,
)
from app.services.brand_intelligence.product_knowledge_items_import import import_items_from_file
from app.services.brand_intelligence.product_knowledge_item_service import (
    apply_items_import_proposal,
    create_item_from_shopify,
    delete_item,
    get_item,
    item_completion,
    list_items,
    list_shopify_products_for_picker,
    update_item,
)
from app.services.brand_intelligence.safe_claims_import import import_safe_claims_from_file
from app.services.brand_intelligence.safe_claims_service import (
    apply_safe_claims_proposal,
    get_safe_claims,
    upsert_safe_claims,
)
from app.services.brand_intelligence.faq_objections_import import import_faq_objections_from_file
from app.services.brand_intelligence.faq_objections_service import (
    apply_faq_objections_proposal,
    get_faq_objections,
    upsert_faq_objections,
)
from app.services.brand_intelligence.visual_extraction import extract_visual_from_website
from app.services.brand_intelligence.visual_identity_service import (
    apply_visual_proposal,
    get_visual_identity,
    upsert_visual_identity,
)
from app.services.brand_intelligence.synthesis import synthesize_batch
from app.services.projects import get_project_in_default_workspace

router = APIRouter(prefix="/projects", tags=["brand-intelligence"])


@router.get(
    "/{project_id}/brand-intelligence",
    response_model=BrandIntelligenceOverviewResponse,
    response_model_by_alias=True,
)
async def get_brand_intelligence_overview(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> BrandIntelligenceOverviewResponse:
    await get_project_in_default_workspace(project_id, session)
    return await bi_service.build_overview(session, project_id)


@router.get(
    "/{project_id}/brand-intelligence/score",
    response_model=BrandKnowledgeScoreResponse,
    response_model_by_alias=True,
)
async def get_brand_knowledge_score(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> BrandKnowledgeScoreResponse:
    await get_project_in_default_workspace(project_id, session)
    return await bi_service.get_knowledge_score(session, project_id)


@router.get(
    "/{project_id}/brand-intelligence/context",
    response_model=BrandContextBundleResponse,
    response_model_by_alias=True,
)
async def get_brand_context(
    project_id: UUID,
    format: str | None = Query(
        default=None,
        description="format=prompt restituisce lo stesso bundle con promptContext.previewText",
    ),
    session: AsyncSession = Depends(get_db),
) -> BrandContextBundleResponse:
    """Contesto brand machine-ready. Con format=prompt, stessa response (preview in promptContext)."""
    await get_project_in_default_workspace(project_id, session)
    del format
    return await bi_service.get_context_bundle(session, project_id)


@router.get(
    "/{project_id}/brand-intelligence/profile",
    response_model=BrandProfileRead,
    response_model_by_alias=True,
)
async def get_brand_profile(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> BrandProfileRead:
    await get_project_in_default_workspace(project_id, session)
    row = await bi_service.get_profile(session, project_id)
    return BrandProfileRead.model_validate(row)


@router.put(
    "/{project_id}/brand-intelligence/profile",
    response_model=BrandProfileRead,
    response_model_by_alias=True,
)
async def update_brand_profile(
    project_id: UUID,
    payload: BrandProfileUpdate,
    session: AsyncSession = Depends(get_db),
) -> BrandProfileRead:
    await get_project_in_default_workspace(project_id, session)
    row = await bi_service.upsert_profile(session, project_id, payload)
    return BrandProfileRead.model_validate(row)


@router.post(
    "/{project_id}/brand-intelligence/profile/enrich",
    response_model=BrandProfileEnrichResponse,
    response_model_by_alias=True,
)
async def enrich_profile(
    project_id: UUID,
    payload: BrandProfileEnrichRequest,
    session: AsyncSession = Depends(get_db),
) -> BrandProfileEnrichResponse:
    await get_project_in_default_workspace(project_id, session)
    return await enrich_brand_profile(session, project_id, payload)


@router.post(
    "/{project_id}/brand-intelligence/profile/apply-proposal",
    response_model=BrandProfileRead,
    response_model_by_alias=True,
)
async def apply_profile_proposal(
    project_id: UUID,
    payload: BrandProfileApplyProposalRequest,
    session: AsyncSession = Depends(get_db),
) -> BrandProfileRead:
    await get_project_in_default_workspace(project_id, session)
    row = await apply_brand_profile_proposal(session, project_id, payload)
    return BrandProfileRead.model_validate(row)


@router.get(
    "/{project_id}/brand-intelligence/identity",
    response_model=BrandIdentityRead,
    response_model_by_alias=True,
)
async def get_brand_identity(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> BrandIdentityRead:
    await get_project_in_default_workspace(project_id, session)
    row = await get_identity(session, project_id)
    return BrandIdentityRead.model_validate(row)


@router.put(
    "/{project_id}/brand-intelligence/identity",
    response_model=BrandIdentityRead,
    response_model_by_alias=True,
)
async def update_brand_identity(
    project_id: UUID,
    payload: BrandIdentityUpdate,
    session: AsyncSession = Depends(get_db),
) -> BrandIdentityRead:
    await get_project_in_default_workspace(project_id, session)
    row = await upsert_identity(session, project_id, payload)
    return BrandIdentityRead.model_validate(row)


@router.post(
    "/{project_id}/brand-intelligence/identity/import-file",
    response_model=BrandIdentityImportResponse,
    response_model_by_alias=True,
)
async def import_brand_identity_file(
    project_id: UUID,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db),
) -> BrandIdentityImportResponse:
    await get_project_in_default_workspace(project_id, session)
    data = await file.read()
    return await import_identity_from_file(
        session,
        project_id,
        filename=file.filename or "document",
        content_type=file.content_type,
        data=data,
    )


@router.post(
    "/{project_id}/brand-intelligence/identity/apply-proposal",
    response_model=BrandIdentityApplyProposalResponse,
    response_model_by_alias=True,
)
async def apply_brand_identity_proposal(
    project_id: UUID,
    payload: BrandIdentityApplyProposalRequest,
    session: AsyncSession = Depends(get_db),
) -> BrandIdentityApplyProposalResponse:
    await get_project_in_default_workspace(project_id, session)
    row = await apply_identity_proposal(session, project_id, payload.proposal)
    return BrandIdentityApplyProposalResponse(
        brand_identity=BrandIdentityRead.model_validate(row),
        message="Brand Identity aggiornata.",
    )


@router.get(
    "/{project_id}/brand-intelligence/visual-identity",
    response_model=BrandVisualIdentityRead,
    response_model_by_alias=True,
)
async def get_brand_visual_identity(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> BrandVisualIdentityRead:
    await get_project_in_default_workspace(project_id, session)
    row = await get_visual_identity(session, project_id)
    return BrandVisualIdentityRead.model_validate(row)


@router.put(
    "/{project_id}/brand-intelligence/visual-identity",
    response_model=BrandVisualIdentityRead,
    response_model_by_alias=True,
)
async def update_brand_visual_identity(
    project_id: UUID,
    payload: BrandVisualIdentityUpdate,
    session: AsyncSession = Depends(get_db),
) -> BrandVisualIdentityRead:
    await get_project_in_default_workspace(project_id, session)
    row = await upsert_visual_identity(session, project_id, payload)
    return BrandVisualIdentityRead.model_validate(row)


@router.post(
    "/{project_id}/brand-intelligence/visual-identity/extract-from-website",
    response_model=VisualExtractResponse,
    response_model_by_alias=True,
)
async def extract_visual_identity_from_website(
    project_id: UUID,
    payload: VisualExtractRequest,
    session: AsyncSession = Depends(get_db),
) -> VisualExtractResponse:
    await get_project_in_default_workspace(project_id, session)
    return await extract_visual_from_website(payload.website_url)


@router.post(
    "/{project_id}/brand-intelligence/visual-identity/apply-proposal",
    response_model=VisualApplyProposalResponse,
    response_model_by_alias=True,
)
async def apply_visual_identity_proposal(
    project_id: UUID,
    payload: VisualApplyProposalRequest,
    session: AsyncSession = Depends(get_db),
) -> VisualApplyProposalResponse:
    await get_project_in_default_workspace(project_id, session)
    row = await apply_visual_proposal(session, project_id, payload.proposal)
    return VisualApplyProposalResponse(
        visual_identity=BrandVisualIdentityRead.model_validate(row),
        message="Visual Identity aggiornata.",
    )


@router.get(
    "/{project_id}/brand-intelligence/safe-claims",
    response_model=BrandSafeClaimsRead,
    response_model_by_alias=True,
)
async def get_brand_safe_claims(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> BrandSafeClaimsRead:
    await get_project_in_default_workspace(project_id, session)
    row = await get_safe_claims(session, project_id)
    return BrandSafeClaimsRead.model_validate(row)


@router.put(
    "/{project_id}/brand-intelligence/safe-claims",
    response_model=BrandSafeClaimsRead,
    response_model_by_alias=True,
)
async def update_brand_safe_claims(
    project_id: UUID,
    payload: BrandSafeClaimsUpdate,
    session: AsyncSession = Depends(get_db),
) -> BrandSafeClaimsRead:
    await get_project_in_default_workspace(project_id, session)
    row = await upsert_safe_claims(session, project_id, payload)
    return BrandSafeClaimsRead.model_validate(row)


@router.post(
    "/{project_id}/brand-intelligence/safe-claims/import-file",
    response_model=BrandSafeClaimsImportResponse,
    response_model_by_alias=True,
)
async def import_brand_safe_claims_file(
    project_id: UUID,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db),
) -> BrandSafeClaimsImportResponse:
    await get_project_in_default_workspace(project_id, session)
    data = await file.read()
    return await import_safe_claims_from_file(
        session,
        project_id,
        filename=file.filename or "document",
        content_type=file.content_type,
        data=data,
    )


@router.post(
    "/{project_id}/brand-intelligence/safe-claims/apply-proposal",
    response_model=BrandSafeClaimsApplyProposalResponse,
    response_model_by_alias=True,
)
async def apply_brand_safe_claims_proposal(
    project_id: UUID,
    payload: BrandSafeClaimsApplyProposalRequest,
    session: AsyncSession = Depends(get_db),
) -> BrandSafeClaimsApplyProposalResponse:
    await get_project_in_default_workspace(project_id, session)
    row = await apply_safe_claims_proposal(session, project_id, payload.proposal)
    return BrandSafeClaimsApplyProposalResponse(
        safe_claims=BrandSafeClaimsRead.model_validate(row),
        message="Safe Claims aggiornati.",
    )


@router.get(
    "/{project_id}/brand-intelligence/faq-objections",
    response_model=BrandFaqObjectionsRead,
    response_model_by_alias=True,
)
async def get_brand_faq_objections(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> BrandFaqObjectionsRead:
    await get_project_in_default_workspace(project_id, session)
    row = await get_faq_objections(session, project_id)
    return BrandFaqObjectionsRead.model_validate(row)


@router.put(
    "/{project_id}/brand-intelligence/faq-objections",
    response_model=BrandFaqObjectionsRead,
    response_model_by_alias=True,
)
async def update_brand_faq_objections(
    project_id: UUID,
    payload: BrandFaqObjectionsUpdate,
    session: AsyncSession = Depends(get_db),
) -> BrandFaqObjectionsRead:
    await get_project_in_default_workspace(project_id, session)
    row = await upsert_faq_objections(session, project_id, payload)
    return BrandFaqObjectionsRead.model_validate(row)


@router.post(
    "/{project_id}/brand-intelligence/faq-objections/import-file",
    response_model=BrandFaqObjectionsImportResponse,
    response_model_by_alias=True,
)
async def import_brand_faq_objections_file(
    project_id: UUID,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db),
) -> BrandFaqObjectionsImportResponse:
    await get_project_in_default_workspace(project_id, session)
    data = await file.read()
    return await import_faq_objections_from_file(
        session,
        project_id,
        filename=file.filename or "document",
        content_type=file.content_type,
        data=data,
    )


@router.post(
    "/{project_id}/brand-intelligence/faq-objections/apply-proposal",
    response_model=BrandFaqObjectionsApplyProposalResponse,
    response_model_by_alias=True,
)
async def apply_brand_faq_objections_proposal(
    project_id: UUID,
    payload: BrandFaqObjectionsApplyProposalRequest,
    session: AsyncSession = Depends(get_db),
) -> BrandFaqObjectionsApplyProposalResponse:
    await get_project_in_default_workspace(project_id, session)
    row = await apply_faq_objections_proposal(session, project_id, payload.proposal)
    return BrandFaqObjectionsApplyProposalResponse(
        faq_objections=BrandFaqObjectionsRead.model_validate(row),
        message="FAQ & Objections aggiornati.",
    )


@router.get(
    "/{project_id}/brand-intelligence/product-knowledge/general",
    response_model=BrandProductKnowledgeGeneralRead,
    response_model_by_alias=True,
)
async def get_product_knowledge_general(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> BrandProductKnowledgeGeneralRead:
    await get_project_in_default_workspace(project_id, session)
    row = await get_general(session, project_id)
    return BrandProductKnowledgeGeneralRead.model_validate(row)


@router.put(
    "/{project_id}/brand-intelligence/product-knowledge/general",
    response_model=BrandProductKnowledgeGeneralRead,
    response_model_by_alias=True,
)
async def update_product_knowledge_general(
    project_id: UUID,
    payload: BrandProductKnowledgeGeneralUpdate,
    session: AsyncSession = Depends(get_db),
) -> BrandProductKnowledgeGeneralRead:
    await get_project_in_default_workspace(project_id, session)
    row = await upsert_general(session, project_id, payload)
    return BrandProductKnowledgeGeneralRead.model_validate(row)


@router.post(
    "/{project_id}/brand-intelligence/product-knowledge/general/import-file",
    response_model=BrandProductKnowledgeGeneralImportResponse,
    response_model_by_alias=True,
)
async def import_product_knowledge_general_file(
    project_id: UUID,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db),
) -> BrandProductKnowledgeGeneralImportResponse:
    await get_project_in_default_workspace(project_id, session)
    data = await file.read()
    return await import_general_from_file(
        session,
        project_id,
        filename=file.filename or "document",
        content_type=file.content_type,
        data=data,
    )


@router.post(
    "/{project_id}/brand-intelligence/product-knowledge/general/apply-proposal",
    response_model=BrandProductKnowledgeGeneralApplyProposalResponse,
    response_model_by_alias=True,
)
async def apply_product_knowledge_general_proposal(
    project_id: UUID,
    payload: BrandProductKnowledgeGeneralApplyProposalRequest,
    session: AsyncSession = Depends(get_db),
) -> BrandProductKnowledgeGeneralApplyProposalResponse:
    await get_project_in_default_workspace(project_id, session)
    row = await apply_general_proposal(session, project_id, payload.proposal)
    return BrandProductKnowledgeGeneralApplyProposalResponse(
        general=BrandProductKnowledgeGeneralRead.model_validate(row),
        message="Product Knowledge generale aggiornata.",
    )


@router.get(
    "/{project_id}/brand-intelligence/product-knowledge/shopify-products",
    response_model=BrandProductKnowledgeShopifyProductsResponse,
    response_model_by_alias=True,
)
async def list_product_knowledge_shopify_products(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> BrandProductKnowledgeShopifyProductsResponse:
    await get_project_in_default_workspace(project_id, session)
    connected, products = await list_shopify_products_for_picker(session, project_id)
    if not connected:
        return BrandProductKnowledgeShopifyProductsResponse(
            shopify_connected=False,
            message="Collega e sincronizza Shopify per selezionare prodotti reali.",
            products=[],
        )
    return BrandProductKnowledgeShopifyProductsResponse(
        shopify_connected=True,
        products=[
            BrandProductKnowledgeShopifyProductOption(
                id=p.id,
                shopify_gid=p.shopify_gid,
                title=p.title,
                handle=p.handle,
                status=p.status,
                vendor=p.vendor,
                product_type=p.product_type,
                featured_image_url=p.featured_image_url,
                has_knowledge_item=has_item,
            )
            for p, has_item in products
        ],
    )


@router.get(
    "/{project_id}/brand-intelligence/product-knowledge/items",
    response_model=list[BrandProductKnowledgeItemRead],
    response_model_by_alias=True,
)
async def list_product_knowledge_items(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> list[BrandProductKnowledgeItemRead]:
    await get_project_in_default_workspace(project_id, session)
    rows = await list_items(session, project_id)
    result: list[BrandProductKnowledgeItemRead] = []
    for row in rows:
        read = BrandProductKnowledgeItemRead.model_validate(row)
        read.completion_status = item_completion(row)
        result.append(read)
    return result


@router.post(
    "/{project_id}/brand-intelligence/product-knowledge/items/import-file",
    response_model=BrandProductKnowledgeItemsImportResponse,
    response_model_by_alias=True,
)
async def import_product_knowledge_items_file(
    project_id: UUID,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db),
) -> BrandProductKnowledgeItemsImportResponse:
    await get_project_in_default_workspace(project_id, session)
    data = await file.read()
    return await import_items_from_file(
        session,
        project_id,
        filename=file.filename or "document",
        content_type=file.content_type,
        data=data,
    )


@router.post(
    "/{project_id}/brand-intelligence/product-knowledge/items/apply-import-proposal",
    response_model=BrandProductKnowledgeItemsApplyImportResponse,
    response_model_by_alias=True,
)
async def apply_product_knowledge_items_import_proposal(
    project_id: UUID,
    payload: BrandProductKnowledgeItemsApplyImportRequest,
    session: AsyncSession = Depends(get_db),
) -> BrandProductKnowledgeItemsApplyImportResponse:
    await get_project_in_default_workspace(project_id, session)
    return await apply_items_import_proposal(session, project_id, payload.items)


@router.post(
    "/{project_id}/brand-intelligence/product-knowledge/items/from-shopify",
    response_model=BrandProductKnowledgeItemRead,
    response_model_by_alias=True,
)
async def create_product_knowledge_item_from_shopify(
    project_id: UUID,
    payload: BrandProductKnowledgeItemFromShopifyRequest,
    session: AsyncSession = Depends(get_db),
) -> BrandProductKnowledgeItemRead:
    await get_project_in_default_workspace(project_id, session)
    row = await create_item_from_shopify(session, project_id, payload.shopify_product_id)
    read = BrandProductKnowledgeItemRead.model_validate(row)
    read.completion_status = item_completion(row)
    return read


@router.get(
    "/{project_id}/brand-intelligence/product-knowledge/items/{item_id}",
    response_model=BrandProductKnowledgeItemRead,
    response_model_by_alias=True,
)
async def get_product_knowledge_item(
    project_id: UUID,
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> BrandProductKnowledgeItemRead:
    await get_project_in_default_workspace(project_id, session)
    row = await get_item(session, project_id, item_id)
    read = BrandProductKnowledgeItemRead.model_validate(row)
    read.completion_status = item_completion(row)
    return read


@router.put(
    "/{project_id}/brand-intelligence/product-knowledge/items/{item_id}",
    response_model=BrandProductKnowledgeItemRead,
    response_model_by_alias=True,
)
async def update_product_knowledge_item(
    project_id: UUID,
    item_id: UUID,
    payload: BrandProductKnowledgeItemUpdate,
    session: AsyncSession = Depends(get_db),
) -> BrandProductKnowledgeItemRead:
    await get_project_in_default_workspace(project_id, session)
    row = await update_item(session, project_id, item_id, payload)
    read = BrandProductKnowledgeItemRead.model_validate(row)
    read.completion_status = item_completion(row)
    return read


@router.delete(
    "/{project_id}/brand-intelligence/product-knowledge/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_product_knowledge_item(
    project_id: UUID,
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> None:
    await get_project_in_default_workspace(project_id, session)
    await delete_item(session, project_id, item_id)


@router.get(
    "/{project_id}/brand-intelligence/voice",
    response_model=BrandVoiceRead,
    response_model_by_alias=True,
    deprecated=True,
)
async def get_brand_voice(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> BrandVoiceRead:
    await get_project_in_default_workspace(project_id, session)
    row = await bi_service.get_voice(session, project_id)
    return BrandVoiceRead.model_validate(row)


@router.put(
    "/{project_id}/brand-intelligence/voice",
    response_model=BrandVoiceRead,
    response_model_by_alias=True,
    deprecated=True,
)
async def update_brand_voice(
    project_id: UUID,
    payload: BrandVoiceUpdate,
    session: AsyncSession = Depends(get_db),
) -> BrandVoiceRead:
    await get_project_in_default_workspace(project_id, session)
    row = await bi_service.upsert_voice(session, project_id, payload)
    return BrandVoiceRead.model_validate(row)


@router.get(
    "/{project_id}/brand-intelligence/products",
    response_model=list[BrandProductKnowledgeRead],
    response_model_by_alias=True,
    deprecated=True,
)
async def list_brand_products(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> list[BrandProductKnowledgeRead]:
    await get_project_in_default_workspace(project_id, session)
    rows = await bi_service.list_products(session, project_id)
    return [BrandProductKnowledgeRead.model_validate(r) for r in rows]


@router.post(
    "/{project_id}/brand-intelligence/products",
    response_model=BrandProductKnowledgeRead,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=True,
    deprecated=True,
)
async def create_brand_product(
    project_id: UUID,
    payload: BrandProductKnowledgeCreate,
    session: AsyncSession = Depends(get_db),
) -> BrandProductKnowledgeRead:
    await get_project_in_default_workspace(project_id, session)
    row = await bi_service.create_product(session, project_id, payload)
    return BrandProductKnowledgeRead.model_validate(row)


@router.put(
    "/{project_id}/brand-intelligence/products/{item_id}",
    response_model=BrandProductKnowledgeRead,
    response_model_by_alias=True,
    deprecated=True,
)
async def update_brand_product(
    project_id: UUID,
    item_id: UUID,
    payload: BrandProductKnowledgeUpdate,
    session: AsyncSession = Depends(get_db),
) -> BrandProductKnowledgeRead:
    await get_project_in_default_workspace(project_id, session)
    row = await bi_service.update_product(session, project_id, item_id, payload)
    return BrandProductKnowledgeRead.model_validate(row)


@router.delete(
    "/{project_id}/brand-intelligence/products/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    deprecated=True,
)
async def delete_brand_product(
    project_id: UUID,
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> None:
    await get_project_in_default_workspace(project_id, session)
    await bi_service.delete_product(session, project_id, item_id)


@router.get(
    "/{project_id}/brand-intelligence/audience",
    response_model=list[BrandAudienceInsightRead],
    response_model_by_alias=True,
    deprecated=True,
)
async def list_brand_audience(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> list[BrandAudienceInsightRead]:
    await get_project_in_default_workspace(project_id, session)
    rows = await bi_service.list_audience(session, project_id)
    return [BrandAudienceInsightRead.model_validate(r) for r in rows]


@router.post(
    "/{project_id}/brand-intelligence/audience",
    response_model=BrandAudienceInsightRead,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=True,
    deprecated=True,
)
async def create_brand_audience(
    project_id: UUID,
    payload: BrandAudienceInsightCreate,
    session: AsyncSession = Depends(get_db),
) -> BrandAudienceInsightRead:
    await get_project_in_default_workspace(project_id, session)
    row = await bi_service.create_audience(session, project_id, payload)
    return BrandAudienceInsightRead.model_validate(row)


@router.put(
    "/{project_id}/brand-intelligence/audience/{item_id}",
    response_model=BrandAudienceInsightRead,
    response_model_by_alias=True,
    deprecated=True,
)
async def update_brand_audience(
    project_id: UUID,
    item_id: UUID,
    payload: BrandAudienceInsightUpdate,
    session: AsyncSession = Depends(get_db),
) -> BrandAudienceInsightRead:
    await get_project_in_default_workspace(project_id, session)
    row = await bi_service.update_audience(session, project_id, item_id, payload)
    return BrandAudienceInsightRead.model_validate(row)


@router.delete(
    "/{project_id}/brand-intelligence/audience/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    deprecated=True,
)
async def delete_brand_audience(
    project_id: UUID,
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> None:
    await get_project_in_default_workspace(project_id, session)
    await bi_service.delete_audience(session, project_id, item_id)


@router.get(
    "/{project_id}/brand-intelligence/claims",
    response_model=list[BrandClaimRuleRead],
    response_model_by_alias=True,
    deprecated=True,
)
async def list_brand_claims(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> list[BrandClaimRuleRead]:
    await get_project_in_default_workspace(project_id, session)
    rows = await bi_service.list_claims(session, project_id)
    return [BrandClaimRuleRead.model_validate(r) for r in rows]


@router.post(
    "/{project_id}/brand-intelligence/claims",
    response_model=BrandClaimRuleRead,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=True,
    deprecated=True,
)
async def create_brand_claim(
    project_id: UUID,
    payload: BrandClaimRuleCreate,
    session: AsyncSession = Depends(get_db),
) -> BrandClaimRuleRead:
    await get_project_in_default_workspace(project_id, session)
    row = await bi_service.create_claim(session, project_id, payload)
    return BrandClaimRuleRead.model_validate(row)


@router.put(
    "/{project_id}/brand-intelligence/claims/{item_id}",
    response_model=BrandClaimRuleRead,
    response_model_by_alias=True,
    deprecated=True,
)
async def update_brand_claim(
    project_id: UUID,
    item_id: UUID,
    payload: BrandClaimRuleUpdate,
    session: AsyncSession = Depends(get_db),
) -> BrandClaimRuleRead:
    await get_project_in_default_workspace(project_id, session)
    row = await bi_service.update_claim(session, project_id, item_id, payload)
    return BrandClaimRuleRead.model_validate(row)


@router.delete(
    "/{project_id}/brand-intelligence/claims/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    deprecated=True,
)
async def delete_brand_claim(
    project_id: UUID,
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> None:
    await get_project_in_default_workspace(project_id, session)
    await bi_service.delete_claim(session, project_id, item_id)


@router.get(
    "/{project_id}/brand-intelligence/seo-strategy",
    response_model=BrandSeoStrategyRead,
    response_model_by_alias=True,
    deprecated=True,
)
async def get_brand_seo_strategy(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> BrandSeoStrategyRead:
    await get_project_in_default_workspace(project_id, session)
    row = await bi_service.get_seo_strategy(session, project_id)
    return BrandSeoStrategyRead.model_validate(row)


@router.put(
    "/{project_id}/brand-intelligence/seo-strategy",
    response_model=BrandSeoStrategyRead,
    response_model_by_alias=True,
    deprecated=True,
)
async def update_brand_seo_strategy(
    project_id: UUID,
    payload: BrandSeoStrategyUpdate,
    session: AsyncSession = Depends(get_db),
) -> BrandSeoStrategyRead:
    await get_project_in_default_workspace(project_id, session)
    row = await bi_service.upsert_seo_strategy(session, project_id, payload)
    return BrandSeoStrategyRead.model_validate(row)


@router.get(
    "/{project_id}/brand-intelligence/content-pillars",
    response_model=list[BrandContentPillarRead],
    response_model_by_alias=True,
    deprecated=True,
)
async def list_brand_pillars(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> list[BrandContentPillarRead]:
    await get_project_in_default_workspace(project_id, session)
    rows = await bi_service.list_pillars(session, project_id)
    return [BrandContentPillarRead.model_validate(r) for r in rows]


@router.post(
    "/{project_id}/brand-intelligence/content-pillars",
    response_model=BrandContentPillarRead,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=True,
    deprecated=True,
)
async def create_brand_pillar(
    project_id: UUID,
    payload: BrandContentPillarCreate,
    session: AsyncSession = Depends(get_db),
) -> BrandContentPillarRead:
    await get_project_in_default_workspace(project_id, session)
    row = await bi_service.create_pillar(session, project_id, payload)
    return BrandContentPillarRead.model_validate(row)


@router.put(
    "/{project_id}/brand-intelligence/content-pillars/{item_id}",
    response_model=BrandContentPillarRead,
    response_model_by_alias=True,
    deprecated=True,
)
async def update_brand_pillar(
    project_id: UUID,
    item_id: UUID,
    payload: BrandContentPillarUpdate,
    session: AsyncSession = Depends(get_db),
) -> BrandContentPillarRead:
    await get_project_in_default_workspace(project_id, session)
    row = await bi_service.update_pillar(session, project_id, item_id, payload)
    return BrandContentPillarRead.model_validate(row)


@router.delete(
    "/{project_id}/brand-intelligence/content-pillars/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    deprecated=True,
)
async def delete_brand_pillar(
    project_id: UUID,
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> None:
    await get_project_in_default_workspace(project_id, session)
    await bi_service.delete_pillar(session, project_id, item_id)


@router.get(
    "/{project_id}/brand-intelligence/guardrails",
    response_model=list[BrandAiGuardrailRead],
    response_model_by_alias=True,
    deprecated=True,
)
async def list_brand_guardrails(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> list[BrandAiGuardrailRead]:
    await get_project_in_default_workspace(project_id, session)
    rows = await bi_service.list_guardrails(session, project_id)
    return [BrandAiGuardrailRead.model_validate(r) for r in rows]


@router.post(
    "/{project_id}/brand-intelligence/guardrails",
    response_model=BrandAiGuardrailRead,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=True,
    deprecated=True,
)
async def create_brand_guardrail(
    project_id: UUID,
    payload: BrandAiGuardrailCreate,
    session: AsyncSession = Depends(get_db),
) -> BrandAiGuardrailRead:
    await get_project_in_default_workspace(project_id, session)
    row = await bi_service.create_guardrail(session, project_id, payload)
    return BrandAiGuardrailRead.model_validate(row)


@router.put(
    "/{project_id}/brand-intelligence/guardrails/{item_id}",
    response_model=BrandAiGuardrailRead,
    response_model_by_alias=True,
    deprecated=True,
)
async def update_brand_guardrail(
    project_id: UUID,
    item_id: UUID,
    payload: BrandAiGuardrailUpdate,
    session: AsyncSession = Depends(get_db),
) -> BrandAiGuardrailRead:
    await get_project_in_default_workspace(project_id, session)
    row = await bi_service.update_guardrail(session, project_id, item_id, payload)
    return BrandAiGuardrailRead.model_validate(row)


@router.delete(
    "/{project_id}/brand-intelligence/guardrails/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    deprecated=True,
)
async def delete_brand_guardrail(
    project_id: UUID,
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> None:
    await get_project_in_default_workspace(project_id, session)
    await bi_service.delete_guardrail(session, project_id, item_id)


@router.get(
    "/{project_id}/brand-intelligence/assets",
    response_model=list[BrandAssetRead],
    response_model_by_alias=True,
    deprecated=True,
)
async def list_brand_assets(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> list[BrandAssetRead]:
    await get_project_in_default_workspace(project_id, session)
    rows = await bi_service.list_assets(session, project_id)
    return [BrandAssetRead.model_validate(r) for r in rows]


@router.post(
    "/{project_id}/brand-intelligence/assets",
    response_model=BrandAssetRead,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=True,
    deprecated=True,
)
async def create_brand_asset(
    project_id: UUID,
    payload: BrandAssetCreate,
    session: AsyncSession = Depends(get_db),
) -> BrandAssetRead:
    await get_project_in_default_workspace(project_id, session)
    row = await bi_service.create_asset(session, project_id, payload)
    return BrandAssetRead.model_validate(row)


@router.put(
    "/{project_id}/brand-intelligence/assets/{item_id}",
    response_model=BrandAssetRead,
    response_model_by_alias=True,
    deprecated=True,
)
async def update_brand_asset(
    project_id: UUID,
    item_id: UUID,
    payload: BrandAssetUpdate,
    session: AsyncSession = Depends(get_db),
) -> BrandAssetRead:
    await get_project_in_default_workspace(project_id, session)
    row = await bi_service.update_asset(session, project_id, item_id, payload)
    return BrandAssetRead.model_validate(row)


@router.delete(
    "/{project_id}/brand-intelligence/assets/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    deprecated=True,
)
async def delete_brand_asset(
    project_id: UUID,
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> None:
    await get_project_in_default_workspace(project_id, session)
    await bi_service.delete_asset(session, project_id, item_id)


@router.post(
    "/{project_id}/brand-intelligence/import-batches",
    response_model=BrandImportBatchCreateResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
)
async def create_brand_import_batch(
    project_id: UUID,
    body: BrandImportBatchCreateRequest,
    session: AsyncSession = Depends(get_db),
) -> BrandImportBatchCreateResponse:
    await get_project_in_default_workspace(project_id, session)
    return await create_import_batch_with_sources(
        session,
        project_id,
        batch_name=body.batch_name,
        brand_name=body.brand_name,
        website_url=body.website_url,
        sources=body.sources,
    )


@router.post(
    "/{project_id}/brand-intelligence/sources/upload",
    response_model=BrandSourceDocumentsUploadResponse,
    response_model_by_alias=True,
    deprecated=True,
)
async def upload_brand_source_documents(
    project_id: UUID,
    files: list[UploadFile] = File(default=[]),
    batch_name: str | None = Form(default=None, alias="batchName"),
    source_type: str = Form(default="file_upload", alias="sourceType"),
    notes: str | None = Form(default=None),
    brand_name: str | None = Form(default=None, alias="brandName"),
    website_url: str | None = Form(default=None, alias="websiteUrl"),
    sources: str | None = Form(default=None),
    batch_id: UUID | None = Form(default=None, alias="batchId"),
    session: AsyncSession = Depends(get_db),
) -> BrandSourceDocumentsUploadResponse:
    await get_project_in_default_workspace(project_id, session)
    parsed_sources = parse_sources_json(sources)
    return await sources_service.upload_source_documents(
        session,
        project_id,
        files,
        batch_name=batch_name,
        source_type=source_type,
        notes=notes,
        brand_name=brand_name,
        website_url=website_url,
        sources=parsed_sources,
        batch_id=batch_id,
    )


@router.post(
    "/{project_id}/brand-intelligence/import-batches/{batch_id}/start",
    response_model=BrandImportBatchStartResponse,
    response_model_by_alias=True,
    deprecated=True,
)
async def start_brand_import_batch(
    project_id: UUID,
    batch_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> BrandImportBatchStartResponse:
    await get_project_in_default_workspace(project_id, session)
    batch = await mark_batch_started(session, project_id, batch_id)
    schedule_batch_processing(batch_id)
    return BrandImportBatchStartResponse(batch_id=batch.id, status=batch.status)


@router.get(
    "/{project_id}/brand-intelligence/import-batches/{batch_id}/status",
    response_model=BrandImportBatchStatusResponse,
    response_model_by_alias=True,
    deprecated=True,
)
async def get_brand_import_batch_status(
    project_id: UUID,
    batch_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> BrandImportBatchStatusResponse:
    await get_project_in_default_workspace(project_id, session)
    return await get_batch_status(session, project_id, batch_id)


@router.get(
    "/{project_id}/brand-intelligence/import-batches",
    response_model=list[BrandImportBatchListItem],
    response_model_by_alias=True,
    deprecated=True,
)
async def list_brand_import_batches(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> list[BrandImportBatchListItem]:
    await get_project_in_default_workspace(project_id, session)
    return await list_batches(session, project_id)


@router.get(
    "/{project_id}/brand-intelligence/import-batches/{batch_id}/external-sources",
    response_model=list[BrandExternalSourceRead],
    response_model_by_alias=True,
    deprecated=True,
)
async def list_batch_external_sources(
    project_id: UUID,
    batch_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> list[BrandExternalSourceRead]:
    await get_project_in_default_workspace(project_id, session)
    rows = await list_external_sources_for_batch(session, project_id, batch_id)
    return [BrandExternalSourceRead.model_validate(r) for r in rows]


@router.post(
    "/{project_id}/brand-intelligence/import-batches/{batch_id}/external-sources",
    response_model=list[BrandExternalSourceRead],
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
)
async def add_batch_external_sources(
    project_id: UUID,
    batch_id: UUID,
    body: BrandExternalSourcesAddRequest,
    session: AsyncSession = Depends(get_db),
) -> list[BrandExternalSourceRead]:
    await get_project_in_default_workspace(project_id, session)
    return await add_external_sources_to_batch(
        session, project_id, batch_id, body.sources
    )


@router.post(
    "/{project_id}/brand-intelligence/import-batches/{batch_id}/fetch-sources",
    response_model=BrandExternalSourcesFetchResponse,
    response_model_by_alias=True,
    deprecated=True,
)
async def fetch_batch_external_sources_route(
    project_id: UUID,
    batch_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> BrandExternalSourcesFetchResponse:
    await get_project_in_default_workspace(project_id, session)
    await get_batch_status(session, project_id, batch_id)
    warnings, fetched_count = await fetch_batch_external_sources(
        session, batch_id, refetch_failed=True
    )
    return BrandExternalSourcesFetchResponse(
        fetched_count=fetched_count,
        warnings=warnings,
    )


@router.put(
    "/{project_id}/brand-intelligence/import-batches/{batch_id}/sources",
    response_model=BrandImportBatchSourcesUpdateResponse,
    response_model_by_alias=True,
    deprecated=True,
)
async def update_import_batch_sources(
    project_id: UUID,
    batch_id: UUID,
    body: BrandImportBatchSourcesUpdateRequest,
    session: AsyncSession = Depends(get_db),
) -> BrandImportBatchSourcesUpdateResponse:
    await get_project_in_default_workspace(project_id, session)
    return await upsert_batch_sources(
        session,
        project_id,
        batch_id,
        brand_name=body.brand_name,
        website_url=body.website_url,
        sources=body.sources,
    )


@router.post(
    "/{project_id}/brand-intelligence/import-batches/{batch_id}/refresh-context",
    response_model=BrandImportBatchRefreshContextResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_202_ACCEPTED,
)
async def refresh_import_batch_context(
    project_id: UUID,
    batch_id: UUID,
    body: BrandImportBatchRefreshContextRequest,
    session: AsyncSession = Depends(get_db),
) -> BrandImportBatchRefreshContextResponse:
    await get_project_in_default_workspace(project_id, session)
    await get_batch_status(session, project_id, batch_id)
    schedule_refresh_context(
        batch_id,
        refetch_external_sources=body.refetch_external_sources,
        regenerate_section_drafts=body.regenerate_section_drafts,
        archive_previous_drafts=body.archive_previous_drafts,
    )
    return BrandImportBatchRefreshContextResponse(
        batch_id=batch_id,
        status="ai_processing",
        message="Aggiornamento contesto avviato.",
    )


@router.get(
    "/{project_id}/brand-intelligence/sources",
    response_model=list[BrandSourceDocumentRead],
    response_model_by_alias=True,
    deprecated=True,
)
async def list_brand_source_documents(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> list[BrandSourceDocumentRead]:
    await get_project_in_default_workspace(project_id, session)
    rows = await sources_service.list_source_documents(session, project_id)
    return [BrandSourceDocumentRead.model_validate(r) for r in rows]


@router.post(
    "/{project_id}/brand-intelligence/sources/{document_id}/extract",
    response_model=list[BrandExtractedFactRead],
    response_model_by_alias=True,
    deprecated=True,
)
async def extract_brand_source_document(
    project_id: UUID,
    document_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> list[BrandExtractedFactRead]:
    await get_project_in_default_workspace(project_id, session)
    facts = await run_ai_extraction(session, project_id, document_id)
    return [BrandExtractedFactRead.model_validate(f) for f in facts]


@router.post("/{project_id}/brand-intelligence/sources/extract-batch")
async def extract_brand_source_batch(
    project_id: UUID,
    payload: BrandExtractBatchRequest,
    session: AsyncSession = Depends(get_db),
) -> dict:
    """Deprecato: preferire import-batches/{id}/start + polling status."""
    await get_project_in_default_workspace(project_id, session)
    return await sources_service.extract_document_batch(
        session, project_id, payload.document_ids
    )


@router.get(
    "/{project_id}/brand-intelligence/extracted-facts",
    response_model=list[BrandExtractedFactRead],
    response_model_by_alias=True,
    deprecated=True,
)
async def list_brand_extracted_facts(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
    status: str | None = Query(default=None),
    target_section: str | None = Query(default=None, alias="targetSection"),
    source_document_id: UUID | None = Query(default=None, alias="sourceDocumentId"),
    batch_id: UUID | None = Query(default=None, alias="batchId"),
) -> list[BrandExtractedFactRead]:
    await get_project_in_default_workspace(project_id, session)
    rows = await sources_service.list_extracted_facts(
        session,
        project_id,
        status_filter=status,
        target_section=target_section,
        source_document_id=source_document_id,
        batch_id=batch_id,
    )
    return [BrandExtractedFactRead.model_validate(r) for r in rows]


@router.patch(
    "/{project_id}/brand-intelligence/extracted-facts/{fact_id}",
    response_model=BrandExtractedFactRead,
    response_model_by_alias=True,
    deprecated=True,
)
async def patch_brand_extracted_fact(
    project_id: UUID,
    fact_id: UUID,
    payload: BrandExtractedFactUpdate,
    session: AsyncSession = Depends(get_db),
) -> BrandExtractedFactRead:
    await get_project_in_default_workspace(project_id, session)
    row = await sources_service.patch_extracted_fact(session, project_id, fact_id, payload)
    return BrandExtractedFactRead.model_validate(row)


@router.post(
    "/{project_id}/brand-intelligence/extracted-facts/apply",
    response_model=BrandApplyFactsResponse,
    response_model_by_alias=True,
    deprecated=True,
)
async def apply_brand_extracted_facts(
    project_id: UUID,
    payload: BrandApplyFactsRequest,
    session: AsyncSession = Depends(get_db),
) -> BrandApplyFactsResponse:
    await get_project_in_default_workspace(project_id, session)
    return await sources_service.apply_facts(
        session, project_id, payload.fact_ids, batch_id=payload.batch_id
    )


@router.post(
    "/{project_id}/brand-intelligence/import-batches/{batch_id}/synthesize",
    response_model=BrandSectionDraftSynthesizeResponse,
    response_model_by_alias=True,
    deprecated=True,
)
async def synthesize_brand_import_batch(
    project_id: UUID,
    batch_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> BrandSectionDraftSynthesizeResponse:
    await get_project_in_default_workspace(project_id, session)
    return await synthesize_batch(session, project_id, batch_id)


@router.get(
    "/{project_id}/brand-intelligence/section-drafts",
    response_model=list[BrandSectionDraftListItem],
    response_model_by_alias=True,
    deprecated=True,
)
async def list_brand_section_drafts(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
    batch_id: UUID | None = Query(default=None, alias="batchId"),
    status: str | None = Query(default=None),
    section_key: str | None = Query(default=None, alias="sectionKey"),
    latest_only: bool = Query(default=True, alias="latestOnly"),
) -> list[BrandSectionDraftListItem]:
    await get_project_in_default_workspace(project_id, session)
    rows = await list_section_drafts(
        session,
        project_id,
        batch_id=batch_id,
        status_filter=status,
        section_key=section_key,
        latest_only=latest_only,
    )
    return [BrandSectionDraftListItem.model_validate(r) for r in rows]


@router.get(
    "/{project_id}/brand-intelligence/section-drafts/{draft_id}",
    response_model=BrandSectionDraftRead,
    response_model_by_alias=True,
    deprecated=True,
)
async def get_brand_section_draft(
    project_id: UUID,
    draft_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> BrandSectionDraftRead:
    await get_project_in_default_workspace(project_id, session)
    row = await get_section_draft(session, project_id, draft_id)
    return BrandSectionDraftRead.model_validate(row)


@router.patch(
    "/{project_id}/brand-intelligence/section-drafts/{draft_id}",
    response_model=BrandSectionDraftRead,
    response_model_by_alias=True,
    deprecated=True,
)
async def patch_brand_section_draft(
    project_id: UUID,
    draft_id: UUID,
    payload: BrandSectionDraftUpdate,
    session: AsyncSession = Depends(get_db),
) -> BrandSectionDraftRead:
    await get_project_in_default_workspace(project_id, session)
    row = await patch_section_draft(session, project_id, draft_id, payload)
    return BrandSectionDraftRead.model_validate(row)


@router.post(
    "/{project_id}/brand-intelligence/section-drafts/{draft_id}/apply",
    response_model=BrandSectionDraftApplyResponse,
    response_model_by_alias=True,
    deprecated=True,
)
async def apply_brand_section_draft(
    project_id: UUID,
    draft_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> BrandSectionDraftApplyResponse:
    await get_project_in_default_workspace(project_id, session)
    return await apply_section_draft(session, project_id, draft_id)


@router.post(
    "/{project_id}/brand-intelligence/section-drafts/apply-batch",
    response_model=BrandSectionDraftApplyResponse,
    response_model_by_alias=True,
    deprecated=True,
)
async def apply_brand_section_drafts_batch(
    project_id: UUID,
    payload: BrandSectionDraftApplyBatchRequest,
    session: AsyncSession = Depends(get_db),
) -> BrandSectionDraftApplyResponse:
    await get_project_in_default_workspace(project_id, session)
    return await apply_section_drafts_batch(session, project_id, payload.draft_ids)


@router.post(
    "/{project_id}/brand-intelligence/section-drafts/{draft_id}/regenerate",
    response_model=BrandSectionDraftRead,
    response_model_by_alias=True,
    deprecated=True,
)
async def regenerate_brand_section_draft(
    project_id: UUID,
    draft_id: UUID,
    payload: BrandSectionDraftRegenerateRequest | None = None,
    session: AsyncSession = Depends(get_db),
) -> BrandSectionDraftRead:
    await get_project_in_default_workspace(project_id, session)
    body = payload or BrandSectionDraftRegenerateRequest()
    row = await regenerate_section_draft(
        session,
        project_id,
        draft_id,
        instructions=body.instructions,
        include_fact_ids=body.include_fact_ids,
    )
    return BrandSectionDraftRead.model_validate(row)


@router.post(
    "/{project_id}/brand-intelligence/import-batches/{batch_id}/generate-brief",
    response_model=GenerateBriefResponse,
    response_model_by_alias=True,
    deprecated=True,
)
async def generate_brand_intelligence_brief(
    project_id: UUID,
    batch_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> GenerateBriefResponse:
    await get_project_in_default_workspace(project_id, session)
    brief = await generate_brief_from_batch(session, project_id, batch_id)
    return GenerateBriefResponse(
        brief_id=brief.id,
        status=brief.status,
        confidence=brief.confidence,
        message="Brand Intelligence Brief generato.",
    )


@router.get(
    "/{project_id}/brand-intelligence/briefs",
    response_model=list[BrandIntelligenceBriefListItem],
    response_model_by_alias=True,
    deprecated=True,
)
async def list_brand_intelligence_briefs(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> list[BrandIntelligenceBriefListItem]:
    await get_project_in_default_workspace(project_id, session)
    rows = await list_briefs(session, project_id)
    return [BrandIntelligenceBriefListItem.model_validate(r) for r in rows]


@router.get(
    "/{project_id}/brand-intelligence/briefs/{brief_id}",
    response_model=BrandIntelligenceBriefRead,
    response_model_by_alias=True,
    deprecated=True,
)
async def get_brand_intelligence_brief(
    project_id: UUID,
    brief_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> BrandIntelligenceBriefRead:
    await get_project_in_default_workspace(project_id, session)
    row = await get_brief(session, project_id, brief_id)
    return build_brand_intelligence_brief_read(row)


@router.patch(
    "/{project_id}/brand-intelligence/briefs/{brief_id}",
    response_model=BrandIntelligenceBriefRead,
    response_model_by_alias=True,
    deprecated=True,
)
async def patch_brand_intelligence_brief(
    project_id: UUID,
    brief_id: UUID,
    body: BrandIntelligenceBriefUpdate,
    session: AsyncSession = Depends(get_db),
) -> BrandIntelligenceBriefRead:
    await get_project_in_default_workspace(project_id, session)
    row = await patch_brief(session, project_id, brief_id, body)
    return build_brand_intelligence_brief_read(row)


@router.post(
    "/{project_id}/brand-intelligence/briefs/{brief_id}/approve",
    response_model=BrandIntelligenceBriefRead,
    response_model_by_alias=True,
    deprecated=True,
)
async def approve_brand_intelligence_brief(
    project_id: UUID,
    brief_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> BrandIntelligenceBriefRead:
    await get_project_in_default_workspace(project_id, session)
    row = await approve_brief(session, project_id, brief_id)
    return build_brand_intelligence_brief_read(row)


@router.post(
    "/{project_id}/brand-intelligence/briefs/{brief_id}/archive",
    response_model=BrandIntelligenceBriefRead,
    response_model_by_alias=True,
    deprecated=True,
)
async def archive_brand_intelligence_brief(
    project_id: UUID,
    brief_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> BrandIntelligenceBriefRead:
    await get_project_in_default_workspace(project_id, session)
    row = await archive_brief(session, project_id, brief_id)
    return build_brand_intelligence_brief_read(row)

