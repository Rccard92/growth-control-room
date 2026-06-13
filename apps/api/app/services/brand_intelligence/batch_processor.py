"""Async batch processor for Brand Intelligence import jobs."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select

from app.db.session import get_session_factory
from app.models.brand_intelligence import BrandExtractedFact, BrandImportBatch, BrandSourceDocument
from app.services.brand_intelligence.batch_service import finalize_batch_counts, update_batch_progress
from app.services.brand_intelligence.conflict_detection import (
    apply_conflict_detection_to_batch,
    build_bi_summary,
    load_official_snapshot,
)
from app.services.brand_intelligence.document_extraction import (
    VALID_TARGET_SECTIONS,
    _normalize_fact_status,
    _truncate_text,
)
from app.services.ai.openai_client import (
    OpenAINotConfiguredError,
    OpenAIRequestError,
    generate_structured_json,
    is_openai_configured,
)

logger = logging.getLogger(__name__)

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
      "ai_reasoning": "why this mapping",
      "update_mode": "create|enrich|update|duplicate_candidate|unknown"
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
- Every fact MUST include source_excerpt from the document.
- Compare with existing brand data in the prompt: propose update_mode create for new data,
  enrich for empty official fields, update for different values, duplicate_candidate for same values.
"""


def schedule_batch_processing(batch_id: UUID) -> None:
    asyncio.create_task(process_batch(batch_id))


async def process_batch(batch_id: UUID) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        batch = (
            await session.execute(
                select(BrandImportBatch).where(BrandImportBatch.id == batch_id)
            )
        ).scalar_one_or_none()
        if not batch:
            logger.error("Batch %s non trovato", batch_id)
            return

        project_id = batch.project_id
        docs = list(
            (
                await session.execute(
                    select(BrandSourceDocument)
                    .where(BrandSourceDocument.batch_id == batch_id)
                    .order_by(BrandSourceDocument.processing_order.asc())
                )
            ).scalars().all()
        )
        total_docs = len(docs) or 1
        warnings: list[str] = []

        try:
            await update_batch_progress(
                session,
                batch,
                status="extracting",
                progress_percent=10,
                current_step="Estrazione testo completata",
                commit=True,
            )

            if not is_openai_configured():
                batch.status = "failed"
                batch.error_message = "OPENAI_API_KEY non configurata."
                batch.current_step = "Elaborazione fallita"
                batch.completed_at = datetime.now(timezone.utc)
                await session.commit()
                return

            snapshot = await load_official_snapshot(session, project_id)
            bi_summary = build_bi_summary(snapshot)

            await update_batch_progress(
                session,
                batch,
                status="ai_processing",
                progress_percent=30,
                current_step="Classificazione documenti",
                commit=True,
            )

            # Clear draft facts for re-extract in same batch
            existing_facts = list(
                (
                    await session.execute(
                        select(BrandExtractedFact).where(
                            BrandExtractedFact.batch_id == batch_id,
                            BrandExtractedFact.status.in_(("suggested", "needs_review")),
                        )
                    )
                ).scalars().all()
            )
            for fact in existing_facts:
                await session.delete(fact)
            await session.commit()

            success_count = 0
            fail_count = 0
            import_round = 1

            for idx, doc in enumerate(docs, start=1):
                if doc.extraction_status == "failed" or not doc.extracted_text:
                    doc.progress_percent = 100
                    doc.current_step = "Estrazione testo fallita"
                    fail_count += 1
                    await session.commit()
                    continue

                doc.extraction_status = "extracting"
                doc.current_step = f"Estrazione AI file {idx} di {total_docs}"
                pct = 45 + int((idx - 1) / total_docs * 30)
                doc.progress_percent = pct
                await update_batch_progress(
                    session,
                    batch,
                    progress_percent=pct,
                    current_step=f"Estrazione AI file {idx} di {total_docs}",
                    commit=True,
                )

                try:
                    user_prompt = (
                        f"Filename: {doc.filename}\n"
                        f"Content-Type: {doc.content_type}\n\n"
                        f"Existing Brand Intelligence (official data, read-only context):\n{bi_summary}\n\n"
                        f"Document text:\n{_truncate_text(doc.extracted_text)}"
                    )
                    parsed = await generate_structured_json(
                        system_prompt=EXTRACTION_SYSTEM_PROMPT,
                        user_prompt=user_prompt,
                        timeout=90.0,
                    )
                    raw_facts = parsed.get("facts") or []
                    if not isinstance(raw_facts, list):
                        raw_facts = []
                    doc_warnings = parsed.get("warnings") or []
                    if isinstance(doc_warnings, list):
                        for w in doc_warnings:
                            if isinstance(w, str) and w.strip():
                                warnings.append(w.strip())

                    now = datetime.now(timezone.utc)
                    created_count = 0
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
                            source_document_id=doc.id,
                            batch_id=batch_id,
                            target_section=target_section,
                            target_entity_type=item.get("target_entity_type"),
                            field_name=item.get("field_name"),
                            extracted_value=item.get("extracted_value"),
                            source_excerpt=excerpt,
                            confidence=confidence,
                            status=_normalize_fact_status(confidence),
                            ai_reasoning=item.get("ai_reasoning"),
                            update_mode=str(item.get("update_mode") or "create"),
                            import_round=import_round,
                            source_created_at=now,
                        )
                        session.add(fact)
                        created_count += 1

                    doc.document_type = str(parsed.get("document_type") or "unknown")
                    summary = str(parsed.get("document_summary") or "")
                    doc.document_summary = summary[:2000] if summary else None
                    doc.extraction_status = "extracted"
                    doc.processed_at = now
                    doc.extraction_error = None
                    doc.progress_percent = 100
                    doc.current_step = "Completato"
                    doc.extracted_facts_count = created_count
                    success_count += 1
                    await session.commit()

                except (OpenAINotConfiguredError, OpenAIRequestError) as exc:
                    doc.extraction_status = "failed"
                    doc.extraction_error = getattr(exc, "message", str(exc))
                    doc.progress_percent = 100
                    doc.current_step = "Estrazione AI fallita"
                    fail_count += 1
                    await session.commit()
                except Exception as exc:
                    logger.exception("AI extraction failed for doc %s", doc.id)
                    doc.extraction_status = "failed"
                    doc.extraction_error = str(exc)
                    doc.progress_percent = 100
                    doc.current_step = "Estrazione AI fallita"
                    fail_count += 1
                    await session.commit()

            await update_batch_progress(
                session,
                batch,
                progress_percent=75,
                current_step="Rilevamento conflitti",
                commit=True,
            )
            await apply_conflict_detection_to_batch(session, project_id, batch_id)

            await update_batch_progress(
                session,
                batch,
                progress_percent=88,
                current_step="Preparazione review",
                commit=True,
            )
            await finalize_batch_counts(session, batch_id)

            batch = (
                await session.execute(
                    select(BrandImportBatch).where(BrandImportBatch.id == batch_id)
                )
            ).scalar_one()
            batch.warnings = warnings or None
            batch.processed_files = success_count + fail_count

            if fail_count > 0 and success_count > 0:
                final_status = "partially_failed"
            elif fail_count > 0 and success_count == 0:
                final_status = "failed"
                batch.error_message = "Tutti i file sono falliti durante l'estrazione."
            else:
                final_status = "review_ready"

            await update_batch_progress(
                session,
                batch,
                status=final_status,
                progress_percent=100,
                current_step="Pronto per revisione" if final_status != "failed" else "Elaborazione fallita",
                commit=True,
            )

        except Exception as exc:
            logger.exception("Batch processing failed for %s", batch_id)
            batch = (
                await session.execute(
                    select(BrandImportBatch).where(BrandImportBatch.id == batch_id)
                )
            ).scalar_one_or_none()
            if batch:
                batch.status = "failed"
                batch.error_message = str(exc)
                batch.current_step = "Elaborazione fallita"
                batch.completed_at = datetime.now(timezone.utc)
                await session.commit()
