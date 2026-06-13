from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
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
)
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
    session: AsyncSession = Depends(get_db),
) -> BrandContextBundleResponse:
    await get_project_in_default_workspace(project_id, session)
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


@router.get(
    "/{project_id}/brand-intelligence/voice",
    response_model=BrandVoiceRead,
    response_model_by_alias=True,
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


@router.get(
    "/{project_id}/brand-intelligence/sources",
    response_model=list[BrandSourceDocumentRead],
    response_model_by_alias=True,
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
)
async def list_brand_section_drafts(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
    batch_id: UUID | None = Query(default=None, alias="batchId"),
    status: str | None = Query(default=None),
    section_key: str | None = Query(default=None, alias="sectionKey"),
) -> list[BrandSectionDraftListItem]:
    await get_project_in_default_workspace(project_id, session)
    rows = await list_section_drafts(
        session,
        project_id,
        batch_id=batch_id,
        status_filter=status,
        section_key=section_key,
    )
    return [BrandSectionDraftListItem.model_validate(r) for r in rows]


@router.get(
    "/{project_id}/brand-intelligence/section-drafts/{draft_id}",
    response_model=BrandSectionDraftRead,
    response_model_by_alias=True,
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

