"""CRUD operations for Brand Intelligence entities."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brand_intelligence import (
    BrandAiGuardrail,
    BrandAsset,
    BrandAudienceInsight,
    BrandClaimRule,
    BrandContentPillar,
    BrandProductKnowledge,
    BrandProfile,
    BrandSeoStrategy,
    BrandVoice,
)
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
    BrandSectionStatus,
    BrandSeoStrategyUpdate,
    BrandVoiceUpdate,
)
from app.services.brand_intelligence.context import BrandIntelligenceContextBuilder
from app.services.brand_intelligence.score import (
    SECTION_LABELS,
    compute_brand_knowledge_score,
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
    voice = (
        await session.execute(select(BrandVoice).where(BrandVoice.project_id == project_id))
    ).scalar_one_or_none()
    products = await list_products(session, project_id)
    audience = await list_audience(session, project_id)
    claims = await list_claims(session, project_id)
    guardrails = await list_guardrails(session, project_id)
    pillars = await list_pillars(session, project_id)
    assets = await list_assets(session, project_id)

    sections = [
        BrandSectionStatus(
            key=key,
            label=SECTION_LABELS[key],
            complete=score.section_scores.get(key, 0) >= 60,
            score=score.section_scores.get(key, 0),
        )
        for key in SECTION_LABELS
    ]

    return BrandIntelligenceOverviewResponse(
        score=BrandKnowledgeScoreResponse.model_validate(score_to_response(score)),
        sections=sections,
        has_profile=profile is not None and bool(profile.brand_name),
        has_voice=voice is not None and bool(voice.tone),
        products_count=len(products),
        audience_count=len(audience),
        claims_count=len(claims),
        guardrails_count=len(guardrails),
        pillars_count=len(pillars),
        assets_count=len(assets),
    )


async def get_context_bundle(session: AsyncSession, project_id: UUID):
    return await BrandIntelligenceContextBuilder.build_brand_context(session, project_id)
