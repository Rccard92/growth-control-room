"""AI Article Draft Generator for Content SEO editorial items.

Uses approved brief + BrandIntelligenceContextBuilder. Does not publish to Shopify.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_seo_editorial import ContentSeoEditorialItem
from app.schemas.content_seo_editorial import (
    EditorialArticlePayload,
    EditorialArticleUpdateRequest,
    normalize_editorial_article_payload,
)
from app.services.ai.openai_client import (
    OpenAINotConfiguredError,
    OpenAIRequestError,
    generate_structured_json,
    is_openai_configured,
)
from app.services.brand_intelligence.context import BrandIntelligenceContextBuilder
from app.services.brand_intelligence.product_knowledge_context import (
    get_product_knowledge_prompt_for_entity,
)
from app.services.content.editorial_brief_batch_service import has_editorial_brief_payload
from app.services.content.editorial_brief_service import (
    _CONTENT_TYPE_INSTRUCTIONS,
    _safe_claims_guardrail_suffix,
    build_bi_warnings,
    build_brand_context_used,
)
from app.services.content.editorial_item_service import get_editorial_item
from app.services.content.seo_skill_loader import load_seo_skill_context

logger = logging.getLogger(__name__)


class ArticleGenerationError(Exception):
    """Domain error for article generation (no HTTP)."""

    def __init__(
        self,
        message: str,
        *,
        ai_not_configured: bool = False,
        brief_not_approved: bool = False,
    ) -> None:
        super().__init__(message)
        self.ai_not_configured = ai_not_configured
        self.brief_not_approved = brief_not_approved


_ARTICLE_JSON_SCHEMA = """{
  "title": "string",
  "handle": "string",
  "excerpt": "string",
  "bodyHtml": "string",
  "bodyMarkdown": "string",
  "seoTitle": "string",
  "metaDescription": "string",
  "tags": ["string"],
  "linkedProducts": ["string"],
  "cta": "string",
  "authorName": "string",
  "authorRole": "string",
  "communityCta": "string",
  "contentLengthProfile": "breve|medio|approfondito",
  "warnings": ["string"]
}"""

_ARTICLE_TYPE_INSTRUCTIONS: dict[str, str] = {
    "educational_article": (
        "Articolo educativo: breve, chiaro, concreto — rispondi a un dubbio reale "
        "del cliente senza prolissità SEO."
    ),
    "product_guide": (
        "Guida prodotto: utile e pratica, non enciclopedica — collega benefici reali "
        "al catalogo con CTA soft."
    ),
    "recipe": (
        "Ricetta: pratica e semplice — passaggi chiari, prodotto collegato come "
        "ingrediente o abbinamento."
    ),
    "faq_objection_article": (
        "Articolo FAQ/obiezioni: risposta diretta e rassicurante — tono umano, "
        "max 4-6 FAQ solo se utili."
    ),
    "brand_storytelling": (
        "Storytelling brand: più narrativo e umano — valori e dietro le quinte, "
        "zero claim inventati."
    ),
    "product_comparison": (
        "Confronto prodotti: criteri oggettivi, breve e utile — evita attacchi a competitor."
    ),
    "seasonal_article": (
        "Articolo stagionale: angolo legato al periodo, concreto e non prolisso."
    ),
}

_EDITORIAL_HUMAN_RULES = """
REGOLE EDITORIALI (obbligatorie):
- Non scrivere articoli lunghi solo per SEO; evita ripetizioni e riempitivi.
- Target 700-1100 parole (salvo brief esplicito diverso o profilo lunghezza approfondito).
- Max 5-7 sezioni H2 principali; max 4-6 FAQ solo se davvero utili.
- Tono morbido, familiare, concreto — valore reale per i dubbi dei clienti.
- Aggiungi nota umana / firma brand quando coerente (es. A cura di Davide, Filippo, Salvo).
- NON inventare citazioni dirette o storie personali non presenti nel contesto brand.
- Usa le persone del brand solo se coerenti col tema dell'articolo.
- CTA finale community (scrivere, commentare, social, domande) — morbida, non aggressiva.
- communityCta è distinta da cta (community vs commerciale).
- Safe Claims restano prioritari assoluti su tutto.
"""


def _count_words_from_html(html: str) -> int:
    import re

    text = re.sub(r"<[^>]+>", " ", html or "")
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return 0
    return len(text.split())


def _derive_reading_time(word_count: int) -> str:
    if word_count <= 0:
        return ""
    minutes = max(1, round(word_count / 200))
    return f"{minutes} min"


def _derive_content_length_profile(
    word_count: int,
    default_length: str | None,
) -> str:
    if word_count <= 0:
        return default_length or "medio"
    if word_count < 700:
        return "breve"
    if word_count <= 1100:
        return "medio"
    return "approfondito"


def _enrich_article_payload(
    payload: EditorialArticlePayload,
    *,
    default_length: str | None = None,
) -> EditorialArticlePayload:
    word_count = _count_words_from_html(payload.body_html)

    updates: dict = {}
    if not payload.estimated_reading_time.strip():
        updates["estimated_reading_time"] = _derive_reading_time(word_count)
    if payload.content_length_profile is None:
        updates["content_length_profile"] = _derive_content_length_profile(
            word_count, default_length
        )
    if updates:
        return payload.model_copy(update=updates)
    return payload


def _build_article_system_prompt(
    brand_context: str | None,
    brand_guardrails: str,
    *,
    default_article_length: str | None = None,
) -> str:
    length_note = ""
    if default_article_length == "approfondito":
        length_note = (
            "\nProfilo lunghezza predefinito: approfondito — puoi superare 1100 parole "
            "solo se il brief lo richiede esplicitamente."
        )
    elif default_article_length == "breve":
        length_note = (
            "\nProfilo lunghezza predefinito: breve — punta a 500-800 parole, "
            "massima chiarezza."
        )

    base = (
        "Sei un redattore per ecommerce Shopify. "
        "Genera un articolo blog in italiano a partire dal brief SEO approvato. "
        "Scrivi come un essere umano: concreto, utile, non prolisso. "
        "Rispetta Safe Claims con priorità assoluta: non inventare claim medici, "
        "non promettere cure o guarigioni, non attaccare competitor, non divulgare process secrets. "
        "Usa il tono del brand dal contesto. "
        "bodyHtml deve usare SOLO tag sicuri: h2, h3, p, ul, ol, li, strong, em, a, blockquote. "
        "Nessuno script, iframe o style inline. "
        "Segui la struttura H2/H3 del brief. "
        "Includi prodotti da linkare e FAQ solo se presenti e sensati nel brief. "
        f"{_EDITORIAL_HUMAN_RULES}"
        f"{length_note}\n"
        "Rispondi SOLO con JSON valido.\n\n"
        f"{brand_guardrails}"
    )
    if brand_context:
        base += f"\n\n{brand_context}"
        base += _safe_claims_guardrail_suffix(brand_context)
    return base


def _build_article_user_prompt(item: ContentSeoEditorialItem, type_instruction: str) -> str:
    brief_json = json.dumps(item.brief_payload or {}, ensure_ascii=False, indent=2)
    return (
        f"Genera l'articolo completo per questo contenuto editoriale.\n\n"
        f"TIPO CONTENUTO: {item.content_type}\n"
        f"ISTRUZIONI TIPO: {type_instruction}\n"
        f"TITOLO PIANIFICATO: {item.title}\n"
        f"DATA PIANIFICATA: {item.planned_date}\n"
        f"PRODOTTO COLLEGATO: {item.linked_shopify_product_title or '—'}\n\n"
        f"BRIEF SEO APPROVATO (fonte principale — segui struttura, keyword, claim, FAQ, CTA):\n"
        f"{brief_json}\n\n"
        "bodyHtml deve essere HTML pulito pronto per anteprima e pubblicazione Shopify futura. "
        "handle: slug URL-friendly in minuscolo con trattini. "
        "excerpt: 1-2 frasi introduttive. "
        "Se mancano informazioni, segnalale in warnings.\n\n"
        f"Rispondi con JSON nel seguente schema:\n{_ARTICLE_JSON_SCHEMA}"
    )


async def generate_editorial_article_core(
    session: AsyncSession,
    project_id: UUID,
    item_id: UUID,
) -> ContentSeoEditorialItem:
    if not is_openai_configured():
        raise ArticleGenerationError(
            "AI non configurata. Inserisci OPENAI_API_KEY per generare l'articolo.",
            ai_not_configured=True,
        )

    item = await get_editorial_item(session, project_id, item_id)

    if not has_editorial_brief_payload(item.brief_payload):
        raise ArticleGenerationError(
            "Approva il brief prima di generare l'articolo.",
            brief_not_approved=True,
        )
    if item.status != "brief_approved":
        raise ArticleGenerationError(
            "Approva il brief prima di generare l'articolo.",
            brief_not_approved=True,
        )

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
    type_instruction = _ARTICLE_TYPE_INSTRUCTIONS.get(
        item.content_type,
        _CONTENT_TYPE_INSTRUCTIONS.get(
            item.content_type,
            "Contenuto editoriale generico: articolo blog chiaro e umano.",
        ),
    )
    default_length = (
        bundle.editorial_guidelines.default_article_length
        if getattr(bundle, "editorial_guidelines", None)
        else None
    )
    skill = load_seo_skill_context()
    system_prompt = _build_article_system_prompt(
        brand_ctx,
        skill.brand_guardrails,
        default_article_length=default_length,
    )
    user_prompt = _build_article_user_prompt(item, type_instruction)

    try:
        parsed = await generate_structured_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            timeout=120.0,
        )
        payload = normalize_editorial_article_payload(parsed)
        payload = _enrich_article_payload(
            payload,
            default_length=default_length,
        )
    except OpenAINotConfiguredError:
        raise ArticleGenerationError(
            "AI non configurata. Inserisci OPENAI_API_KEY per generare l'articolo.",
            ai_not_configured=True,
        ) from None
    except (OpenAIRequestError, ValidationError, ValueError) as exc:
        logger.warning("Editorial article generation failed for %s: %s", item_id, exc)
        raise ArticleGenerationError("Articolo non generato per questo contenuto.") from exc

    context_used = build_brand_context_used(bundle, product_pk_appended=product_pk_appended)
    merged_warnings = list(dict.fromkeys([*bi_warnings, *payload.warnings]))
    payload = payload.model_copy(
        update={
            "brand_context_used": context_used,
            "warnings": merged_warnings,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    )

    item.article_payload = payload.model_dump(mode="json", by_alias=True)
    item.status = "draft_review"
    await session.commit()
    await session.refresh(item)
    return item


async def generate_editorial_article(
    session: AsyncSession,
    project_id: UUID,
    item_id: UUID,
) -> ContentSeoEditorialItem:
    try:
        return await generate_editorial_article_core(session, project_id, item_id)
    except ArticleGenerationError as exc:
        if exc.brief_not_approved:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        if exc.ai_not_configured:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            detail="Generazione articolo non riuscita. Riprova più tardi o verifica la configurazione AI.",
        ) from exc


_DISALLOWED_ARTICLE_STATUSES = frozenset({"scheduled", "published", "publish_error"})


async def update_editorial_article(
    session: AsyncSession,
    project_id: UUID,
    item_id: UUID,
    request: EditorialArticleUpdateRequest,
) -> ContentSeoEditorialItem:
    item = await get_editorial_item(session, project_id, item_id)
    try:
        payload = normalize_editorial_article_payload(request.article_payload)
        payload = _enrich_article_payload(payload)
    except ValidationError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="articlePayload non valido.",
        ) from exc

    item.article_payload = payload.model_dump(mode="json", by_alias=True)
    if request.status is not None:
        if request.status in _DISALLOWED_ARTICLE_STATUSES:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Status non consentito da questo endpoint.",
            )
        item.status = request.status

    await session.commit()
    await session.refresh(item)
    return item
