"""Product Knowledge general import from single file — scoped AI extraction."""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brand_intelligence import BrandSafeClaims
from app.schemas.brand_product_knowledge import (
    BrandProductKnowledgeGeneralImportResponse,
    BrandProductKnowledgeGeneralProposal,
)
from app.services.ai.openai_client import (
    AiRequestMetadata,
    OpenAINotConfiguredError,
    OpenAIRequestError,
    generate_structured_json,
    is_openai_configured,
)
from app.services.ai.context_profiles import brand_import_metadata
from app.services.brand_intelligence.text_extraction import TextExtractionError, extract_text_from_bytes

logger = logging.getLogger(__name__)

GENERAL_IMPORT_SYSTEM_PROMPT = """Sei un assistente che estrae SOLO la Product Knowledge GENERALE da un documento.
Rispondi SOLO in JSON valido con i campi richiesti.

Regole rigorose:
- Estrai SOLO informazioni valide per tutti o quasi tutti i prodotti del brand.
- NON creare schede prodotto specifiche. Se trovi "Miele di Limone", "Polline", "Pappa Reale" ecc.,
  NON creare prodotti singoli: usa quei dettagli solo per dedurre principi generali ricorrenti.
- Campi lista: principi generali, punti di forza comuni, regole qualità, note produzione/uso,
  obiezioni comuni, regole comunicazione, regole storytelling prodotto.
- commonFaq: array di oggetti {{"question": "...", "answer": "..."}} con FAQ generali.
- NON inventare informazioni non presenti o chiaramente deducibili dal documento.
- NON generare claim medici o terapeutici non verificabili.
- Rispetta i Safe Claims forniti (se presenti): non includere claim vietati.
- Scrivi in italiano, testo chiaro e revisionabile.
- NON estrarre Brand Identity, Visual Identity, Safe Claims dettagliati o contenuti SEO.
- Se un campo non è supportato dal documento, usa null o array vuoto.
"""

GENERAL_IMPORT_USER_TEMPLATE = """Documento: {filename}

{safe_claims_block}

Testo estratto:
---
{document_text}
---

Genera una proposta Product Knowledge GENERALE con questo JSON:
{{
  "generalPrinciples": [],
  "commonStrengths": [],
  "commonQualityRules": [],
  "commonProductionNotes": [],
  "commonUsageNotes": [],
  "commonObjections": [],
  "commonFaq": [],
  "communicationRules": [],
  "productStorytellingRules": [],
  "notes": ""
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
    parts: list[str] = ["Safe Claims del brand (rispettare):"]
    if row.forbidden_claims:
        parts.append(f"- Vietati: {', '.join(row.forbidden_claims[:10])}")
    if row.allowed_claims:
        parts.append(f"- Consentiti: {', '.join(row.allowed_claims[:10])}")
    if row.caution_claims:
        parts.append(f"- Cautela: {', '.join(row.caution_claims[:8])}")
    if len(parts) == 1:
        return ""
    return "\n".join(parts) + "\n"


def _compute_confidence(proposal: BrandProductKnowledgeGeneralProposal, text_len: int) -> float:
    score = 0.15
    fields = [
        proposal.general_principles,
        proposal.common_strengths,
        proposal.common_quality_rules,
        proposal.common_production_notes,
        proposal.common_usage_notes,
    ]
    for field in fields:
        if field:
            score += min(0.12, 0.04 * len(field))
    if proposal.common_faq:
        score += min(0.1, 0.03 * len(proposal.common_faq))
    if text_len > 500:
        score += 0.1
    return round(min(0.95, max(0.1, score)), 2)


def _build_warnings(proposal: BrandProductKnowledgeGeneralProposal, text_len: int) -> list[str]:
    warnings: list[str] = []
    if text_len < 200:
        warnings.append("Documento breve: alcuni campi potrebbero essere incompleti.")
    if not proposal.general_principles and not proposal.common_strengths:
        warnings.append("Nessun principio o punto di forza generale individuato.")
    return warnings


async def import_general_from_file(
    session: AsyncSession,
    project_id: UUID,
    *,
    filename: str,
    content_type: str | None,
    data: bytes,
) -> BrandProductKnowledgeGeneralImportResponse:
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
    user_prompt = GENERAL_IMPORT_USER_TEMPLATE.format(
        filename=filename,
        safe_claims_block=safe_claims_block,
        document_text=truncated,
    )

    try:
        metadata, _ctx = await brand_import_metadata(
            session,
            project_id,
            AiRequestMetadata(
                project_id=project_id,
                module="brand_intelligence",
                operation="import_product_knowledge_general",
                entity_type="brand_section",
                entity_id="product_knowledge_general",
            ),
            section="product_knowledge_general",
            instructions="Estrazione Product Knowledge generale da documento",
        )
        parsed = await generate_structured_json(
            system_prompt=GENERAL_IMPORT_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            timeout=90.0,
            metadata=metadata,
        )
    except OpenAINotConfiguredError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI non configurata. Inserisci OPENAI_API_KEY per generare una proposta da file.",
        ) from None
    except OpenAIRequestError as exc:
        logger.exception("import_general_from_file AI error project=%s", project_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Errore generazione proposta: {exc.message}",
        ) from exc

    proposal = BrandProductKnowledgeGeneralProposal.model_validate(parsed)
    confidence = _compute_confidence(proposal, len(text))
    warnings = _build_warnings(proposal, len(text))
    source_summary = truncated[:400] + ("…" if len(truncated) > 400 else "")

    return BrandProductKnowledgeGeneralImportResponse(
        proposal=proposal,
        confidence=confidence,
        warnings=warnings,
        source_summary=source_summary,
    )
