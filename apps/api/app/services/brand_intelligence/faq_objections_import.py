"""FAQ & Objections import from single file — scoped AI extraction."""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import HTTPException, status
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

FAQ_OBJECTIONS_IMPORT_SYSTEM_PROMPT = """Sei un assistente che estrae SOLO FAQ, obiezioni e dubbi clienti da un documento.
Rispondi SOLO in JSON valido con i campi richiesti.

Regole rigorose:
- Estrai SOLO: domande frequenti, obiezioni, falsi miti, risposte consigliate (se presenti nel file),
  insight da commenti social, opportunità di contenuto derivate da FAQ/obiezioni.
- Scrivi in italiano, testo chiaro e revisionabile.
- NON inventare domande o risposte non presenti o chiaramente deducibili dal documento.
- Se una risposta non è nel file, lascia answer vuoto e segnala nei warnings (non inventare).
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

Genera una proposta FAQ & Objections con questo JSON:
{{
  "generalFaq": [{{"question": "...", "answer": "..."}}],
  "productProcessQuestions": [{{"question": "...", "answer": "..."}}],
  "purchaseShippingQuestions": [{{"question": "...", "answer": "..."}}],
  "objections": [],
  "mythsMisconceptions": [],
  "recommendedAnswers": [],
  "contentOpportunities": [],
  "socialCommentInsights": [{{"insight": "...", "doubt": "...", "suggestedReply": "..."}}],
  "notes": "..."
}}
"""


def _truncate_text(text: str, max_chars: int = 12000) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[... testo troncato ...]"


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


def _has_faq_entries(value: list | None) -> bool:
    if not value:
        return False
    return any(
        isinstance(e, dict) and (e.get("question") or "").strip() for e in value
    )


def _compute_confidence(proposal: BrandFaqObjectionsProposal, text_len: int) -> float:
    score = 0.15
    if _has_faq_entries(
        [e.model_dump() for e in (proposal.general_faq or [])]
    ):
        score += 0.15
    if _has_faq_entries(
        [e.model_dump() for e in (proposal.product_process_questions or [])]
    ):
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


def _build_warnings(proposal: BrandFaqObjectionsProposal, text_len: int) -> list[str]:
    warnings: list[str] = []
    if text_len < 200:
        warnings.append("Documento breve: alcuni campi potrebbero essere incompleti.")

    faq_groups = [
        ("FAQ generali", proposal.general_faq),
        ("Domande prodotto/processo", proposal.product_process_questions),
        ("Domande acquisto/spedizione", proposal.purchase_shipping_questions),
    ]
    for label, entries in faq_groups:
        for entry in entries or []:
            if entry.question.strip() and not entry.answer.strip():
                warnings.append(
                    f"Risposta non presente nel documento per ({label}): {entry.question[:80]}"
                )

    has_any = (
        _has_faq_entries([e.model_dump() for e in (proposal.general_faq or [])])
        or _has_faq_entries(
            [e.model_dump() for e in (proposal.product_process_questions or [])]
        )
        or _has_faq_entries(
            [e.model_dump() for e in (proposal.purchase_shipping_questions or [])]
        )
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

    proposal = BrandFaqObjectionsProposal.model_validate(parsed)
    confidence = _compute_confidence(proposal, len(text))
    warnings = _build_warnings(proposal, len(text))
    source_summary = truncated[:400] + ("…" if len(truncated) > 400 else "")

    return BrandFaqObjectionsImportResponse(
        proposal=proposal,
        confidence=confidence,
        warnings=warnings,
        source_summary=source_summary,
    )
