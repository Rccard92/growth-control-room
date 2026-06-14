"""FAQ & Objections import from single file — scoped AI extraction."""

from __future__ import annotations

import json
import logging
from typing import Literal
from uuid import UUID

from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brand_intelligence import BrandSafeClaims
from app.schemas.brand_faq_objections import (
    BrandFaqObjectionsImportResponse,
    BrandFaqObjectionsProposal,
)
from app.services.ai.openai_client import (
    OpenAINotConfiguredError,
    OpenAIRequestError,
    generate_structured_json,
    is_openai_configured,
)
from app.services.brand_intelligence.text_extraction import TextExtractionError, extract_text_from_bytes

logger = logging.getLogger(__name__)

FieldKind = Literal["faq", "objections", "myths", "recommended", "content", "social", "generic"]

_MAX_STRING_LEN = 2000

FAQ_OBJECTIONS_IMPORT_SYSTEM_PROMPT = """Sei un assistente che estrae SOLO FAQ, obiezioni e dubbi clienti da un documento.
Rispondi SOLO in JSON valido con i campi richiesti.

Regole rigorose:
- Estrai SOLO: domande frequenti, obiezioni, falsi miti, risposte consigliate (se presenti nel file),
  insight da commenti social, opportunità di contenuto derivate da FAQ/obiezioni.
- Ogni campo lista deve essere un array di stringhe plain. NON usare oggetti dentro gli array.
- Scrivi in italiano, testo chiaro e revisionabile.
- NON inventare domande o risposte non presenti o chiaramente deducibili dal documento.
- Se una risposta non è nel file, lascia il campo vuoto e segnala nei warnings (non inventare).
- NON estrarre Brand Identity, Visual Identity, Safe Claims, schede prodotto complete, Product Knowledge dettagliata.
- NON creare claim medici o terapeutici.
- NON generare PED completo, articoli blog o ads.
- Separa bene: FAQ generali, domande prodotto/processo, domande acquisto/spedizione, obiezioni, falsi miti,
  risposte consigliate, opportunità contenuto, insight social.
- Per commenti social: estrai il dubbio sottostante, sintetizza l'obiezione, proponi suggestedReply solo se supportata.
- Rispetta eventuali Safe Claims del brand forniti nel prompt utente.
"""

FAQ_OBJECTIONS_IMPORT_USER_TEMPLATE = """{safe_claims_block}Documento: {filename}

Testo estratto:
---
{document_text}
---

Genera una proposta FAQ & Objections con questo JSON (liste di stringhe, NON oggetti negli array):
{{
  "generalFaq": ["Domanda: ...\\nRisposta: ..."],
  "productProcessQuestions": ["Domanda: ...\\nRisposta: ..."],
  "purchaseShippingQuestions": ["Domanda: ...\\nRisposta: ..."],
  "objections": ["..."],
  "mythsMisconceptions": ["Mito: ...\\nCorrezione: ..."],
  "recommendedAnswers": ["Obiezione: ...\\nRisposta consigliata: ..."],
  "contentOpportunities": ["..."],
  "socialCommentInsights": ["Insight: ... | Dubbio: ... | Risposta: ..."],
  "notes": "..."
}}
"""


def _truncate_text(text: str, max_chars: int = 12000) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[... testo troncato ...]"


def _soft_cap(value: str, max_len: int = _MAX_STRING_LEN) -> str:
    if len(value) <= max_len:
        return value
    return value[:max_len] + "…"


def _dedupe_strings(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        trimmed = item.strip()
        if not trimmed or trimmed in seen:
            continue
        seen.add(trimmed)
        out.append(_soft_cap(trimmed))
    return out


def _pick_field(data: dict[str, object], *aliases: str) -> object | None:
    for key in aliases:
        if key in data:
            return data[key]
    return None


def _get_str_field(data: dict[str, object], *keys: str) -> str:
    for key in keys:
        value = data.get(key)
        if isinstance(value, str):
            trimmed = value.strip()
            if trimmed:
                return trimmed
    return ""


def _format_faq_block(question: str, answer: str) -> str:
    q = question.strip()
    a = answer.strip()
    if not q:
        return ""
    if a:
        return f"Domanda: {q}\nRisposta: {a}"
    return f"Domanda: {q}"


def _format_myth_block(myth: str, correction: str) -> str:
    m = myth.strip()
    c = correction.strip()
    if not m:
        return ""
    if c:
        return f"Mito: {m}\nCorrezione: {c}"
    return f"Mito: {m}"


def _format_objection_answer_block(objection: str, answer: str) -> str:
    o = objection.strip()
    a = answer.strip()
    if not o:
        return ""
    if a:
        return f"Obiezione: {o}\nRisposta consigliata: {a}"
    return f"Obiezione: {o}"


def _format_social_block(insight: str, doubt: str, reply: str) -> str:
    parts: list[str] = []
    if insight.strip():
        parts.append(f"Insight: {insight.strip()}")
    if doubt.strip():
        parts.append(f"Dubbio: {doubt.strip()}")
    if reply.strip():
        parts.append(f"Risposta: {reply.strip()}")
    return " | ".join(parts)


def _serialize_unknown_object(item: dict[str, object]) -> str:
    try:
        return json.dumps(item, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return str(item)


def _expand_list_item(
    item: object,
    field_kind: FieldKind,
) -> tuple[list[str], list[str], list[str]]:
    """Return (primary_strings, recommended_extra, warnings)."""
    warnings: list[str] = []
    primary: list[str] = []
    recommended_extra: list[str] = []

    if item is None:
        return primary, recommended_extra, warnings

    if isinstance(item, str):
        trimmed = item.strip()
        if trimmed:
            primary.append(trimmed)
        return primary, recommended_extra, warnings

    if not isinstance(item, dict):
        warnings.append(f"Elemento ignorato (tipo non supportato): {type(item).__name__}")
        return primary, recommended_extra, warnings

    question = _get_str_field(item, "question", "domanda")
    answer = _get_str_field(item, "answer", "risposta", "response")
    objection = _get_str_field(item, "objection", "obiezione")
    myth = _get_str_field(item, "myth", "mito", "misconception")
    correction = _get_str_field(item, "correction", "correzione", "clarification")
    insight = _get_str_field(item, "insight")
    doubt = _get_str_field(item, "doubt", "dubbio", "concern")
    suggested_reply = _get_str_field(
        item, "suggestedReply", "suggested_reply", "reply", "rispostaConsigliata"
    )
    title = _get_str_field(item, "title", "titolo")
    description = _get_str_field(item, "description", "descrizione")
    text = _get_str_field(item, "text", "testo", "content")
    value = _get_str_field(item, "value", "valore")

    if field_kind == "faq" and (question or answer):
        block = _format_faq_block(question, answer)
        if block:
            primary.append(block)
        return primary, recommended_extra, warnings

    if field_kind == "objections" and (objection or answer):
        if objection:
            primary.append(objection)
        if objection and answer:
            block = _format_objection_answer_block(objection, answer)
            if block:
                recommended_extra.append(block)
        elif answer:
            recommended_extra.append(answer)
        return primary, recommended_extra, warnings

    if field_kind == "myths" and (myth or correction):
        block = _format_myth_block(myth, correction)
        if block:
            primary.append(block)
        return primary, recommended_extra, warnings

    if field_kind == "social" and (insight or doubt or suggested_reply):
        block = _format_social_block(insight, doubt, suggested_reply)
        if block:
            primary.append(block)
        return primary, recommended_extra, warnings

    if question or answer:
        block = _format_faq_block(question, answer)
        if block:
            primary.append(block)
        return primary, recommended_extra, warnings

    if objection:
        primary.append(objection)
        if answer:
            block = _format_objection_answer_block(objection, answer)
            if block:
                recommended_extra.append(block)
        return primary, recommended_extra, warnings

    if myth or correction:
        block = _format_myth_block(myth, correction)
        if block:
            primary.append(block)
        return primary, recommended_extra, warnings

    if insight or doubt or suggested_reply:
        block = _format_social_block(insight, doubt, suggested_reply)
        if block:
            primary.append(block)
        return primary, recommended_extra, warnings

    if title and description:
        primary.append(f"{title} — {description}")
        return primary, recommended_extra, warnings

    if title:
        primary.append(title)
        return primary, recommended_extra, warnings

    if text:
        primary.append(text)
        return primary, recommended_extra, warnings

    if value:
        primary.append(value)
        return primary, recommended_extra, warnings

    if item:
        warnings.append("Elemento oggetto non riconosciuto serializzato come testo.")
        primary.append(_serialize_unknown_object(item))

    return primary, recommended_extra, warnings


def _normalize_field_list(
    raw_value: object | None,
    field_kind: FieldKind,
) -> tuple[list[str], list[str], list[str]]:
    """Return (field_strings, recommended_spillover, warnings)."""
    warnings: list[str] = []
    primary: list[str] = []
    recommended_spillover: list[str] = []

    if raw_value is None:
        return primary, recommended_spillover, warnings

    if isinstance(raw_value, str):
        trimmed = raw_value.strip()
        if trimmed:
            primary.append(trimmed)
        return primary, recommended_spillover, warnings

    if not isinstance(raw_value, list):
        warnings.append(f"Campo lista atteso, ricevuto {type(raw_value).__name__}.")
        return primary, recommended_spillover, warnings

    for item in raw_value:
        item_primary, item_recommended, item_warnings = _expand_list_item(item, field_kind)
        primary.extend(item_primary)
        recommended_spillover.extend(item_recommended)
        warnings.extend(item_warnings)

    return primary, recommended_spillover, warnings


def normalize_faq_objections_ai_output(
    raw: object,
) -> tuple[dict[str, object], list[str]]:
    """Normalize flexible AI JSON into stable list[str] proposal shape."""
    warnings: list[str] = []
    empty: dict[str, object] = {
        "general_faq": [],
        "product_process_questions": [],
        "purchase_shipping_questions": [],
        "objections": [],
        "myths_misconceptions": [],
        "recommended_answers": [],
        "content_opportunities": [],
        "social_comment_insights": [],
        "notes": "",
    }

    if not isinstance(raw, dict):
        warnings.append("Output AI non è un oggetto JSON.")
        return empty, warnings

    field_specs: list[tuple[str, tuple[str, ...], FieldKind]] = [
        ("general_faq", ("general_faq", "generalFaq"), "faq"),
        (
            "product_process_questions",
            ("product_process_questions", "productProcessQuestions"),
            "faq",
        ),
        (
            "purchase_shipping_questions",
            ("purchase_shipping_questions", "purchaseShippingQuestions"),
            "faq",
        ),
        ("objections", ("objections",), "objections"),
        ("myths_misconceptions", ("myths_misconceptions", "mythsMisconceptions"), "myths"),
        ("recommended_answers", ("recommended_answers", "recommendedAnswers"), "recommended"),
        (
            "content_opportunities",
            ("content_opportunities", "contentOpportunities"),
            "content",
        ),
        (
            "social_comment_insights",
            ("social_comment_insights", "socialCommentInsights"),
            "social",
        ),
    ]

    result: dict[str, object] = dict(empty)
    recommended_accumulator: list[str] = []

    for field_key, aliases, field_kind in field_specs:
        raw_field = _pick_field(raw, *aliases)
        primary, spillover, field_warnings = _normalize_field_list(raw_field, field_kind)
        warnings.extend(field_warnings)
        result[field_key] = _dedupe_strings(primary)
        if field_kind == "objections":
            recommended_accumulator.extend(spillover)

    rec_primary, rec_spillover, rec_warnings = _normalize_field_list(
        _pick_field(raw, "recommended_answers", "recommendedAnswers"),
        "recommended",
    )
    warnings.extend(rec_warnings)
    recommended_accumulator.extend(rec_primary)
    recommended_accumulator.extend(rec_spillover)
    result["recommended_answers"] = _dedupe_strings(recommended_accumulator)

    notes_raw = _pick_field(raw, "notes", "note")
    if isinstance(notes_raw, str):
        result["notes"] = _soft_cap(notes_raw.strip())
    elif notes_raw is not None:
        warnings.append("Campo notes ignorato: atteso stringa.")

    return result, warnings


async def _load_safe_claims_block(session: AsyncSession, project_id: UUID) -> str:
    row = (
        await session.execute(
            select(BrandSafeClaims).where(BrandSafeClaims.project_id == project_id)
        )
    ).scalar_one_or_none()
    if not row:
        return ""
    parts: list[str] = ["Safe Claims del brand (rispettare — prioritari sui contenuti generati):"]
    if row.forbidden_claims:
        parts.append(f"- Vietati: {', '.join(row.forbidden_claims[:10])}")
    if row.allowed_claims:
        parts.append(f"- Consentiti: {', '.join(row.allowed_claims[:10])}")
    if row.caution_claims:
        parts.append(f"- Cautela: {', '.join(row.caution_claims[:8])}")
    if len(parts) == 1:
        return ""
    return "\n".join(parts) + "\n\n"


def _has_nonempty_strings(value: list[str] | None) -> bool:
    return bool(value and any(s.strip() for s in value))


def _faq_strings_missing_answer(entries: list[str] | None) -> list[str]:
    missing: list[str] = []
    for entry in entries or []:
        text = entry.strip()
        if not text:
            continue
        lower = text.lower()
        if lower.startswith("domanda:") and "risposta:" not in lower:
            question = text.split("\n", 1)[0].replace("Domanda:", "").strip()[:80]
            missing.append(question)
    return missing


def _compute_confidence(proposal: BrandFaqObjectionsProposal, text_len: int) -> float:
    score = 0.15
    if _has_nonempty_strings(proposal.general_faq):
        score += 0.15
    if _has_nonempty_strings(proposal.product_process_questions):
        score += 0.1
    if proposal.objections:
        score += min(0.15, 0.05 * len(proposal.objections))
    if proposal.recommended_answers:
        score += min(0.15, 0.05 * len(proposal.recommended_answers))
    if proposal.myths_misconceptions or proposal.content_opportunities:
        score += 0.1
    if text_len > 500:
        score += 0.1
    return round(min(0.95, max(0.1, score)), 2)


def _build_warnings(
    proposal: BrandFaqObjectionsProposal,
    text_len: int,
    normalize_warnings: list[str],
) -> list[str]:
    warnings: list[str] = list(normalize_warnings)
    if text_len < 200:
        warnings.append("Documento breve: alcuni campi potrebbero essere incompleti.")

    faq_groups = [
        ("FAQ generali", proposal.general_faq),
        ("Domande prodotto/processo", proposal.product_process_questions),
        ("Domande acquisto/spedizione", proposal.purchase_shipping_questions),
    ]
    for label, entries in faq_groups:
        for question in _faq_strings_missing_answer(entries):
            warnings.append(
                f"Risposta non presente nel documento per ({label}): {question}"
            )

    has_any = (
        _has_nonempty_strings(proposal.general_faq)
        or _has_nonempty_strings(proposal.product_process_questions)
        or _has_nonempty_strings(proposal.purchase_shipping_questions)
        or bool(proposal.objections)
        or bool(proposal.myths_misconceptions)
    )
    if not has_any:
        warnings.append("Nessuna FAQ o obiezione esplicita individuata nel documento.")

    return warnings


async def import_faq_objections_from_file(
    session: AsyncSession,
    project_id: UUID,
    *,
    filename: str,
    content_type: str | None,
    data: bytes,
) -> BrandFaqObjectionsImportResponse:
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
            detail="AI non configurata. Inserisci OPENAI_API_KEY per generare una proposta da file.",
        )

    truncated = _truncate_text(text.strip())
    safe_claims_block = await _load_safe_claims_block(session, project_id)
    user_prompt = FAQ_OBJECTIONS_IMPORT_USER_TEMPLATE.format(
        filename=filename,
        safe_claims_block=safe_claims_block,
        document_text=truncated,
    )

    try:
        parsed = await generate_structured_json(
            system_prompt=FAQ_OBJECTIONS_IMPORT_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            timeout=90.0,
        )
    except OpenAINotConfiguredError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI non configurata. Inserisci OPENAI_API_KEY per generare una proposta da file.",
        ) from None
    except OpenAIRequestError as exc:
        logger.exception("import_faq_objections_from_file AI error project=%s", project_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Errore generazione proposta: {exc.message}",
        ) from exc

    normalized, norm_warnings = normalize_faq_objections_ai_output(parsed)
    try:
        proposal = BrandFaqObjectionsProposal.model_validate(normalized)
    except ValidationError as exc:
        logger.warning(
            "FAQ import normalize validation failed project=%s: %s",
            project_id,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Impossibile normalizzare la proposta FAQ. Controlla il file o riprova.",
        ) from exc

    confidence = _compute_confidence(proposal, len(text))
    warnings = _build_warnings(proposal, len(text), norm_warnings)
    source_summary = truncated[:400] + ("…" if len(truncated) > 400 else "")

    return BrandFaqObjectionsImportResponse(
        proposal=proposal,
        confidence=confidence,
        warnings=warnings,
        source_summary=source_summary,
    )
