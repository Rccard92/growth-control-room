"""AI Brief Generator for Content SEO editorial items.

Uses BrandIntelligenceContextBuilder + Safe Claims. Does not generate full articles.
"""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_seo_editorial import ContentSeoEditorialItem
from app.schemas.brand_intelligence import BrandContextBundleResponse
from app.schemas.content_seo_editorial import (
    EditorialBriefPayload,
    EditorialBriefUpdateRequest,
    normalize_editorial_brief_payload,
)
from app.services.ai.openai_client import (
    AiRequestMetadata,
    OpenAINotConfiguredError,
    OpenAIRequestError,
    generate_structured_json,
    is_openai_configured,
)
from app.services.ai.context_profiles import (
    AiContextProfile,
    build_context_for_profile,
    build_prompt_cache_key,
    enrich_ai_metadata,
)
from app.services.brand_intelligence.context import BrandIntelligenceContextBuilder
from app.services.brand_intelligence.faq_objections_service import faq_objections_completion
from app.services.brand_intelligence.editorial_guidelines_service import (
    editorial_guidelines_completion,
)
from app.services.brand_intelligence.identity_service import identity_has_minimum
from app.services.brand_intelligence.product_knowledge_context import (
    get_product_knowledge_prompt_for_entity,
)
from app.services.brand_intelligence.safe_claims_service import safe_claims_has_minimum
from app.services.brand_intelligence.score import profile_has_minimum
from app.services.content.editorial_item_service import get_editorial_item
from app.services.content.editorial_structure_profiles import (
    default_avoid_repetitions,
    resolve_structure_profile,
)
from app.services.content.editorial_structure_utils import count_h2_h3, trim_structure
from app.services.content.seo_skill_loader import load_seo_skill_context

logger = logging.getLogger(__name__)


class BriefGenerationError(Exception):
    """Domain error for brief generation (batch-safe, no HTTP)."""

    def __init__(self, message: str, *, ai_not_configured: bool = False) -> None:
        super().__init__(message)
        self.ai_not_configured = ai_not_configured

_CONTENT_TYPE_INSTRUCTIONS: dict[str, str] = {
    "educational_article": (
        "Articolo educativo: rispondi a un dubbio reale del cliente con struttura snella. "
        "Max 4-5 H2, H3 opzionali (max 2-3 totali), target 700-950 parole. "
        "No struttura enciclopedica. E-E-A-T senza claim non verificati."
    ),
    "product_guide": (
        "Guida prodotto: focus su gusto, uso, conservazione e scelta. "
        "Max 5 H2, target 800-1100 parole. CTA soft verso acquisto."
    ),
    "recipe": (
        "Ricetta: struttura pratica (ingredienti, procedimento, consigli, abbinamento). "
        "Max 4 H2, target 600-900 parole. FAQ opzionali max 2."
    ),
    "faq_objection_article": (
        "Articolo FAQ/obiezioni: risposta concreta a un dubbio, struttura compatta. "
        "Max 4-5 H2, FAQ max 3-4 solo se aggiungono valore, target 700-950 parole."
    ),
    "product_comparison": (
        "Confronto prodotti: solo se il tema lo richiede davvero. "
        "Max 6 H2 e 5 H3, target 1000-1300 parole. Evita attacchi a competitor."
    ),
    "seasonal_article": (
        "Articolo stagionale: angolo legato al periodo, struttura proporzionata. "
        "Max 6 H2 se necessario, target 1000-1300 parole."
    ),
    "brand_storytelling": (
        "Storytelling brand: meno H2, più racconto. Max 3-4 H2, target 700-1000 parole. "
        "Emotivo ma fedele al Brand Identity, zero claim inventati."
    ),
}

_BRIEF_STRUCTURE_RULES = """
REGOLE STRUTTURA BRIEF (obbligatorie):
- Obiettivo editoriale: contenuti utili, leggibili, morbidi e concreti — NON guide SEO enciclopediche.
- Struttura H2/H3 proporzionata al tipo contenuto e al dubbio del cliente.
- Per dubbi semplici / educational / FAQ: max 4-5 H2, H3 opzionali (max 2-3 totali), NON mettere H3 sotto ogni H2.
- Per temi complessi: max 5-6 H2 e max 4-5 H3 solo se davvero necessario.
- h2H3Structure: array di oggetti { "h2": "titolo sezione", "h3": ["sottosezione opzionale"] } — compatto.
- Evita sezioni "In sintesi" lunghe se ci sono già FAQ; evita H3 che ripetono il titolo H2.
- Evita sezioni tecniche inutili e doppioni tra H2, sintesi e FAQ.
- faqToInclude: max 3-4, solo se aggiungono valore; non ripetere risposte già nel corpo.
- Compila recommendedWordCountMin, recommendedWordCountMax, structureComplexity (snella|media|approfondita),
  maxH2, maxH3, avoidRepetitions coerenti con il tipo contenuto.
"""

_BRIEF_JSON_SCHEMA = """{
  "proposedTitle": "string",
  "searchIntent": "string",
  "targetAudience": "string",
  "primaryKeyword": "string",
  "secondaryKeywords": ["string"],
  "contentAngle": "string",
  "h2H3Structure": [{"h2": "titolo sezione", "h3": ["sottosezione opzionale"]}],
  "productsToLink": ["string"],
  "faqToInclude": ["string"],
  "claimsToAvoid": ["string"],
  "safeClaimsToUse": ["string"],
  "recommendedCta": "string",
  "metaTitle": "string",
  "metaDescription": "string",
  "internalLinksSuggestions": ["string"],
  "notes": "string",
  "authorSuggestion": "",
  "authorReason": "string",
  "contentLengthProfile": "breve|medio|approfondito",
  "communityCtaSuggestion": "string",
  "editorialToneNotes": ["string"],
  "recommendedWordCountMin": 700,
  "recommendedWordCountMax": 950,
  "structureComplexity": "snella|media|approfondita",
  "maxH2": 5,
  "maxH3": 3,
  "avoidRepetitions": ["string"],
  "warnings": ["string"]
}"""

_COMPLEXITY_TO_LENGTH = {
    "snella": "breve",
    "media": "medio",
    "approfondita": "approfondito",
}


def enforce_brief_structure(
    payload: EditorialBriefPayload,
    content_type: str,
    title: str,
) -> EditorialBriefPayload:
    """Apply content-type structure limits and fill editorial metadata fields."""
    profile = resolve_structure_profile(content_type, title)
    warnings = list(payload.warnings)

    h2_before, h3_before = count_h2_h3(payload.h2_h3_structure)
    trimmed_structure, structure_trimmed = trim_structure(
        payload.h2_h3_structure,
        max_h2=profile.max_h2,
        max_h3=profile.max_h3,
    )
    if structure_trimmed:
        h2_after, h3_after = count_h2_h3(trimmed_structure)
        warnings.append(
            f"Struttura H2/H3 compattata ({h2_before}→{h2_after} H2, {h3_before}→{h3_after} H3)"
        )

    faq = list(payload.faq_to_include)
    if len(faq) > profile.max_faq:
        faq = faq[: profile.max_faq]
        warnings.append(f"FAQ ridotte a {profile.max_faq} per mantenere il brief snello")

    avoid = list(payload.avoid_repetitions) or default_avoid_repetitions(
        content_type, payload.primary_keyword
    )
    length_profile = (payload.content_length_profile or "").strip()
    if length_profile not in ("breve", "medio", "approfondito"):
        length_profile = _COMPLEXITY_TO_LENGTH.get(profile.structure_complexity, "medio")

    return payload.model_copy(
        update={
            "h2_h3_structure": trimmed_structure,
            "faq_to_include": faq,
            "recommended_word_count_min": profile.word_min,
            "recommended_word_count_max": profile.word_max,
            "structure_complexity": profile.structure_complexity,
            "max_h2": profile.max_h2,
            "max_h3": profile.max_h3,
            "avoid_repetitions": avoid,
            "content_length_profile": length_profile,
            "warnings": list(dict.fromkeys(warnings)),
        }
    )


_BRIEF_EDITORIAL_RULES = """
REGOLE EDITORIALI (dal contesto EDITORIAL GUIDELINES — obbligatorie):
- Usa filosofia contenuti, persone del brand, tono e lunghezza dalle Editorial Guidelines.
- La firma autore è OPZIONALE: non forzare sempre Davide, Filippo o Salvo.
- authorSuggestion può essere solo: "" (nessuna firma), "Davide", "Filippo Leonardi", "Salvo Leonardi".
- Davide: produzione, lavorazione, processi, qualità, dietro le quinte.
- Filippo Leonardi: apicoltura, territorio, esperienza aziendale, racconto autorevole.
- Salvo Leonardi: continuità familiare, tono community/giovane e familiare.
- Nessuna firma (authorSuggestion ""): guide generiche, ricette semplici, contenuti informativi SEO dove la firma sarebbe forzata.
- Se suggerisci un autore, motiva in authorReason in modo concreto.
- Se nessuna firma, spiega in authorReason (es. contenuto informativo generico).
- communityCtaSuggestion: CTA community morbida, distinta da recommendedCta (commerciale).
- contentLengthProfile: breve|medio|approfondito coerente con guidelines e tipo contenuto.
- editorialToneNotes: note operative sul tono per il redattore.
- Safe Claims restano prioritari assoluti.
"""


def _safe_claims_guardrail_suffix(brand_context: str | None) -> str:
    if not brand_context:
        return ""
    if "SAFE CLAIMS" in brand_context.upper():
        return (
            "\n\nREGOLE SAFE CLAIMS (priorità massima): non usare claim vietati; "
            "evitare claim medici/terapeutici; non attaccare competitor; "
            "non divulgare process secrets."
        )
    return ""


def build_bi_warnings(bundle: BrandContextBundleResponse) -> list[str]:
    warnings: list[str] = []
    if not identity_has_minimum(bundle.brand_identity):
        warnings.append("Brand Identity mancante")
    if not safe_claims_has_minimum(bundle.safe_claims):
        warnings.append("Safe Claims mancanti")
    if not bundle.product_knowledge:
        warnings.append("Product Knowledge mancante")
    if faq_objections_completion(bundle.faq_objections) == "empty":
        warnings.append("FAQ & Objections mancanti")
    editorial_guidelines = getattr(bundle, "editorial_guidelines", None)
    if editorial_guidelines_completion(editorial_guidelines) == "empty":
        warnings.append("Editorial Guidelines mancanti")
    return warnings


def build_brand_context_used(
    bundle: BrandContextBundleResponse,
    *,
    product_pk_appended: bool,
) -> list[str]:
    used: list[str] = []
    if bundle.profile and profile_has_minimum(bundle.profile):
        used.append("Brand Profile")
    if identity_has_minimum(bundle.brand_identity):
        used.append("Brand Identity")
    if bundle.safe_claims and safe_claims_has_minimum(bundle.safe_claims):
        used.append("Safe Claims")
    elif bundle.prompt_context and bundle.prompt_context.safe_claims:
        used.append("Safe Claims")
    if bundle.product_knowledge or product_pk_appended:
        used.append("Product Knowledge")
    if bundle.faq_objections and faq_objections_completion(bundle.faq_objections) != "empty":
        used.append("FAQ & Objections")
    editorial_guidelines = getattr(bundle, "editorial_guidelines", None)
    if (
        editorial_guidelines
        and editorial_guidelines_completion(editorial_guidelines) != "empty"
    ):
        used.append("Editorial Guidelines")
    return used


def _build_system_prompt(brand_context: str | None, content_brief_rules: str) -> str:
    base = (
        "Sei un content strategist SEO per ecommerce Shopify. "
        "Genera SOLO un brief operativo per un futuro articolo blog — NON scrivere l'articolo, "
        "NON generare body HTML, NON inventare claim non presenti nel contesto brand. "
        "Rispetta Safe Claims con priorità assoluta. "
        "Usa le Editorial Guidelines dal contesto brand per tono, lunghezza e firma autore. "
        f"{_BRIEF_EDITORIAL_RULES}"
        f"{_BRIEF_STRUCTURE_RULES}"
        "Scrivi in italiano. Rispondi SOLO con JSON valido.\n\n"
        f"{content_brief_rules}"
    )
    if brand_context:
        base += f"\n\n{brand_context}"
        base += _safe_claims_guardrail_suffix(brand_context)
    return base


def _build_user_prompt(item: ContentSeoEditorialItem, type_instruction: str) -> str:
    secondary = ", ".join(item.secondary_keywords or []) or "—"
    return (
        f"Genera un brief SEO per questo contenuto editoriale pianificato.\n\n"
        f"TIPO CONTENUTO: {item.content_type}\n"
        f"ISTRUZIONI TIPO: {type_instruction}\n"
        f"TITOLO PIANIFICATO: {item.title}\n"
        f"DATA PIANIFICATA: {item.planned_date}\n"
        f"OBIETTIVO: {item.objective or '—'}\n"
        f"INTENSITÀ COMMERCIALE: {item.commercial_intensity or '—'}\n"
        f"KEYWORD PRINCIPALE: {item.primary_keyword or '—'}\n"
        f"KEYWORD SECONDARIE: {secondary}\n"
        f"PRODOTTO COLLEGATO: {item.linked_shopify_product_title or '—'}\n"
        f"NOTE EDITORIALI: {item.notes or '—'}\n\n"
        "Il brief deve essere concreto e operativo per un redattore. "
        "In claimsToAvoid inserisci claim vietati dal contesto Safe Claims. "
        "In safeClaimsToUse inserisci solo claim esplicitamente consentiti. "
        "Decidi authorSuggestion in base al tipo contenuto e all'angolo: non forzare sempre una firma. "
        "Compila authorReason, contentLengthProfile, communityCtaSuggestion, editorialToneNotes, "
        "recommendedWordCountMin/Max, structureComplexity, maxH2, maxH3 e avoidRepetitions. "
        "Se mancano informazioni, segnalale in warnings.\n\n"
        f"Rispondi con JSON nel seguente schema:\n{_BRIEF_JSON_SCHEMA}"
    )


async def generate_editorial_brief_core(
    session: AsyncSession,
    project_id: UUID,
    item_id: UUID,
    *,
    job_id: str | None = None,
) -> ContentSeoEditorialItem:
    if not is_openai_configured():
        raise BriefGenerationError(
            "AI non configurata. Inserisci OPENAI_API_KEY per generare il brief.",
            ai_not_configured=True,
        )

    item = await get_editorial_item(session, project_id, item_id)
    bundle = await BrandIntelligenceContextBuilder.build_brand_context(session, project_id)
    ctx = await build_context_for_profile(
        session,
        project_id,
        AiContextProfile.BLOG_BRIEF,
        entity_type="editorial_item",
        entity_id=str(item_id),
        options={
            "shopify_product_id": str(item.linked_shopify_product_id)
            if item.linked_shopify_product_id
            else None,
            "editorial_item": {
                "title": item.title,
                "content_type": item.content_type,
                "primary_keyword": item.primary_keyword,
                "notes": item.notes,
            },
        },
    )
    brand_ctx = ctx.context_text

    product_pk_appended = bool(
        item.linked_shopify_product_id and brand_ctx and "PRODUCT KNOWLEDGE" in (brand_ctx or "")
    )

    bi_warnings = build_bi_warnings(bundle)
    type_instruction = _CONTENT_TYPE_INSTRUCTIONS.get(
        item.content_type,
        "Contenuto editoriale generico: brief SEO operativo.",
    )
    skill = load_seo_skill_context()
    system_prompt = _build_system_prompt(brand_ctx, skill.content_brief_rules)
    user_prompt = _build_user_prompt(item, type_instruction)

    try:
        parsed = await generate_structured_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            timeout=90.0,
            metadata=enrich_ai_metadata(
                AiRequestMetadata(
                    project_id=project_id,
                    module="blog_brief",
                    operation="batch_brief_item" if job_id else "generate_brief",
                    operation_key="blog_brief_batch_item" if job_id else "blog_brief_generation",
                    entity_type="editorial_item",
                    entity_id=str(item_id),
                    job_id=job_id,
                ),
                ctx,
            ),
            prompt_cache_key=build_prompt_cache_key(project_id, "blog_brief", ctx.context_hash),
        )
        payload = normalize_editorial_brief_payload(parsed)
        payload = enforce_brief_structure(payload, item.content_type, item.title)
    except OpenAINotConfiguredError:
        raise BriefGenerationError(
            "AI non configurata. Inserisci OPENAI_API_KEY per generare il brief.",
            ai_not_configured=True,
        ) from None
    except (OpenAIRequestError, ValidationError, ValueError) as exc:
        logger.warning("Editorial brief generation failed for %s: %s", item_id, exc)
        raise BriefGenerationError("Brief non generato per questo contenuto.") from exc

    context_used = build_brand_context_used(bundle, product_pk_appended=product_pk_appended)
    merged_warnings = list(dict.fromkeys([*bi_warnings, *payload.warnings]))
    payload.brand_context_used = context_used
    payload.warnings = merged_warnings

    item.brief_payload = payload.model_dump(mode="json", by_alias=True)
    item.status = "brief_pending"
    await session.commit()
    await session.refresh(item)
    return item


async def generate_editorial_brief(
    session: AsyncSession,
    project_id: UUID,
    item_id: UUID,
) -> ContentSeoEditorialItem:
    try:
        return await generate_editorial_brief_core(session, project_id, item_id)
    except BriefGenerationError as exc:
        if exc.ai_not_configured:
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            detail="Generazione brief non riuscita. Riprova più tardi o verifica la configurazione AI.",
        ) from exc


async def update_editorial_brief(
    session: AsyncSession,
    project_id: UUID,
    item_id: UUID,
    request: EditorialBriefUpdateRequest,
) -> ContentSeoEditorialItem:
    item = await get_editorial_item(session, project_id, item_id)
    try:
        payload = normalize_editorial_brief_payload(request.brief_payload)
    except ValidationError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="briefPayload non valido.",
        ) from exc

    item.brief_payload = payload.model_dump(mode="json", by_alias=True)
    if request.status is not None:
        item.status = request.status

    await session.commit()
    await session.refresh(item)
    return item
