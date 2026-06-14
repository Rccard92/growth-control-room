"""Safe Claims import from single file — scoped AI extraction."""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.brand_safe_claims import BrandSafeClaimsImportResponse, BrandSafeClaimsProposal
from app.services.ai.openai_client import (
    AiRequestMetadata,
    OpenAINotConfiguredError,
    OpenAIRequestError,
    generate_structured_json,
    is_openai_configured,
)
from app.services.brand_intelligence.text_extraction import TextExtractionError, extract_text_from_bytes

logger = logging.getLogger(__name__)

SAFE_CLAIMS_IMPORT_SYSTEM_PROMPT = """Sei un assistente che estrae SOLO Safe Claims e Red Flags da un documento.
Rispondi SOLO in JSON valido con i campi richiesti.

Regole rigorose:
- Estrai SOLO: claim consentiti, claim vietati, claim da usare con cautela, disclaimer,
  regole su claim salutistici, regole su competitor, process secrets, tone red flags.
- Scrivi in italiano, testo chiaro e revisionabile.
- NON inventare claim non presenti o chiaramente deducibili dal documento.
- Claim medici o terapeutici non verificabili → forbiddenClaims.
- Claim ambigui o sensibili → cautionClaims.
- NON estrarre Brand Identity, Visual Identity, Product Knowledge dettagliata o contenuti SEO.
- Tutti i campi lista sono array di stringhe brevi.
- Se un campo non è supportato dal documento, usa null o array vuoto.
"""

SAFE_CLAIMS_IMPORT_USER_TEMPLATE = """Documento: {filename}

Testo estratto:
---
{document_text}
---

Genera una proposta Safe Claims con questo JSON:
{{
  "allowedClaims": [],
  "forbiddenClaims": [],
  "cautionClaims": [],
  "disclaimers": [],
  "healthClaimRules": [],
  "competitorRules": [],
  "processSecrets": [],
  "toneRedFlags": [],
  "notes": "..."
}}
"""


def _truncate_text(text: str, max_chars: int = 12000) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[... testo troncato ...]"


def _compute_confidence(proposal: BrandSafeClaimsProposal, text_len: int) -> float:
    score = 0.2
    if proposal.allowed_claims:
        score += min(0.2, 0.05 * len(proposal.allowed_claims))
    if proposal.forbidden_claims:
        score += min(0.2, 0.05 * len(proposal.forbidden_claims))
    if proposal.caution_claims or proposal.disclaimers:
        score += 0.15
    if proposal.health_claim_rules or proposal.competitor_rules:
        score += 0.1
    if text_len > 500:
        score += 0.1
    return round(min(0.95, max(0.1, score)), 2)


def _build_warnings(proposal: BrandSafeClaimsProposal, text_len: int) -> list[str]:
    warnings: list[str] = []
    if text_len < 200:
        warnings.append("Documento breve: alcuni campi potrebbero essere incompleti.")
    if not proposal.allowed_claims and not proposal.forbidden_claims:
        warnings.append("Nessun claim esplicito individuato nel documento.")
    if not proposal.caution_claims and not proposal.disclaimers:
        warnings.append("Nessun disclaimer o claim con cautela trovato.")
    return warnings


async def import_safe_claims_from_file(
    session: AsyncSession,
    project_id: UUID,
    *,
    filename: str,
    content_type: str | None,
    data: bytes,
) -> BrandSafeClaimsImportResponse:
    del session, project_id  # no DB write on import preview

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
    user_prompt = SAFE_CLAIMS_IMPORT_USER_TEMPLATE.format(
        filename=filename,
        document_text=truncated,
    )

    try:
        parsed = await generate_structured_json(
            system_prompt=SAFE_CLAIMS_IMPORT_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            timeout=90.0,
            metadata=AiRequestMetadata(
                project_id=project_id,
                module="brand_intelligence",
                operation="import_safe_claims",
                entity_type="brand_section",
                entity_id="safe_claims",
            ),
        )
    except OpenAINotConfiguredError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI non configurata. Inserisci OPENAI_API_KEY per generare una proposta da file.",
        ) from None
    except OpenAIRequestError as exc:
        logger.exception("import_safe_claims_from_file AI error project=%s", project_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Errore generazione proposta: {exc.message}",
        ) from exc

    proposal = BrandSafeClaimsProposal.model_validate(parsed)
    confidence = _compute_confidence(proposal, len(text))
    warnings = _build_warnings(proposal, len(text))

    source_summary = truncated[:400] + ("…" if len(truncated) > 400 else "")

    return BrandSafeClaimsImportResponse(
        proposal=proposal,
        confidence=confidence,
        warnings=warnings,
        source_summary=source_summary,
    )
