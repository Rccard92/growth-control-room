"""CRUD operations for Brand Intelligence entities."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brand_intelligence import (
    BrandAiGuardrail,
    BrandAsset,
    BrandAudienceInsight,
    BrandClaimRule,
    BrandContentPillar,
    BrandExtractedFact,
    BrandFaqObjections,
    BrandIdentity,
    BrandProductKnowledge,
    BrandProductKnowledgeGeneral,
    BrandProductKnowledgeItem,
    BrandProfile,
    BrandSafeClaims,
    BrandSeoStrategy,
    BrandSourceDocument,
    BrandVisualIdentity,
    BrandVoice,
)
from app.schemas.brand_identity_visual import BrandModuleStatus
from app.schemas.brand_intelligence import (
    BrandAiGuardrailCreate,
    BrandAiGuardrailUpdate,
    BrandAssetCreate,
    BrandAssetUpdate,
    BrandAudienceInsightCreate,
    BrandAudienceInsightUpdate,
    BrandClaimRuleCreate,
    BrandClaimRuleUpdate,
    BrandContentPillarCreate,
    BrandContentPillarUpdate,
    BrandIntelligenceOverviewResponse,
    BrandKnowledgeScoreResponse,
    BrandProductKnowledgeCreate,
    BrandProductKnowledgeUpdate,
    BrandProfileUpdate,
    BrandSeoStrategyUpdate,
    BrandVoiceUpdate,
)
from app.services.brand_intelligence.identity_service import (
    identity_completion,
    identity_missing_fields,
)
from app.services.brand_intelligence.safe_claims_service import (
    safe_claims_completion,
    safe_claims_missing_fields,
)
from app.services.brand_intelligence.visual_identity_service import (
    visual_completion,
    visual_missing_fields,
)
from app.services.brand_intelligence.context import BrandIntelligenceContextBuilder
from app.services.brand_intelligence.product_knowledge_general_service import general_has_content
from app.services.brand_intelligence.faq_objections_service import (
    faq_objections_completion,
    faq_objections_missing_fields,
)
from app.services.brand_intelligence.score import (
    SECTION_LABELS,
    compute_brand_knowledge_score,
    product_knowledge_missing_fields,
    product_knowledge_module_completion,
    profile_has_minimum,
    profile_is_complete,
    profile_missing_context,
    profile_missing_fields,
    score_to_response,
)


async def _get_or_create_profile(session: AsyncSession, project_id: UUID) -> BrandProfile:
    row = (
        await session.execute(select(BrandProfile).where(BrandProfile.project_id == project_id))
    ).scalar_one_or_none()
    if row:
        return row
    row = BrandProfile(project_id=project_id)
    session.add(row)
    await session.flush()
    return row


async def _get_or_create_voice(session: AsyncSession, project_id: UUID) -> BrandVoice:
    row = (
        await session.execute(select(BrandVoice).where(BrandVoice.project_id == project_id))
    ).scalar_one_or_none()
    if row:
        return row
    row = BrandVoice(project_id=project_id)
    session.add(row)
    await session.flush()
    return row


async def _get_or_create_seo(session: AsyncSession, project_id: UUID) -> BrandSeoStrategy:
    row = (
        await session.execute(
            select(BrandSeoStrategy).where(BrandSeoStrategy.project_id == project_id)
        )
    ).scalar_one_or_none()
    if row:
        return row
    row = BrandSeoStrategy(project_id=project_id)
    session.add(row)
    await session.flush()
    return row


def _apply_update(model: object, data: dict) -> None:
    for key, value in data.items():
        if value is not None:
            setattr(model, key, value)


async def get_profile(session: AsyncSession, project_id: UUID) -> BrandProfile:
    return await _get_or_create_profile(session, project_id)


async def upsert_profile(
    session: AsyncSession, project_id: UUID, payload: BrandProfileUpdate
) -> BrandProfile:
    row = await _get_or_create_profile(session, project_id)
    _apply_update(row, payload.model_dump(exclude_unset=True))
    await session.commit()
    await session.refresh(row)
    return row


async def get_voice(session: AsyncSession, project_id: UUID) -> BrandVoice:
    return await _get_or_create_voice(session, project_id)


async def upsert_voice(
    session: AsyncSession, project_id: UUID, payload: BrandVoiceUpdate
) -> BrandVoice:
    row = await _get_or_create_voice(session, project_id)
    _apply_update(row, payload.model_dump(exclude_unset=True))
    await session.commit()
    await session.refresh(row)
    return row


async def list_products(session: AsyncSession, project_id: UUID) -> list[BrandProductKnowledge]:
    return list(
        (
            await session.execute(
                select(BrandProductKnowledge).where(
                    BrandProductKnowledge.project_id == project_id
                )
            )
        ).scalars().all()
    )


async def create_product(
    session: AsyncSession, project_id: UUID, payload: BrandProductKnowledgeCreate
) -> BrandProductKnowledge:
    row = BrandProductKnowledge(project_id=project_id, **payload.model_dump())
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def update_product(
    session: AsyncSession,
    project_id: UUID,
    item_id: UUID,
    payload: BrandProductKnowledgeUpdate,
) -> BrandProductKnowledge:
    row = await _get_entity(session, BrandProductKnowledge, project_id, item_id)
    _apply_update(row, payload.model_dump(exclude_unset=True))
    await session.commit()
    await session.refresh(row)
    return row


async def delete_product(session: AsyncSession, project_id: UUID, item_id: UUID) -> None:
    row = await _get_entity(session, BrandProductKnowledge, project_id, item_id)
    await session.delete(row)
    await session.commit()


async def list_audience(session: AsyncSession, project_id: UUID) -> list[BrandAudienceInsight]:
    return list(
        (
            await session.execute(
                select(BrandAudienceInsight).where(
                    BrandAudienceInsight.project_id == project_id
                )
            )
        ).scalars().all()
    )


async def create_audience(
    session: AsyncSession, project_id: UUID, payload: BrandAudienceInsightCreate
) -> BrandAudienceInsight:
    row = BrandAudienceInsight(project_id=project_id, **payload.model_dump())
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def update_audience(
    session: AsyncSession,
    project_id: UUID,
    item_id: UUID,
    payload: BrandAudienceInsightUpdate,
) -> BrandAudienceInsight:
    row = await _get_entity(session, BrandAudienceInsight, project_id, item_id)
    _apply_update(row, payload.model_dump(exclude_unset=True))
    await session.commit()
    await session.refresh(row)
    return row


async def delete_audience(session: AsyncSession, project_id: UUID, item_id: UUID) -> None:
    row = await _get_entity(session, BrandAudienceInsight, project_id, item_id)
    await session.delete(row)
    await session.commit()


async def list_claims(session: AsyncSession, project_id: UUID) -> list[BrandClaimRule]:
    return list(
        (
            await session.execute(
                select(BrandClaimRule).where(BrandClaimRule.project_id == project_id)
            )
        ).scalars().all()
    )


async def create_claim(
    session: AsyncSession, project_id: UUID, payload: BrandClaimRuleCreate
) -> BrandClaimRule:
    row = BrandClaimRule(project_id=project_id, **payload.model_dump())
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def update_claim(
    session: AsyncSession,
    project_id: UUID,
    item_id: UUID,
    payload: BrandClaimRuleUpdate,
) -> BrandClaimRule:
    row = await _get_entity(session, BrandClaimRule, project_id, item_id)
    _apply_update(row, payload.model_dump(exclude_unset=True))
    await session.commit()
    await session.refresh(row)
    return row


async def delete_claim(session: AsyncSession, project_id: UUID, item_id: UUID) -> None:
    row = await _get_entity(session, BrandClaimRule, project_id, item_id)
    await session.delete(row)
    await session.commit()


async def get_seo_strategy(session: AsyncSession, project_id: UUID) -> BrandSeoStrategy:
    return await _get_or_create_seo(session, project_id)


async def upsert_seo_strategy(
    session: AsyncSession, project_id: UUID, payload: BrandSeoStrategyUpdate
) -> BrandSeoStrategy:
    row = await _get_or_create_seo(session, project_id)
    _apply_update(row, payload.model_dump(exclude_unset=True))
    await session.commit()
    await session.refresh(row)
    return row


async def list_pillars(session: AsyncSession, project_id: UUID) -> list[BrandContentPillar]:
    return list(
        (
            await session.execute(
                select(BrandContentPillar).where(
                    BrandContentPillar.project_id == project_id
                )
            )
        ).scalars().all()
    )


async def create_pillar(
    session: AsyncSession, project_id: UUID, payload: BrandContentPillarCreate
) -> BrandContentPillar:
    row = BrandContentPillar(project_id=project_id, **payload.model_dump())
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def update_pillar(
    session: AsyncSession,
    project_id: UUID,
    item_id: UUID,
    payload: BrandContentPillarUpdate,
) -> BrandContentPillar:
    row = await _get_entity(session, BrandContentPillar, project_id, item_id)
    _apply_update(row, payload.model_dump(exclude_unset=True))
    await session.commit()
    await session.refresh(row)
    return row


async def delete_pillar(session: AsyncSession, project_id: UUID, item_id: UUID) -> None:
    row = await _get_entity(session, BrandContentPillar, project_id, item_id)
    await session.delete(row)
    await session.commit()


async def list_guardrails(session: AsyncSession, project_id: UUID) -> list[BrandAiGuardrail]:
    return list(
        (
            await session.execute(
                select(BrandAiGuardrail).where(
                    BrandAiGuardrail.project_id == project_id
                )
            )
        ).scalars().all()
    )


async def create_guardrail(
    session: AsyncSession, project_id: UUID, payload: BrandAiGuardrailCreate
) -> BrandAiGuardrail:
    row = BrandAiGuardrail(project_id=project_id, **payload.model_dump())
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def update_guardrail(
    session: AsyncSession,
    project_id: UUID,
    item_id: UUID,
    payload: BrandAiGuardrailUpdate,
) -> BrandAiGuardrail:
    row = await _get_entity(session, BrandAiGuardrail, project_id, item_id)
    _apply_update(row, payload.model_dump(exclude_unset=True))
    await session.commit()
    await session.refresh(row)
    return row


async def delete_guardrail(session: AsyncSession, project_id: UUID, item_id: UUID) -> None:
    row = await _get_entity(session, BrandAiGuardrail, project_id, item_id)
    await session.delete(row)
    await session.commit()


async def list_assets(session: AsyncSession, project_id: UUID) -> list[BrandAsset]:
    return list(
        (
            await session.execute(
                select(BrandAsset).where(BrandAsset.project_id == project_id)
            )
        ).scalars().all()
    )


async def create_asset(
    session: AsyncSession, project_id: UUID, payload: BrandAssetCreate
) -> BrandAsset:
    row = BrandAsset(project_id=project_id, **payload.model_dump())
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def update_asset(
    session: AsyncSession,
    project_id: UUID,
    item_id: UUID,
    payload: BrandAssetUpdate,
) -> BrandAsset:
    row = await _get_entity(session, BrandAsset, project_id, item_id)
    _apply_update(row, payload.model_dump(exclude_unset=True))
    await session.commit()
    await session.refresh(row)
    return row


async def delete_asset(session: AsyncSession, project_id: UUID, item_id: UUID) -> None:
    row = await _get_entity(session, BrandAsset, project_id, item_id)
    await session.delete(row)
    await session.commit()


async def _get_entity(
    session: AsyncSession,
    model: type,
    project_id: UUID,
    item_id: UUID,
):
    row = (
        await session.execute(
            select(model).where(model.id == item_id, model.project_id == project_id)
        )
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Elemento non trovato.")
    return row


async def get_knowledge_score(
    session: AsyncSession, project_id: UUID
) -> BrandKnowledgeScoreResponse:
    score = await compute_brand_knowledge_score(session, project_id)
    return BrandKnowledgeScoreResponse.model_validate(score_to_response(score))


async def build_overview(
    session: AsyncSession, project_id: UUID
) -> BrandIntelligenceOverviewResponse:
    score = await compute_brand_knowledge_score(session, project_id)
    profile = (
        await session.execute(select(BrandProfile).where(BrandProfile.project_id == project_id))
    ).scalar_one_or_none()
    identity = (
        await session.execute(select(BrandIdentity).where(BrandIdentity.project_id == project_id))
    ).scalar_one_or_none()
    visual = (
        await session.execute(
            select(BrandVisualIdentity).where(BrandVisualIdentity.project_id == project_id)
        )
    ).scalar_one_or_none()
    safe_claims = (
        await session.execute(
            select(BrandSafeClaims).where(BrandSafeClaims.project_id == project_id)
        )
    ).scalar_one_or_none()
    pk_general = (
        await session.execute(
            select(BrandProductKnowledgeGeneral).where(
                BrandProductKnowledgeGeneral.project_id == project_id
            )
        )
    ).scalar_one_or_none()
    pk_items = list(
        (
            await session.execute(
                select(BrandProductKnowledgeItem).where(
                    BrandProductKnowledgeItem.project_id == project_id
                )
            )
        ).scalars().all()
    )
    faq_objections = (
        await session.execute(
            select(BrandFaqObjections).where(BrandFaqObjections.project_id == project_id)
        )
    ).scalar_one_or_none()

    sections = [
        BrandModuleStatus(
            key="brandProfile",
            label=SECTION_LABELS["brandProfile"],
            status="complete"
            if profile_is_complete(profile)
            else "partial"
            if profile_has_minimum(profile)
            else "empty",
            missing_fields=profile_missing_fields(profile),
            updated_at=profile.updated_at if profile else None,
        ),
        BrandModuleStatus(
            key="brandIdentity",
            label=SECTION_LABELS["brandIdentity"],
            status=identity_completion(identity),
            missing_fields=identity_missing_fields(identity),
            updated_at=identity.updated_at if identity else None,
        ),
        BrandModuleStatus(
            key="visualIdentity",
            label=SECTION_LABELS["visualIdentity"],
            status=visual_completion(visual),
            missing_fields=visual_missing_fields(visual),
            updated_at=visual.updated_at if visual else None,
        ),
        BrandModuleStatus(
            key="safeClaims",
            label=SECTION_LABELS["safeClaims"],
            status=safe_claims_completion(safe_claims),
            missing_fields=safe_claims_missing_fields(safe_claims),
            updated_at=safe_claims.updated_at if safe_claims else None,
        ),
        BrandModuleStatus(
            key="productKnowledge",
            label=SECTION_LABELS["productKnowledge"],
            status=product_knowledge_module_completion(pk_general, len(pk_items)),
            missing_fields=product_knowledge_missing_fields(pk_general, len(pk_items)),
            updated_at=(
                pk_general.updated_at
                if pk_general and general_has_content(pk_general)
                else (pk_items[0].updated_at if pk_items else None)
            ),
        ),
        BrandModuleStatus(
            key="faqObjections",
            label=SECTION_LABELS["faqObjections"],
            status=faq_objections_completion(faq_objections),
            missing_fields=faq_objections_missing_fields(faq_objections),
            updated_at=faq_objections.updated_at if faq_objections else None,
        ),
    ]

    return BrandIntelligenceOverviewResponse(
        score=BrandKnowledgeScoreResponse.model_validate(score_to_response(score)),
        sections=sections,
        has_profile=profile is not None and bool(profile.brand_name),
        profile_complete=profile_is_complete(profile),
        brand_name=profile.brand_name if profile else None,
        website_url=profile.website_url if profile else None,
        last_updated=profile.updated_at if profile else None,
        enrichment_confidence=profile.enrichment_confidence if profile else None,
        enrichment_warnings=profile.enrichment_warnings if profile else None,
        has_voice=False,
        products_count=len(pk_items),
        audience_count=0,
        claims_count=0,
        guardrails_count=0,
        pillars_count=0,
        assets_count=0,
        source_documents_count=0,
        pending_facts_count=0,
        pending_section_drafts_count=0,
        latest_batch_id=None,
        has_approved_brief=False,
        approved_brief_id=None,
        brief_version=None,
        brief_approved_at=None,
        pending_brief_count=0,
    )


async def get_context_bundle(session: AsyncSession, project_id: UUID):
    return await BrandIntelligenceContextBuilder.build_brand_context(session, project_id)
