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
    OpenAINotConfiguredError,
    OpenAIRequestError,
    generate_structured_json,
    is_openai_configured,
)
from app.services.brand_intelligence.context import BrandIntelligenceContextBuilder
from app.services.brand_intelligence.faq_objections_service import faq_objections_completion
from app.services.brand_intelligence.identity_service import identity_has_minimum
from app.services.brand_intelligence.product_knowledge_context import (
    get_product_knowledge_prompt_for_entity,
)
from app.services.brand_intelligence.safe_claims_service import safe_claims_has_minimum
from app.services.brand_intelligence.score import profile_has_minimum
from app.services.content.editorial_item_service import get_editorial_item
from app.services.content.seo_skill_loader import load_seo_skill_context

logger = logging.getLogger(__name__)

_CONTENT_TYPE_INSTRUCTIONS: dict[str, str] = {
    "educational_article": (
        "Articolo educativo: focus su intento informativo, guida pratica, "
        "struttura didattica H2/H3, E-E-A-T senza claim non verificati."
    ),
    "product_guide": (
        "Guida prodotto: collega benefici reali al catalogo, uso consigliato, "
        "prodotti da linkare prioritari, CTA soft verso acquisto."
    ),
    "recipe": (
        "Ricetta/contenuto food: ingredienti, passaggi in H2/H3, "
        "prodotto collegato come ingrediente o abbinamento, tono ispirazionale."
    ),
    "faq_objection_article": (
        "Articolo FAQ/obiezioni: rispondi a dubbi reali dal brand, "
        "sezione FAQ obbligatoria, tono rassicurante, no promesse non supportate."
    ),
    "product_comparison": (
        "Confronto prodotti: criteri oggettivi, tabella mentale in H2/H3, "
        "evita attacchi a competitor, confronta solo prodotti del brand se possibile."
    ),
    "seasonal_article": (
        "Articolo stagionale: angolo legato al periodo pianificato, "
        "riferimenti stagionali nel titolo e nella struttura."
    ),
    "brand_storytelling": (
        "Storytelling brand: valori, missione, dietro le quinte; "
        "emotivo ma fedele al Brand Identity, zero claim inventati."
    ),
}

_BRIEF_JSON_SCHEMA = """{
  "proposedTitle": "string",
  "searchIntent": "string",
  "targetAudience": "string",
  "primaryKeyword": "string",
  "secondaryKeywords": ["string"],
  "contentAngle": "string",
  "h2H3Structure": ["H2: ...", "H3: ..."],
  "productsToLink": ["string"],
  "faqToInclude": ["string"],
  "claimsToAvoid": ["string"],
  "safeClaimsToUse": ["string"],
  "recommendedCta": "string",
  "metaTitle": "string",
  "metaDescription": "string",
  "internalLinksSuggestions": ["string"],
  "notes": "string",
  "warnings": ["string"]
}"""


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
    return used


def _build_system_prompt(brand_context: str | None, content_brief_rules: str) -> str:
    base = (
        "Sei un content strategist SEO per ecommerce Shopify. "
        "Genera SOLO un brief operativo per un futuro articolo blog — NON scrivere l'articolo, "
        "NON generare body HTML, NON inventare claim non presenti nel contesto brand. "
        "Rispetta Safe Claims con priorità assoluta. "
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
        "Se mancano informazioni, segnalale in warnings.\n\n"
        f"Rispondi con JSON nel seguente schema:\n{_BRIEF_JSON_SCHEMA}"
    )


async def generate_editorial_brief(
    session: AsyncSession,
    project_id: UUID,
    item_id: UUID,
) -> ContentSeoEditorialItem:
    if not is_openai_configured():
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI non configurata. Inserisci OPENAI_API_KEY per generare il brief.",
        )

    item = await get_editorial_item(session, project_id, item_id)
    bundle = await BrandIntelligenceContextBuilder.build_brand_context(session, project_id)
    brand_ctx = BrandIntelligenceContextBuilder.format_for_prompt(bundle)

    product_pk_appended = False
    if item.linked_shopify_product_id:
        pk = await get_product_knowledge_prompt_for_entity(
            session,
            project_id,
            shopify_product_id=item.linked_shopify_product_id,
        )
        if pk:
            product_pk_appended = True
            brand_ctx = f"{brand_ctx}\n\n{pk}" if brand_ctx else pk

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
        )
        payload = normalize_editorial_brief_payload(parsed)
    except OpenAINotConfiguredError:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI non configurata. Inserisci OPENAI_API_KEY per generare il brief.",
        ) from None
    except (OpenAIRequestError, ValidationError, ValueError) as exc:
        logger.warning("Editorial brief generation failed for %s: %s", item_id, exc)
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            detail="Generazione brief non riuscita. Riprova più tardi o verifica la configurazione AI.",
        ) from exc

    context_used = build_brand_context_used(bundle, product_pk_appended=product_pk_appended)
    merged_warnings = list(dict.fromkeys([*bi_warnings, *payload.warnings]))
    payload.brand_context_used = context_used
    payload.warnings = merged_warnings

    item.brief_payload = payload.model_dump(mode="json", by_alias=True)
    item.status = "brief_pending"
    await session.commit()
    await session.refresh(item)
    return item


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
