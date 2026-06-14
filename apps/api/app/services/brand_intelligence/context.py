"""Brand Intelligence context builder.

v0.3.2: machine-ready promptContext + Profile, Identity, Visual.
v0.3.5: previewText human-friendly per AI Context Preview UI.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brand_intelligence import (
    BrandFaqObjections,
    BrandIdentity,
    BrandProductKnowledgeGeneral,
    BrandProductKnowledgeItem,
    BrandProfile,
    BrandSafeClaims,
    BrandVisualIdentity,
)
from app.schemas.brand_faq_objections import BrandFaqObjectionsRead
from app.schemas.brand_identity_visual import BrandIdentityRead, BrandVisualIdentityRead
from app.schemas.brand_safe_claims import BrandSafeClaimsRead
from app.schemas.brand_intelligence import (
    BrandContextBundleResponse,
    BrandKnowledgeScoreResponse,
    BrandProfileRead,
    BrandPromptContext,
)
from app.services.brand_intelligence.product_knowledge_context import (
    build_product_knowledge_context,
    format_product_knowledge_preview,
)
from app.services.brand_intelligence.product_knowledge_general_service import general_has_content
from app.services.brand_intelligence.faq_objections_normalize import normalize_to_string_list
from app.services.brand_intelligence.faq_objections_service import (
    faq_objections_completion,
    faq_objections_missing_context,
)
from app.services.brand_intelligence.safe_claims_service import safe_claims_completion
from app.services.brand_intelligence.score import (
    compute_brand_knowledge_score,
    identity_missing_context,
    profile_has_minimum,
    profile_missing_context,
    safe_claims_missing_context,
    score_to_response,
    visual_missing_context,
)

SAFE_CLAIMS_PRUDENCE_FALLBACK = """SAFE CLAIMS & RED FLAGS (fallback prudenza)
- Non usare claim medici, terapeutici o promesse di cura non verificabili.
- Non attaccare competitor o fare confronti denigratori.
- Non divulgare process secrets o dettagli produttivi riservati.
- Preferire claim fattuali, verificabili e conformi al brand."""

_EMPTY_SECTION_LABEL = "Sezione non compilata."


class BrandIntelligenceContextBuilder:
    """Central source of truth for brand context used by all AI modules.

    Tutti i moduli AI brand-facing devono usare BrandIntelligenceContextBuilder
    e non leggere direttamente le tabelle Brand Intelligence.
    """

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
                    select(BrandProductKnowledgeItem)
                    .where(BrandProductKnowledgeItem.project_id == project_id)
                    .order_by(BrandProductKnowledgeItem.product_name.asc())
                )
            ).scalars().all()
        )
        faq_objections = (
            await session.execute(
                select(BrandFaqObjections).where(BrandFaqObjections.project_id == project_id)
            )
        ).scalar_one_or_none()

        score = await compute_brand_knowledge_score(session, project_id)
        missing = (
            profile_missing_context(profile)
            + identity_missing_context(identity)
            + visual_missing_context(visual)
            + safe_claims_missing_context(safe_claims)
            + faq_objections_missing_context(
                BrandFaqObjectionsRead.model_validate(faq_objections)
                if faq_objections
                else None
            )
        )
        if safe_claims_completion(safe_claims) == "empty":
            missing.append(
                "Safe Claims non compilata: i moduli AI devono evitare claim sensibili."
            )
        if not general_has_content(pk_general) and not pk_items:
            missing.append(
                "Product Knowledge non compilata: i moduli AI useranno solo dati Shopify."
            )

        primary_source = "brand_profile" if profile and profile_has_minimum(profile) else "minimal"

        profile_read = BrandProfileRead.model_validate(profile) if profile else None
        identity_read = BrandIdentityRead.model_validate(identity) if identity else None
        visual_read = BrandVisualIdentityRead.model_validate(visual) if visual else None
        safe_claims_read = (
            BrandSafeClaimsRead.model_validate(safe_claims) if safe_claims else None
        )
        faq_objections_read = (
            BrandFaqObjectionsRead.model_validate(faq_objections) if faq_objections else None
        )
        pk_context = build_product_knowledge_context(pk_general, pk_items)

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
            safe_claims=safe_claims_read,
            faq_objections=faq_objections_read,
            product_knowledge=pk_context,
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
    def format_safe_claims_for_prompt(safe_claims: BrandSafeClaimsRead) -> str:
        parts: list[str] = ["SAFE CLAIMS & RED FLAGS"]
        if safe_claims.allowed_claims:
            parts.append("Claim consentiti:")
            parts.extend(f"- {c}" for c in safe_claims.allowed_claims[:12])
        if safe_claims.forbidden_claims:
            parts.append("Claim vietati:")
            parts.extend(f"- {c}" for c in safe_claims.forbidden_claims[:12])
        if safe_claims.caution_claims:
            parts.append("Da usare con cautela:")
            parts.extend(f"- {c}" for c in safe_claims.caution_claims[:10])
        if safe_claims.disclaimers:
            parts.append("Disclaimer:")
            parts.extend(f"- {d}" for d in safe_claims.disclaimers[:8])
        if safe_claims.health_claim_rules:
            parts.append("Regole claim salutistici:")
            parts.extend(f"- {r}" for r in safe_claims.health_claim_rules[:8])
        if safe_claims.competitor_rules:
            parts.append("Regole competitor:")
            parts.extend(f"- {r}" for r in safe_claims.competitor_rules[:8])
        if safe_claims.process_secrets:
            parts.append("Process secrets (non divulgare):")
            parts.extend(f"- {s}" for s in safe_claims.process_secrets[:8])
        if safe_claims.tone_red_flags:
            parts.append("Tone red flags:")
            parts.extend(f"- {f}" for f in safe_claims.tone_red_flags[:8])
        if safe_claims.notes:
            parts.append(f"Note: {safe_claims.notes[:400]}")
        return "\n".join(parts)

    @staticmethod
    def _section_has_content(text: str | None) -> bool:
        return bool(text and len(text.splitlines()) > 1)

    @staticmethod
    def _normalized_strings(value: object | None) -> list[str]:
        return normalize_to_string_list(value)

    @staticmethod
    def _format_string_list(label: str, items: object | None) -> list[str]:
        normalized = BrandIntelligenceContextBuilder._normalized_strings(items)
        if not normalized:
            return []
        lines = [f"{label}:"]
        for text in normalized:
            if text:
                lines.append(f"- {text}")
        return lines if len(lines) > 1 else []

    @staticmethod
    def format_faq_objections_for_prompt(row: BrandFaqObjectionsRead) -> str | None:
        if faq_objections_completion(row) == "empty":
            return None
        parts: list[str] = ["FAQ & OBJECTIONS"]
        parts.extend(
            BrandIntelligenceContextBuilder._format_string_list(
                "FAQ generali", row.general_faq
            )
        )
        parts.extend(
            BrandIntelligenceContextBuilder._format_string_list(
                "Domande prodotto/processo", row.product_process_questions
            )
        )
        parts.extend(
            BrandIntelligenceContextBuilder._format_string_list(
                "Domande acquisto/spedizione", row.purchase_shipping_questions
            )
        )
        objections = BrandIntelligenceContextBuilder._normalized_strings(row.objections)
        if objections:
            parts.append("Obiezioni frequenti:")
            parts.extend(f"- {o}" for o in objections[:20])
        myths = BrandIntelligenceContextBuilder._normalized_strings(row.myths_misconceptions)
        if myths:
            parts.append("Falsi miti:")
            parts.extend(f"- {m}" for m in myths[:20])
        recommended = BrandIntelligenceContextBuilder._normalized_strings(row.recommended_answers)
        if recommended:
            parts.append("Risposte consigliate:")
            parts.extend(f"- {r}" for r in recommended[:20])
        opportunities = BrandIntelligenceContextBuilder._normalized_strings(row.content_opportunities)
        if opportunities:
            parts.append("Opportunità contenuto:")
            parts.extend(f"- {c}" for c in opportunities[:15])
        social = BrandIntelligenceContextBuilder._normalized_strings(row.social_comment_insights)
        if social:
            parts.append("Insight commenti social:")
            parts.extend(f"- {s}" for s in social[:15])
        if row.notes:
            parts.append(f"Note: {row.notes[:400]}")
        return "\n".join(parts) if len(parts) > 1 else None

    @staticmethod
    def build_prompt_preview_text(bundle: BrandContextBundleResponse) -> str | None:
        if bundle.primary_source == "minimal" or not bundle.profile:
            return None

        blocks: list[str] = []

        profile_text = BrandIntelligenceContextBuilder.format_profile_for_prompt(bundle.profile)
        blocks.append(
            profile_text
            if BrandIntelligenceContextBuilder._section_has_content(profile_text)
            else f"BRAND PROFILE\n{_EMPTY_SECTION_LABEL}"
        )

        if bundle.brand_identity:
            identity_text = BrandIntelligenceContextBuilder.format_identity_for_prompt(
                bundle.brand_identity
            )
            blocks.append(
                identity_text
                if BrandIntelligenceContextBuilder._section_has_content(identity_text)
                else f"BRAND IDENTITY\n{_EMPTY_SECTION_LABEL}"
            )
        else:
            blocks.append(f"BRAND IDENTITY\n{_EMPTY_SECTION_LABEL}")

        if bundle.visual_identity:
            visual_text = BrandIntelligenceContextBuilder.format_visual_for_prompt(
                bundle.visual_identity
            )
            blocks.append(
                visual_text
                if BrandIntelligenceContextBuilder._section_has_content(visual_text)
                else f"VISUAL IDENTITY\n{_EMPTY_SECTION_LABEL}"
            )
        else:
            blocks.append(f"VISUAL IDENTITY\n{_EMPTY_SECTION_LABEL}")

        if bundle.safe_claims and safe_claims_completion(bundle.safe_claims) != "empty":
            blocks.append(
                BrandIntelligenceContextBuilder.format_safe_claims_for_prompt(bundle.safe_claims)
            )
        else:
            blocks.append(SAFE_CLAIMS_PRUDENCE_FALLBACK)

        if bundle.product_knowledge:
            pk_preview = format_product_knowledge_preview(bundle.product_knowledge)
            blocks.append(
                pk_preview if pk_preview else f"PRODUCT KNOWLEDGE\n{_EMPTY_SECTION_LABEL}"
            )
        else:
            blocks.append(f"PRODUCT KNOWLEDGE\n{_EMPTY_SECTION_LABEL}")

        if bundle.faq_objections:
            faq_text = BrandIntelligenceContextBuilder.format_faq_objections_for_prompt(
                bundle.faq_objections
            )
            blocks.append(
                faq_text if faq_text else f"FAQ & OBJECTIONS\n{_EMPTY_SECTION_LABEL}"
            )
        else:
            blocks.append(f"FAQ & OBJECTIONS\n{_EMPTY_SECTION_LABEL}")

        if bundle.missing_context:
            missing_parts = ["MISSING CONTEXT", *[f"- {m}" for m in bundle.missing_context]]
            blocks.append("\n".join(missing_parts))

        return "\n\n".join(blocks)

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
        safe_claims_text = None
        if bundle.safe_claims and safe_claims_completion(bundle.safe_claims) != "empty":
            safe_claims_text = BrandIntelligenceContextBuilder.format_safe_claims_for_prompt(
                bundle.safe_claims
            )
        else:
            safe_claims_text = SAFE_CLAIMS_PRUDENCE_FALLBACK

        product_knowledge_text = None
        if bundle.product_knowledge:
            pk_blocks: list[str] = []
            rules = bundle.product_knowledge.general_rules
            if rules and (
                rules.general_principles
                or rules.common_strengths
                or rules.quality_rules
                or rules.production_notes
                or rules.usage_notes
                or rules.common_objections
                or rules.common_faq
                or rules.communication_rules
                or rules.storytelling_rules
            ):
                general_parts = ["PRODUCT KNOWLEDGE — GENERAL"]
                if rules.general_principles:
                    general_parts.append("Principi generali:")
                    general_parts.extend(f"- {p}" for p in rules.general_principles[:10])
                if rules.common_strengths:
                    general_parts.append("Punti di forza comuni:")
                    general_parts.extend(f"- {s}" for s in rules.common_strengths[:8])
                if rules.quality_rules:
                    general_parts.append("Regole qualità:")
                    general_parts.extend(f"- {r}" for r in rules.quality_rules[:8])
                if rules.common_objections:
                    general_parts.append("Obiezioni comuni:")
                    general_parts.extend(f"- {o}" for o in rules.common_objections[:6])
                if len(general_parts) > 1:
                    pk_blocks.append("\n".join(general_parts))
            if bundle.product_knowledge.specific_products:
                specific_parts = ["PRODUCT KNOWLEDGE — SPECIFIC PRODUCTS"]
                for sp in bundle.product_knowledge.specific_products[:15]:
                    title = sp.title or "Prodotto"
                    lines = [f"Prodotto: {title}"]
                    if sp.handle:
                        lines.append(f"- Handle: {sp.handle}")
                    if sp.strategic_description:
                        lines.append(f"- Descrizione: {sp.strategic_description[:400]}")
                    if sp.ingredients:
                        lines.append(f"- Ingredienti: {sp.ingredients[:300]}")
                    if sp.allowed_claims:
                        lines.append(f"- Claim consentiti: {', '.join(sp.allowed_claims[:6])}")
                    if len(lines) > 1:
                        specific_parts.append("\n".join(lines))
                if len(specific_parts) > 1:
                    pk_blocks.append("\n\n".join(specific_parts))
            if pk_blocks:
                product_knowledge_text = "\n\n".join(pk_blocks)

        faq_objections_text = None
        if bundle.faq_objections:
            faq_objections_text = BrandIntelligenceContextBuilder.format_faq_objections_for_prompt(
                bundle.faq_objections
            )

        blocks = [profile_text]
        if identity_text and len(identity_text.splitlines()) > 1:
            blocks.append(identity_text)
        if visual_text and len(visual_text.splitlines()) > 1:
            blocks.append(visual_text)
        if safe_claims_text:
            blocks.append(safe_claims_text)
        if product_knowledge_text:
            blocks.append(product_knowledge_text)
        if faq_objections_text:
            blocks.append(faq_objections_text)

        full_text = "\n\n".join(blocks)
        preview_text = BrandIntelligenceContextBuilder.build_prompt_preview_text(bundle)
        return BrandPromptContext(
            brand_profile=profile_text,
            brand_identity=identity_text,
            visual_identity=visual_text,
            safe_claims=safe_claims_text,
            product_knowledge=product_knowledge_text,
            faq_objections=faq_objections_text,
            full_text=full_text,
            preview_text=preview_text,
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
        if bundle.safe_claims and safe_claims_completion(bundle.safe_claims) != "empty":
            blocks.append(
                BrandIntelligenceContextBuilder.format_safe_claims_for_prompt(bundle.safe_claims)
            )
        elif bundle.prompt_context and bundle.prompt_context.safe_claims:
            blocks.append(bundle.prompt_context.safe_claims)
        if bundle.prompt_context and bundle.prompt_context.product_knowledge:
            blocks.append(bundle.prompt_context.product_knowledge)
        if bundle.faq_objections:
            faq_text = BrandIntelligenceContextBuilder.format_faq_objections_for_prompt(
                bundle.faq_objections
            )
            if faq_text:
                blocks.append(faq_text)
        elif bundle.prompt_context and bundle.prompt_context.faq_objections:
            blocks.append(bundle.prompt_context.faq_objections)
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
