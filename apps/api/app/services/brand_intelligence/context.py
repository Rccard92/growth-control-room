"""
Brand Intelligence context builder.

Any AI module that generates brand-facing content must call
BrandIntelligenceContextBuilder before generating output.
"""

from uuid import UUID

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
    BrandAiGuardrailRead,
    BrandAssetRead,
    BrandAudienceInsightRead,
    BrandClaimRuleRead,
    BrandContentPillarRead,
    BrandContextBundleResponse,
    BrandKnowledgeScoreResponse,
    BrandProductKnowledgeRead,
    BrandProfileRead,
    BrandSeoStrategyRead,
    BrandVoiceRead,
)
from app.services.brand_intelligence.score import (
    BrandKnowledgeScore,
    compute_brand_knowledge_score,
    score_to_response,
)


class BrandIntelligenceContextBuilder:
    """
    Central source of truth for brand context used by all AI modules.

    Any AI module that generates brand-facing content must call
    BrandIntelligenceContextBuilder before generating output.
    """

    @staticmethod
    async def build_brand_context(
        session: AsyncSession,
        project_id: UUID,
    ) -> BrandContextBundleResponse:
        profile = (
            await session.execute(select(BrandProfile).where(BrandProfile.project_id == project_id))
        ).scalar_one_or_none()
        voice = (
            await session.execute(select(BrandVoice).where(BrandVoice.project_id == project_id))
        ).scalar_one_or_none()
        products_raw = list(
            (
                await session.execute(
                    select(BrandProductKnowledge).where(
                        BrandProductKnowledge.project_id == project_id
                    )
                )
            ).scalars().all()
        )
        audience = list(
            (
                await session.execute(
                    select(BrandAudienceInsight).where(
                        BrandAudienceInsight.project_id == project_id
                    )
                )
            ).scalars().all()
        )
        claims = list(
            (
                await session.execute(
                    select(BrandClaimRule).where(BrandClaimRule.project_id == project_id)
                )
            ).scalars().all()
        )
        seo = (
            await session.execute(
                select(BrandSeoStrategy).where(BrandSeoStrategy.project_id == project_id)
            )
        ).scalar_one_or_none()
        pillars = list(
            (
                await session.execute(
                    select(BrandContentPillar).where(
                        BrandContentPillar.project_id == project_id
                    )
                )
            ).scalars().all()
        )
        guardrails = list(
            (
                await session.execute(
                    select(BrandAiGuardrail).where(
                        BrandAiGuardrail.project_id == project_id
                    )
                )
            ).scalars().all()
        )
        assets = list(
            (
                await session.execute(
                    select(BrandAsset).where(BrandAsset.project_id == project_id)
                )
            ).scalars().all()
        )

        score = await compute_brand_knowledge_score(session, project_id)
        products = [p for p in products_raw if p.entity_type == "product"]
        categories = [p for p in products_raw if p.entity_type == "category"]

        return BrandContextBundleResponse(
            profile=BrandProfileRead.model_validate(profile) if profile else None,
            voice=BrandVoiceRead.model_validate(voice) if voice else None,
            products=[BrandProductKnowledgeRead.model_validate(p) for p in products],
            categories=[BrandProductKnowledgeRead.model_validate(c) for c in categories],
            audience=[BrandAudienceInsightRead.model_validate(a) for a in audience],
            claims=[BrandClaimRuleRead.model_validate(c) for c in claims],
            seo_strategy=BrandSeoStrategyRead.model_validate(seo) if seo else None,
            content_pillars=[BrandContentPillarRead.model_validate(p) for p in pillars],
            guardrails=[BrandAiGuardrailRead.model_validate(g) for g in guardrails],
            assets=[BrandAssetRead.model_validate(a) for a in assets],
            knowledge_score=BrandKnowledgeScoreResponse.model_validate(score_to_response(score)),
        )

    @staticmethod
    def format_for_prompt(bundle: BrandContextBundleResponse) -> str | None:
        """Compact text block for AI system prompts. Returns None if no meaningful data."""
        parts: list[str] = []

        if bundle.profile:
            p = bundle.profile
            if p.brand_name:
                parts.append(f"Brand: {p.brand_name}")
            if p.short_description:
                parts.append(f"Description: {p.short_description}")
            if p.industry:
                parts.append(f"Industry: {p.industry}")
            if p.values:
                parts.append(f"Values: {', '.join(p.values[:6])}")
            if p.differentiators:
                parts.append(f"Differentiators: {', '.join(p.differentiators[:5])}")

        if bundle.voice:
            v = bundle.voice
            if v.tone:
                parts.append(f"Tone: {v.tone}")
            if v.words_to_use:
                parts.append(f"Words to use: {', '.join(v.words_to_use[:10])}")
            if v.words_to_avoid:
                parts.append(f"Words to avoid: {', '.join(v.words_to_avoid[:10])}")
            if v.style_notes:
                parts.append(f"Style: {v.style_notes[:300]}")

        if bundle.products:
            names = [p.name for p in bundle.products[:5]]
            parts.append(f"Key products: {', '.join(names)}")

        if bundle.claims:
            forbidden = [c.title for c in bundle.claims if c.rule_type in ("forbidden", "caution")]
            if forbidden:
                parts.append(f"Claims caution/forbidden: {'; '.join(forbidden[:5])}")

        if bundle.guardrails:
            must_not = [g.title for g in bundle.guardrails if g.rule_type == "must_not"]
            if must_not:
                parts.append(f"AI must NOT: {'; '.join(must_not[:5])}")
            must = [g.title for g in bundle.guardrails if g.rule_type == "must"]
            if must:
                parts.append(f"AI must: {'; '.join(must[:5])}")

        if bundle.seo_strategy and bundle.seo_strategy.primary_keywords:
            parts.append(
                f"Primary keywords: {', '.join(bundle.seo_strategy.primary_keywords[:8])}"
            )

        if not parts:
            return None

        return "# Brand Intelligence\n" + "\n".join(f"- {line}" for line in parts)

    @staticmethod
    async def get_prompt_context(
        session: AsyncSession,
        project_id: UUID,
    ) -> str | None:
        """Load bundle and return prompt-ready text, or None for fallback."""
        bundle = await BrandIntelligenceContextBuilder.build_brand_context(session, project_id)
        if bundle.knowledge_score.overall_score < 10:
            return None
        return BrandIntelligenceContextBuilder.format_for_prompt(bundle)
