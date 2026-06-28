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
from app.services.content.editorial_article_postprocess import postprocess_editorial_article_html
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
        "del cliente. Target 700-950 parole, max 5 H2, max 3 H3, FAQ finali max 3."
    ),
    "product_guide": (
        "Guida prodotto: utile e pratica — focus su gusto, uso, conservazione e scelta. "
        "Target 800-1100 parole, max 5 H2."
    ),
    "recipe": (
        "Ricetta: pratica e semplice — ingredienti, procedimento, consigli, abbinamento. "
        "Target 600-900 parole, FAQ opzionali max 2."
    ),
    "faq_objection_article": (
        "Articolo FAQ/obiezioni: risposta diretta e rassicurante — target 700-950 parole, "
        "max 5 H2, max 3 H3, FAQ finali max 3."
    ),
    "brand_storytelling": (
        "Storytelling brand: più narrativo e umano — meno H2, più racconto. "
        "Target 700-1000 parole, max 4 H2."
    ),
    "product_comparison": (
        "Confronto prodotti: criteri oggettivi, utile — evita attacchi a competitor. "
        "Target 1000-1300 parole se necessario."
    ),
    "seasonal_article": (
        "Articolo stagionale: angolo legato al periodo, concreto — target 1000-1300 parole "
        "solo se il tema lo richiede."
    ),
}

_EDITORIAL_HUMAN_RULES = """
REGOLE EDITORIALI (obbligatorie):
- Non scrivere articoli lunghi solo per SEO; evita ripetizioni e riempitivi.
- Rispetta recommendedWordCountMin/Max, maxH2, maxH3 e structureComplexity dal brief.
- Se la struttura del brief è troppo lunga o ripetitiva, accorpa sezioni simili mantenendo il valore per il lettore.
- Tono morbido, familiare, concreto — valore reale per i dubbi dei clienti.
- Niente doppia introduzione: excerpt e primo paragrafo non devono ripetersi.
- FIRMA AUTORE: segui authorSuggestion del brief. Se vuoto, authorName e authorRole restano vuoti.
- Senza autore: usa "ci chiedono spesso", "riceviamo spesso questa domanda", "può capitare" — evita prima persona singolare forzata.
- NON inserire firma nel bodyHtml — solo nei campi authorName/authorRole se previsto dal brief.
- NON inventare citazioni dirette o opinioni personali non presenti nel contesto brand.
- NON attribuire opinioni a Davide, Filippo o Salvo se non supportate dalla Brand Intelligence.
- communityCta: usa communityCtaSuggestion del brief se presente; formula naturale e variata, breve.
- communityCta è distinta da cta (community vs commerciale).
- Evita di ripetere più volte gli stessi concetti elencati in avoidRepetitions del brief.
- Safe Claims restano prioritari assoluti su tutto.
"""


def _resolve_author_role(author_name: str, editorial_guidelines) -> str:
    if not editorial_guidelines or not getattr(editorial_guidelines, "brand_people", None):
        return ""
    for person in editorial_guidelines.brand_people:
        name = getattr(person, "name", "") or ""
        if name.strip() == author_name.strip():
            return getattr(person, "role", "") or ""
    return ""


def _apply_brief_author_to_payload(
    payload: EditorialArticlePayload,
    brief_raw: dict | None,
    bundle,
) -> EditorialArticlePayload:
    brief = normalize_editorial_brief_payload(brief_raw or {})
    author_suggestion = (brief.author_suggestion or "").strip()
    updates: dict = {}

    if not author_suggestion:
        updates["author_name"] = ""
        updates["author_role"] = ""
    else:
        updates["author_name"] = f"A cura di {author_suggestion}"
        eg = getattr(bundle, "editorial_guidelines", None)
        updates["author_role"] = _resolve_author_role(author_suggestion, eg)

    if brief.community_cta_suggestion.strip() and not payload.community_cta.strip():
        updates["community_cta"] = brief.community_cta_suggestion.strip()

    brief_profile = (brief.content_length_profile or "").strip()
    if brief_profile in ("breve", "medio", "approfondito"):
        updates["content_length_profile"] = brief_profile

    if updates:
        return payload.model_copy(update=updates)
    return payload


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
        "Segui la struttura H2/H3 del brief rispettando maxH2 e maxH3. "
        "Se il brief ha sezioni eccessive o ripetitive, accorpa mantenendo valore per il lettore. "
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
        "FIRMA E TONO (dal brief):\n"
        "- Se authorSuggestion è vuoto: authorName e authorRole devono restare vuoti.\n"
        "- Se authorSuggestion è valorizzato: compila authorName (es. A cura di ...) e authorRole.\n"
        "- Usa authorReason, editorialToneNotes, contentLengthProfile, communityCtaSuggestion del brief.\n"
        "- Rispetta recommendedWordCountMin/Max, maxH2, maxH3, structureComplexity e avoidRepetitions.\n"
        "- Non inserire la firma nel bodyHtml.\n\n"
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
    ctx = await build_context_for_profile(
        session,
        project_id,
        AiContextProfile.ARTICLE_DRAFT,
        entity_type="editorial_item",
        entity_id=str(item_id),
        options={
            "shopify_product_id": str(item.linked_shopify_product_id)
            if item.linked_shopify_product_id
            else None,
            "brief_payload": item.brief_payload,
        },
    )
    brand_ctx = ctx.context_text

    product_pk_appended = bool(
        item.linked_shopify_product_id and brand_ctx and "PRODUCT KNOWLEDGE" in (brand_ctx or "")
    )

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
            metadata=enrich_ai_metadata(
                AiRequestMetadata(
                    project_id=project_id,
                    module="article_generator",
                    operation="generate_article",
                    operation_key="article_draft_generation",
                    entity_type="editorial_item",
                    entity_id=str(item_id),
                ),
                ctx,
            ),
            prompt_cache_key=build_prompt_cache_key(
                project_id, "article_generator", ctx.context_hash
            ),
        )
        payload = normalize_editorial_article_payload(parsed)
        brief_norm = normalize_editorial_brief_payload(item.brief_payload or {})
        processed_html, post_warnings = postprocess_editorial_article_html(
            payload.body_html,
            payload.excerpt,
            brief_norm,
        )
        if processed_html != payload.body_html or post_warnings:
            payload = payload.model_copy(
                update={
                    "body_html": processed_html,
                    "warnings": list(dict.fromkeys([*payload.warnings, *post_warnings])),
                }
            )
        payload = _apply_brief_author_to_payload(
            payload, item.brief_payload, bundle
        )
        brief_profile = ""
        if item.brief_payload:
            brief_norm = normalize_editorial_brief_payload(item.brief_payload)
            brief_profile = (brief_norm.content_length_profile or "").strip()
        enrich_default = brief_profile or default_length
        payload = _enrich_article_payload(
            payload,
            default_length=enrich_default or None,
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
