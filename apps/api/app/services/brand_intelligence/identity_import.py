"""Brand Identity import from single file — scoped AI extraction."""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.brand_identity_visual import BrandIdentityImportResponse, BrandIdentityProposal
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

_IDENTITY_IMPORT_SCHEMA = """{
  "positioning": "...",
  "brandValues": [],
  "differentiators": [],
  "productionPrinciples": [],
  "qualityPrinciples": [],
  "trustElements": [],
  "whatBrandIs": "...",
  "whatBrandIsNot": "...",
  "storytellingNotes": "..."
}"""

IDENTITY_IMPORT_SYSTEM_PROMPT = """Sei un assistente che estrae SOLO la Brand Identity da un documento.
Rispondi SOLO in JSON valido con i campi richiesti.

Regole rigorose:
- Estrai SOLO: posizionamento, valori, differenziatori, principi produttivi/qualità, elementi fiducia,
  cosa il brand è, cosa il brand NON è, note storytelling.
- Scrivi in italiano, testo chiaro e revisionabile.
- NON inventare informazioni non presenti o chiaramente deducibili dal documento.
- NON creare Product Knowledge dettagliata, FAQ, claims medici, PED, Ads Strategy o contenuti SEO.
- Se nel file ci sono dettagli prodotto, usali SOLO se aiutano a definire l'identità generale del brand.
- NON includere claim medici, terapeutici o promesse non verificabili.
- brandValues, differentiators, productionPrinciples, qualityPrinciples, trustElements sono array di stringhe brevi.
- whatBrandIs e whatBrandIsNot sono stringhe (puoi usare elenchi puntati nel testo).
- Se un campo non è supportato dal documento, usa null o array vuoto.
"""

IDENTITY_IMPORT_USER_TEMPLATE = """Documento: {filename}

Testo estratto:
---
{document_text}
---

Genera una proposta Brand Identity con questo JSON:
{{
  "positioning": "...",
  "brandValues": [],
  "differentiators": [],
  "productionPrinciples": [],
  "qualityPrinciples": [],
  "trustElements": [],
  "whatBrandIs": "...",
  "whatBrandIsNot": "...",
  "storytellingNotes": "..."
}}
"""


def _truncate_text(text: str, max_chars: int = 12000) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[... testo troncato ...]"


def _compute_confidence(proposal: BrandIdentityProposal, text_len: int) -> float:
    score = 0.2
    if proposal.positioning:
        score += 0.2
    if proposal.brand_values:
        score += min(0.15, 0.05 * len(proposal.brand_values))
    if proposal.differentiators:
        score += min(0.15, 0.05 * len(proposal.differentiators))
    if proposal.what_brand_is:
        score += 0.1
    if proposal.what_brand_is_not:
        score += 0.1
    if text_len > 500:
        score += 0.1
    return round(min(0.95, max(0.1, score)), 2)


def _build_warnings(proposal: BrandIdentityProposal, text_len: int) -> list[str]:
    warnings: list[str] = []
    if text_len < 200:
        warnings.append("Documento breve: alcuni campi potrebbero essere incompleti.")
    if not proposal.positioning:
        warnings.append("Posizionamento non individuato nel documento.")
    if not proposal.brand_values and not proposal.differentiators:
        warnings.append("Valori o differenziatori non trovati esplicitamente.")
    return warnings


async def import_identity_from_file(
    session: AsyncSession,
    project_id: UUID,
    *,
    filename: str,
    content_type: str | None,
    data: bytes,
) -> BrandIdentityImportResponse:
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
    user_prompt = IDENTITY_IMPORT_USER_TEMPLATE.format(
        filename=filename,
        document_text=truncated,
    )

    try:
        metadata, _ctx = await brand_import_metadata(
            session,
            project_id,
            AiRequestMetadata(
                project_id=project_id,
                module="brand_intelligence",
                operation="import_identity",
                entity_type="brand_section",
                entity_id="identity",
            ),
            section="identity",
            schema=_IDENTITY_IMPORT_SCHEMA,
            instructions="Estrazione Brand Identity da documento singolo",
        )
        parsed = await generate_structured_json(
            system_prompt=IDENTITY_IMPORT_SYSTEM_PROMPT,
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
        logger.exception("import_identity_from_file AI error project=%s", project_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Errore generazione proposta: {exc.message}",
        ) from exc

    proposal = BrandIdentityProposal.model_validate(parsed)
    confidence = _compute_confidence(proposal, len(text))
    warnings = _build_warnings(proposal, len(text))

    source_summary = truncated[:400] + ("…" if len(truncated) > 400 else "")

    return BrandIdentityImportResponse(
        proposal=proposal,
        confidence=confidence,
        warnings=warnings,
        source_summary=source_summary,
    )
