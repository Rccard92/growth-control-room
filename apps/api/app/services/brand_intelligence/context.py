"""
Brand Intelligence context builder.

Any AI module that generates brand-facing content must call
BrandIntelligenceContextBuilder before generating output.
"""

from __future__ import annotations

from typing import Any
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
from app.services.brand_intelligence.brief_service import get_approved_brief
from app.services.brand_intelligence.score import compute_brand_knowledge_score, score_to_response


def _as_str_list(items: list[Any], limit: int = 8) -> str:
    out: list[str] = []
    for item in items[:limit]:
        if isinstance(item, str):
            out.append(item)
        elif isinstance(item, dict):
            for key in ("name", "title", "label", "text", "segment"):
                if item.get(key):
                    out.append(str(item[key]))
                    break
            else:
                out.append(str(item))
        else:
            out.append(str(item))
    return ", ".join(out)


class BrandIntelligenceContextBuilder:
    """
    Central source of truth for brand context used by all AI modules.

    Priority: approved Brand Intelligence Brief > structured CRUD tables > minimal.
    """

    @staticmethod
    async def build_brand_context(
        session: AsyncSession,
        project_id: UUID,
    ) -> BrandContextBundleResponse:
        approved_brief = await get_approved_brief(session, project_id)

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

        has_structured = bool(
            profile
            or voice
            or products
            or audience
            or claims
            or seo
            or pillars
            or guardrails
        )

        if approved_brief:
            primary_source = "brand_intelligence_brief"
        elif has_structured:
            primary_source = "structured_tables"
        else:
            primary_source = "minimal"

        return BrandContextBundleResponse(
            primary_source=primary_source,
            approved_brief_id=approved_brief.id if approved_brief else None,
            brief_version=approved_brief.version if approved_brief else None,
            brand_brief=approved_brief.brief_payload if approved_brief else None,
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
    def format_brief_for_prompt(brief_payload: dict[str, Any]) -> str:
        parts: list[str] = ["# Brand Intelligence Brief"]

        identity = brief_payload.get("brand_identity") or {}
        if identity.get("brand_name"):
            parts.append(f"- Brand: {identity['brand_name']}")
        if identity.get("short_description"):
            parts.append(f"- Description: {identity['short_description']}")
        if identity.get("mission"):
            parts.append(f"- Mission: {identity['mission']}")
        values = identity.get("values") or []
        if values:
            parts.append(f"- Values: {_as_str_list(values)}")

        voice = brief_payload.get("voice_and_tone") or {}
        if voice.get("tone"):
            parts.append(f"- Tone: {voice['tone']}")
        if voice.get("words_to_use"):
            parts.append(f"- Words to use: {_as_str_list(voice['words_to_use'], 10)}")
        if voice.get("words_to_avoid"):
            parts.append(f"- Words to avoid: {_as_str_list(voice['words_to_avoid'], 10)}")

        products = brief_payload.get("products_and_categories") or []
        if products:
            parts.append(f"- Products: {_as_str_list(products, 5)}")

        claims = brief_payload.get("claims_compliance") or {}
        forbidden = claims.get("forbidden_claims") or []
        caution = claims.get("caution_claims") or []
        if forbidden or caution:
            parts.append(
                f"- Claims caution/forbidden: {_as_str_list(list(forbidden) + list(caution), 6)}"
            )

        guardrails = brief_payload.get("ai_guardrails") or {}
        must_not = guardrails.get("must_not") or []
        if must_not:
            parts.append(f"- AI must NOT: {_as_str_list(must_not, 5)}")

        seo = brief_payload.get("seo_guidelines") or {}
        keywords = seo.get("primary_keywords") or []
        if keywords:
            parts.append(f"- Primary keywords: {_as_str_list(keywords, 8)}")

        missing = brief_payload.get("missing_information") or []
        if missing:
            parts.append(f"- Missing information (verify): {_as_str_list(missing, 5)}")

        return "\n".join(parts)

    @staticmethod
    def format_structured_for_prompt(bundle: BrandContextBundleResponse) -> str | None:
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

        return "## Structured data (secondary)\n" + "\n".join(f"- {line}" for line in parts)

    @staticmethod
    def format_for_prompt(bundle: BrandContextBundleResponse) -> str | None:
        """Compact text block for AI system prompts."""
        if bundle.primary_source == "brand_intelligence_brief" and bundle.brand_brief:
            main = BrandIntelligenceContextBuilder.format_brief_for_prompt(bundle.brand_brief)
            secondary = BrandIntelligenceContextBuilder.format_structured_for_prompt(bundle)
            if secondary:
                return main + "\n\n" + secondary
            return main

        structured = BrandIntelligenceContextBuilder.format_structured_for_prompt(bundle)
        if structured:
            return "# Brand Intelligence\n" + structured.replace("## Structured data (secondary)\n", "")
        return None

    @staticmethod
    async def get_prompt_context(
        session: AsyncSession,
        project_id: UUID,
    ) -> str | None:
        bundle = await BrandIntelligenceContextBuilder.build_brand_context(session, project_id)
        if bundle.primary_source == "minimal" and bundle.knowledge_score.overall_score < 10:
            return None
        return BrandIntelligenceContextBuilder.format_for_prompt(bundle)
