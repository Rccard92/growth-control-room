"""AI document classification and fact extraction for Brand Intelligence."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brand_intelligence import BrandExtractedFact, BrandSourceDocument
from app.services.ai.openai_client import (
    AiRequestMetadata,
    OpenAINotConfiguredError,
    OpenAIRequestError,
    generate_structured_json,
    is_openai_configured,
)

logger = logging.getLogger(__name__)

VALID_TARGET_SECTIONS = frozenset(
    {
        "brand_profile",
        "voice_tone",
        "product_knowledge",
        "category_knowledge",
        "audience",
        "claims_compliance",
        "seo_strategy",
        "content_pillars",
        "ai_guardrails",
        "assets",
        "unknown",
    }
)

EXTRACTION_SYSTEM_PROMPT = """You extract structured brand intelligence facts from documents.
Return JSON only with this shape:
{
  "document_type": "brand_book|catalog|product_sheet|faq|reviews|ads_comments|seo_notes|company_profile|unknown",
  "document_summary": "short summary",
  "facts": [
    {
      "target_section": "brand_profile|voice_tone|product_knowledge|category_knowledge|audience|claims_compliance|seo_strategy|content_pillars|ai_guardrails|assets|unknown",
      "field_name": "snake_case field or entity attribute",
      "extracted_value": "string or array",
      "source_excerpt": "verbatim quote from document",
      "confidence": 0.0,
      "ai_reasoning": "why this mapping"
    }
  ],
  "warnings": []
}

Rules:
- Do NOT invent information not present in the document.
- If inferred (not explicit), confidence must be <= 0.65.
- If explicit in document, confidence can be higher (up to 0.95).
- If unsure where a fact belongs, use target_section=unknown.
- Never auto-approve; facts are suggestions only.
- Do not mix product vs category vs audience vs claims incorrectly.
- Every fact MUST include source_excerpt from the document.
- For product facts use target_section=product_knowledge; for categories use category_knowledge.
- For claims use claims_compliance with field_name rule_type (forbidden|caution|allowed) when possible.
- For guardrails use ai_guardrails with field_name rule_type (must_not|must|caution).
"""


def _truncate_text(text: str, max_chars: int = 12000) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[... testo troncato ...]"


def _normalize_fact_status(confidence: float) -> str:
    if confidence < 0.5:
        return "needs_review"
    return "suggested"


async def _get_document(
    session: AsyncSession, project_id: UUID, document_id: UUID
) -> BrandSourceDocument:
    row = (
        await session.execute(
            select(BrandSourceDocument).where(
                BrandSourceDocument.id == document_id,
                BrandSourceDocument.project_id == project_id,
            )
        )
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento non trovato.")
    return row


async def run_ai_extraction(
    session: AsyncSession,
    project_id: UUID,
    document_id: UUID,
) -> list[BrandExtractedFact]:
    if not is_openai_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OPENAI_API_KEY non configurata. Upload ed estrazione testo funzionano; l'estrazione AI è disabilitata.",
        )

    doc = await _get_document(session, project_id, document_id)
    if not doc.extracted_text or not doc.extracted_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nessun testo estratto dal documento. Ricarica il file o verifica il formato.",
        )

    doc.extraction_status = "extracting"
    doc.extraction_error = None
    await session.commit()

    try:
        user_prompt = (
            f"Filename: {doc.filename}\n"
            f"Content-Type: {doc.content_type}\n\n"
            f"Document text:\n{_truncate_text(doc.extracted_text)}"
        )
        parsed = await generate_structured_json(
            system_prompt=EXTRACTION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            timeout=90.0,
            metadata=AiRequestMetadata(
                project_id=project_id,
                module="brand_intelligence",
                operation="extract_document",
                entity_type="brand_section",
                entity_id=str(document_id),
            ),
        )
    except OpenAINotConfiguredError:
        doc.extraction_status = "failed"
        doc.extraction_error = "OPENAI_API_KEY non configurata"
        await session.commit()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OPENAI_API_KEY non configurata.",
        ) from None
    except OpenAIRequestError as exc:
        doc.extraction_status = "failed"
        doc.extraction_error = exc.message
        await session.commit()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=exc.message,
        ) from exc

    document_type = str(parsed.get("document_type") or "unknown")
    document_summary = str(parsed.get("document_summary") or "")
    raw_facts = parsed.get("facts") or []
    if not isinstance(raw_facts, list):
        raw_facts = []

    # Remove previous suggested facts for this document (re-extract replaces draft)
    existing = list(
        (
            await session.execute(
                select(BrandExtractedFact).where(
                    BrandExtractedFact.source_document_id == document_id,
                    BrandExtractedFact.status.in_(("suggested", "needs_review")),
                )
            )
        ).scalars().all()
    )
    for fact in existing:
        await session.delete(fact)

    created: list[BrandExtractedFact] = []
    now = datetime.now(timezone.utc)
    for item in raw_facts:
        if not isinstance(item, dict):
            continue
        target_section = str(item.get("target_section") or "unknown")
        if target_section not in VALID_TARGET_SECTIONS:
            target_section = "unknown"
        confidence = float(item.get("confidence") or 0.0)
        confidence = max(0.0, min(1.0, confidence))
        excerpt = str(item.get("source_excerpt") or "").strip()
        if not excerpt:
            continue
        fact = BrandExtractedFact(
            project_id=project_id,
            source_document_id=document_id,
            target_section=target_section,
            target_entity_type=item.get("target_entity_type"),
            field_name=item.get("field_name"),
            extracted_value=item.get("extracted_value"),
            source_excerpt=excerpt,
            confidence=confidence,
            status=_normalize_fact_status(confidence),
            ai_reasoning=item.get("ai_reasoning"),
        )
        session.add(fact)
        created.append(fact)

    doc.document_type = document_type
    doc.document_summary = document_summary[:2000] if document_summary else None
    doc.extraction_status = "extracted"
    doc.processed_at = now
    doc.extraction_error = None
    await session.commit()
    for fact in created:
        await session.refresh(fact)
    return created


async def run_ai_extraction_batch(
    session: AsyncSession,
    project_id: UUID,
    document_ids: list[UUID],
) -> dict:
    results: list[dict] = []
    for doc_id in document_ids:
        try:
            facts = await run_ai_extraction(session, project_id, doc_id)
            results.append(
                {
                    "documentId": str(doc_id),
                    "status": "extracted",
                    "factsCount": len(facts),
                    "error": None,
                }
            )
        except HTTPException as exc:
            results.append(
                {
                    "documentId": str(doc_id),
                    "status": "failed",
                    "factsCount": 0,
                    "error": exc.detail if isinstance(exc.detail, str) else json.dumps(exc.detail),
                }
            )
        except Exception as exc:
            logger.exception("Batch extraction failed for %s", doc_id)
            results.append(
                {
                    "documentId": str(doc_id),
                    "status": "failed",
                    "factsCount": 0,
                    "error": str(exc),
                }
            )
    return {"results": results}
