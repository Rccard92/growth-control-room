"""
Brand Intelligence context builder.

Any AI module that generates brand-facing content must call
BrandIntelligenceContextBuilder before generating output.

v0.3.0: primary source is official Brand Profile v1 only.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brand_intelligence import BrandProfile
from app.schemas.brand_intelligence import (
    BrandContextBundleResponse,
    BrandKnowledgeScoreResponse,
    BrandProfileRead,
)
from app.services.brand_intelligence.score import (
    compute_brand_knowledge_score,
    profile_has_minimum,
    profile_missing_context,
    score_to_response,
)


class BrandIntelligenceContextBuilder:
    """
    Central source of truth for brand context used by all AI modules.

    Priority: official Brand Profile v1 > minimal fallback.
    """

    @staticmethod
    async def build_brand_context(
        session: AsyncSession,
        project_id: UUID,
    ) -> BrandContextBundleResponse:
        profile = (
            await session.execute(select(BrandProfile).where(BrandProfile.project_id == project_id))
        ).scalar_one_or_none()

        score = await compute_brand_knowledge_score(session, project_id)
        missing = profile_missing_context(profile)

        if profile and profile_has_minimum(profile):
            primary_source = "brand_profile"
        else:
            primary_source = "minimal"

        return BrandContextBundleResponse(
            primary_source=primary_source,
            missing_context=missing,
            approved_brief_id=None,
            brief_version=None,
            brand_brief=None,
            profile=BrandProfileRead.model_validate(profile) if profile else None,
            voice=None,
            products=[],
            categories=[],
            audience=[],
            claims=[],
            seo_strategy=None,
            content_pillars=[],
            guardrails=[],
            assets=[],
            knowledge_score=BrandKnowledgeScoreResponse.model_validate(score_to_response(score)),
        )

    @staticmethod
    def format_profile_for_prompt(profile: BrandProfileRead) -> str:
        parts: list[str] = ["# Brand Profile"]

        if profile.brand_name:
            parts.append(f"- Brand: {profile.brand_name}")
        if profile.website_url:
            parts.append(f"- Sito: {profile.website_url}")
        if profile.short_description:
            parts.append(f"- Descrizione: {profile.short_description}")
        if profile.story:
            parts.append(f"- Storia: {profile.story[:800]}")
        if profile.mission:
            parts.append(f"- Missione: {profile.mission[:500]}")
        if profile.values:
            parts.append(f"- Valori: {', '.join(profile.values[:8])}")
        if profile.differentiators:
            parts.append(f"- Differenziatori: {', '.join(profile.differentiators[:6])}")
        if profile.origin_notes:
            parts.append(f"- Origine: {profile.origin_notes[:400]}")
        if profile.production_notes:
            parts.append(f"- Produzione: {profile.production_notes[:400]}")
        if profile.tone_notes:
            parts.append(f"- Tono: {profile.tone_notes[:400]}")
        if profile.customer_notes:
            parts.append(f"- Clienti: {profile.customer_notes[:400]}")
        if profile.ai_summary:
            parts.append(f"- Sintesi: {profile.ai_summary[:600]}")

        return "\n".join(parts)

    @staticmethod
    def format_for_prompt(bundle: BrandContextBundleResponse) -> str | None:
        """Compact text block for AI system prompts."""
        if bundle.primary_source == "brand_profile" and bundle.profile:
            return BrandIntelligenceContextBuilder.format_profile_for_prompt(bundle.profile)
        return None

    @staticmethod
    async def get_prompt_context(
        session: AsyncSession,
        project_id: UUID,
    ) -> str | None:
        bundle = await BrandIntelligenceContextBuilder.build_brand_context(session, project_id)
        if bundle.primary_source == "minimal":
            return None
        return BrandIntelligenceContextBuilder.format_for_prompt(bundle)
