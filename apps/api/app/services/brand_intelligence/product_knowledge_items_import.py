"""Product Knowledge item import from single file — scoped AI extraction."""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.brand_product_knowledge import (
    BrandProductKnowledgeItemProposal,
    BrandProductKnowledgeItemsImportResponse,
    BrandProductKnowledgeItemsProposal,
)
from app.services.ai.openai_client import (
    OpenAINotConfiguredError,
    OpenAIRequestError,
    generate_structured_json,
    is_openai_configured,
)
from app.services.brand_intelligence.product_knowledge_general_import import _load_safe_claims_block
from app.services.brand_intelligence.product_knowledge_shopify_match import suggest_shopify_matches
from app.services.brand_intelligence.text_extraction import TextExtractionError, extract_text_from_bytes

logger = logging.getLogger(__name__)

ITEMS_IMPORT_SYSTEM_PROMPT = """Sei un assistente che estrae SOLO schede prodotto SPECIFICHE da un documento.
Rispondi SOLO in JSON valido con il campo "items" (array di prodotti).

Regole rigorose:
- Crea una scheda per ogni prodotto chiaramente identificato nel documento.
- NON creare schede per prodotti non presenti nel file.
- NON inventare ingredienti, target, conservazione, FAQ, claim o note Ads se non presenti.
- NON compilare campi mancanti con contenuti generici inventati.
- Se un campo non è presente o non è chiaramente deducibile, usa "" per stringhe o [] per liste.
- Se un dato è dedotto (non esplicito), aggiungi un messaggio in warnings dell'item.
- NON generare claim medici o terapeutici non verificabili.
- NON estrarre regole generali prodotto, Brand Identity, Safe Claims o Visual Identity.
- Rispetta i Safe Claims forniti (se presenti): non includere claim vietati.
- Scrivi in italiano, testo chiaro e revisionabile.

Mappatura campi:
- Zona di produzione → origin
- Descrizione → strategicDescription o productionProcess secondo contesto
- Stato fisico → textureNotes
- Colore / aspetto → colorNotes
- Profilo olfattivo, aroma, profumo → tasteNotes
- Profilo gustativo → tasteNotes
- Carattere del prodotto → strategicDescription o seoNotes
- Epoca di fioritura/raccolta → productionProcess
- Dettagli senza campo preciso → seoNotes o strategicDescription con formulazione ordinata
- Obiezioni → objections (lista stringhe)
- FAQ → faq (array {{"question": "...", "answer": "..."}})
- Claim consentiti/vietati → allowedClaims / forbiddenClaims solo se espliciti
- priority: "high", "medium" o "low" solo se indicato, altrimenti "medium"
"""

ITEMS_IMPORT_USER_TEMPLATE = """Documento: {filename}

{safe_claims_block}

Testo estratto:
---
{document_text}
---

Genera schede prodotto specifiche con questo JSON (uno oggetto per prodotto identificato):
{{
  "items": [
    {{
      "productName": "",
      "productLine": "",
      "strategicDescription": "",
      "origin": "",
      "ingredients": "",
      "productionProcess": "",
      "tasteNotes": "",
      "colorNotes": "",
      "textureNotes": "",
      "usageSuggestions": "",
      "conservation": "",
      "targetAudience": "",
      "objections": [],
      "faq": [],
      "allowedClaims": [],
      "forbiddenClaims": [],
      "seoNotes": "",
      "adsSocialNotes": "",
      "relatedProducts": [],
      "priority": "medium",
      "warnings": []
    }}
  ]
}}
"""

_STRATEGIC_FIELD_CHECKS: list[tuple[str, str]] = [
    ("productLine", "product_line"),
    ("strategicDescription", "strategic_description"),
    ("origin", "origin"),
    ("ingredients", "ingredients"),
    ("productionProcess", "production_process"),
    ("tasteNotes", "taste_notes"),
    ("colorNotes", "color_notes"),
    ("textureNotes", "texture_notes"),
    ("usageSuggestions", "usage_suggestions"),
    ("conservation", "conservation"),
    ("targetAudience", "target_audience"),
    ("objections", "objections"),
    ("faq", "faq"),
    ("allowedClaims", "allowed_claims"),
    ("forbiddenClaims", "forbidden_claims"),
    ("seoNotes", "seo_notes"),
    ("adsSocialNotes", "ads_social_notes"),
    ("relatedProducts", "related_products"),
    ("priority", "priority"),
]


def _truncate_text(text: str, max_chars: int = 12000) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[... testo troncato ...]"


def _normalize_proposal_item(item: BrandProductKnowledgeItemProposal) -> BrandProductKnowledgeItemProposal:
    data = item.model_dump()
    for key, value in list(data.items()):
        if isinstance(value, str) and not value.strip():
            data[key] = None
        elif isinstance(value, list) and len(value) == 0:
            if key in ("warnings", "missing_fields"):
                data[key] = []
            else:
                data[key] = None
    if not data.get("priority"):
        data["priority"] = "medium"
    return BrandProductKnowledgeItemProposal.model_validate(data)


def compute_item_missing_fields(proposal: BrandProductKnowledgeItemProposal) -> list[str]:
    missing: list[str] = []
    for camel, snake in _STRATEGIC_FIELD_CHECKS:
        value = getattr(proposal, snake)
        if value is None:
            missing.append(camel)
        elif isinstance(value, str) and not value.strip():
            missing.append(camel)
        elif isinstance(value, list) and len(value) == 0:
            missing.append(camel)
    return missing


def _compute_item_confidence(proposal: BrandProductKnowledgeItemProposal) -> float:
    total = len(_STRATEGIC_FIELD_CHECKS)
    filled = total - len(proposal.missing_fields)
    score = filled / total if total else 0.1
    if proposal.warnings:
        score = max(0.1, score - 0.05 * min(len(proposal.warnings), 3))
    return round(min(0.95, max(0.1, score)), 2)


def _build_global_warnings(items: list[BrandProductKnowledgeItemProposal], text_len: int) -> list[str]:
    warnings: list[str] = []
    if text_len < 200:
        warnings.append("Documento breve: alcune schede potrebbero essere incomplete.")
    if len(items) > 15:
        warnings.append(f"Individuati {len(items)} prodotti: verifica ogni scheda prima di salvare.")
    low_conf = [i.product_name for i in items if i.confidence < 0.35]
    if low_conf:
        warnings.append(
            f"Pochi dati per: {', '.join(low_conf[:5])}"
            + ("…" if len(low_conf) > 5 else "")
        )
    return warnings


def _post_process_items(items: list[BrandProductKnowledgeItemProposal]) -> list[BrandProductKnowledgeItemProposal]:
    processed: list[BrandProductKnowledgeItemProposal] = []
    seen_names: set[str] = set()
    for raw in items:
        if not raw.product_name or not raw.product_name.strip():
            continue
        item = _normalize_proposal_item(raw)
        norm = item.product_name.strip().lower()
        if norm in seen_names:
            continue
        seen_names.add(norm)
        item.missing_fields = compute_item_missing_fields(item)
        item.confidence = _compute_item_confidence(item)
        processed.append(item)
    return processed


async def import_items_from_file(
    session: AsyncSession,
    project_id: UUID,
    *,
    filename: str,
    content_type: str | None,
    data: bytes,
) -> BrandProductKnowledgeItemsImportResponse:
    if not filename or not filename.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Nome file non valido.",
        )

    try:
        text = extract_text_from_bytes(
            content_type=content_type or "",
            filename=filename,
            data=data,
        )
    except TextExtractionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.message,
        ) from exc

    if not text or not text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Il file non contiene testo leggibile.",
        )

    if not is_openai_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI non configurata. Inserisci OPENAI_API_KEY per generare schede prodotto da file.",
        )

    truncated = _truncate_text(text.strip())
    safe_claims_block = await _load_safe_claims_block(session, project_id)
    user_prompt = ITEMS_IMPORT_USER_TEMPLATE.format(
        filename=filename,
        safe_claims_block=safe_claims_block,
        document_text=truncated,
    )

    try:
        parsed = await generate_structured_json(
            system_prompt=ITEMS_IMPORT_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            timeout=90.0,
        )
    except OpenAINotConfiguredError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI non configurata. Inserisci OPENAI_API_KEY per generare schede prodotto da file.",
        ) from None
    except OpenAIRequestError as exc:
        logger.exception("import_items_from_file AI error project=%s", project_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Errore generazione schede: {exc.message}",
        ) from exc

    raw_proposal = BrandProductKnowledgeItemsProposal.model_validate(parsed)
    items = _post_process_items(raw_proposal.items)

    if not items:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Nessun prodotto identificato nel file.",
        )

    await suggest_shopify_matches(session, project_id, items)

    warnings = _build_global_warnings(items, len(text))
    source_summary = truncated[:400] + ("…" if len(truncated) > 400 else "")

    return BrandProductKnowledgeItemsImportResponse(
        proposal=BrandProductKnowledgeItemsProposal(items=items),
        source_summary=source_summary,
        warnings=warnings,
    )
