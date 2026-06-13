"""Brand Intelligence context builder.

v0.3.2: machine-ready promptContext + Profile, Identity, Visual.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brand_intelligence import BrandIdentity, BrandProfile, BrandVisualIdentity
from app.schemas.brand_identity_visual import BrandIdentityRead, BrandVisualIdentityRead
from app.schemas.brand_intelligence import (
    BrandContextBundleResponse,
    BrandKnowledgeScoreResponse,
    BrandProfileRead,
    BrandPromptContext,
)
from app.services.brand_intelligence.score import (
    compute_brand_knowledge_score,
    identity_missing_context,
    profile_has_minimum,
    profile_missing_context,
    score_to_response,
    visual_missing_context,
)


class BrandIntelligenceContextBuilder:
    """Central source of truth for brand context used by all AI modules."""

    @staticmethod
    async def build_brand_context(
        session: AsyncSession,
        project_id: UUID,
    ) -> BrandContextBundleResponse:
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

        score = await compute_brand_knowledge_score(session, project_id)
        missing = (
            profile_missing_context(profile)
            + identity_missing_context(identity)
            + visual_missing_context(visual)
        )

        primary_source = "brand_profile" if profile and profile_has_minimum(profile) else "minimal"

        profile_read = BrandProfileRead.model_validate(profile) if profile else None
        identity_read = BrandIdentityRead.model_validate(identity) if identity else None
        visual_read = BrandVisualIdentityRead.model_validate(visual) if visual else None

        bundle = BrandContextBundleResponse(
            brand_context_version="v1",
            primary_source=primary_source,
            missing_context=missing,
            approved_brief_id=None,
            brief_version=None,
            brand_brief=None,
            profile=profile_read,
            brand_identity=identity_read,
            visual_identity=visual_read,
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
        bundle.prompt_context = BrandIntelligenceContextBuilder.build_prompt_context(bundle)
        return bundle

    @staticmethod
    def format_profile_for_prompt(profile: BrandProfileRead) -> str:
        parts: list[str] = ["BRAND PROFILE"]
        if profile.brand_name:
            parts.append(f"- Nome: {profile.brand_name}")
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
        if profile.ai_summary:
            parts.append(f"- Sintesi: {profile.ai_summary[:600]}")
        return "\n".join(parts)

    @staticmethod
    def format_identity_for_prompt(identity: BrandIdentityRead) -> str:
        parts: list[str] = ["BRAND IDENTITY"]
        if identity.positioning:
            parts.append(f"- Posizionamento: {identity.positioning[:500]}")
        if identity.brand_values:
            parts.append(f"- Valori: {', '.join(identity.brand_values[:8])}")
        if identity.differentiators:
            parts.append(f"- Differenziatori: {', '.join(identity.differentiators[:6])}")
        if identity.production_principles:
            parts.append(
                f"- Principi produttivi: {', '.join(identity.production_principles[:5])}"
            )
        if identity.quality_principles:
            parts.append(
                f"- Principi di qualità: {', '.join(identity.quality_principles[:5])}"
            )
        if identity.trust_elements:
            parts.append(f"- Elementi di fiducia: {', '.join(identity.trust_elements[:5])}")
        if identity.what_brand_is:
            parts.append(f"- Il brand è: {identity.what_brand_is[:400]}")
        if identity.what_brand_is_not:
            parts.append(f"- Il brand NON è: {identity.what_brand_is_not[:400]}")
        if identity.storytelling_notes:
            parts.append(f"- Storytelling: {identity.storytelling_notes[:400]}")
        return "\n".join(parts)

    @staticmethod
    def format_visual_for_prompt(visual: BrandVisualIdentityRead) -> str:
        parts: list[str] = ["VISUAL IDENTITY"]
        if visual.primary_logo_url:
            parts.append(f"- Logo: {visual.primary_logo_url}")
        if visual.favicon_url:
            parts.append(f"- Favicon: {visual.favicon_url}")
        colors: list[str] = []
        if visual.primary_color:
            colors.append(f"primary {visual.primary_color}")
        if visual.secondary_color:
            colors.append(f"secondary {visual.secondary_color}")
        if visual.accent_color:
            colors.append(f"accent {visual.accent_color}")
        if visual.background_color:
            colors.append(f"background {visual.background_color}")
        if visual.text_color:
            colors.append(f"text {visual.text_color}")
        if colors:
            parts.append(f"- Colori principali: {', '.join(colors)}")
        if visual.fonts:
            font_names = [
                f.get("name", "") for f in visual.fonts if isinstance(f, dict) and f.get("name")
            ]
            if font_names:
                parts.append(f"- Font: {', '.join(font_names[:3])}")
        if visual.visual_style_notes:
            parts.append(f"- Stile visuale: {visual.visual_style_notes[:300]}")
        if visual.image_style_notes:
            parts.append(f"- Stile immagini: {visual.image_style_notes[:300]}")
        if visual.do_show:
            parts.append(f"- Mostrare: {', '.join(visual.do_show[:5])}")
        if visual.do_not_show:
            parts.append(f"- Evitare: {', '.join(visual.do_not_show[:5])}")
        return "\n".join(parts)

    @staticmethod
    def build_prompt_context(bundle: BrandContextBundleResponse) -> BrandPromptContext | None:
        if bundle.primary_source == "minimal" or not bundle.profile:
            return None

        profile_text = BrandIntelligenceContextBuilder.format_profile_for_prompt(bundle.profile)
        identity_text = (
            BrandIntelligenceContextBuilder.format_identity_for_prompt(bundle.brand_identity)
            if bundle.brand_identity
            else None
        )
        visual_text = (
            BrandIntelligenceContextBuilder.format_visual_for_prompt(bundle.visual_identity)
            if bundle.visual_identity
            else None
        )

        blocks = [profile_text]
        if identity_text and len(identity_text.splitlines()) > 1:
            blocks.append(identity_text)
        if visual_text and len(visual_text.splitlines()) > 1:
            blocks.append(visual_text)

        full_text = "\n\n".join(blocks)
        return BrandPromptContext(
            brand_profile=profile_text,
            brand_identity=identity_text,
            visual_identity=visual_text,
            full_text=full_text,
        )

    @staticmethod
    def format_for_prompt(bundle: BrandContextBundleResponse) -> str | None:
        if bundle.prompt_context and bundle.prompt_context.full_text:
            return bundle.prompt_context.full_text
        if bundle.primary_source == "minimal" or not bundle.profile:
            return None
        blocks: list[str] = [BrandIntelligenceContextBuilder.format_profile_for_prompt(bundle.profile)]
        if bundle.brand_identity:
            blocks.append(
                BrandIntelligenceContextBuilder.format_identity_for_prompt(bundle.brand_identity)
            )
        if bundle.visual_identity:
            blocks.append(
                BrandIntelligenceContextBuilder.format_visual_for_prompt(bundle.visual_identity)
            )
        return "\n\n".join(blocks)

    @staticmethod
    async def get_prompt_context(
        session: AsyncSession,
        project_id: UUID,
    ) -> str | None:
        bundle = await BrandIntelligenceContextBuilder.build_brand_context(session, project_id)
        if bundle.primary_source == "minimal":
            return None
        return BrandIntelligenceContextBuilder.format_for_prompt(bundle)
