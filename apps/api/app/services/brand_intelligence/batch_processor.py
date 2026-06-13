"""Async batch processor for Brand Intelligence import jobs."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select

from app.db.session import get_session_factory
from app.models.brand_intelligence import (
    BrandExtractedFact,
    BrandExternalSource,
    BrandImportBatch,
    BrandSourceDocument,
)
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
from app.services.brand_intelligence.external_sources_service import fetch_batch_external_sources
from app.services.brand_intelligence.source_fetcher import format_external_source_for_prompt
from app.services.ai.openai_client import (
    OpenAINotConfiguredError,
    OpenAIRequestError,
    generate_structured_json,
    is_openai_configured,
)

logger = logging.getLogger(__name__)

EXTRACTION_SYSTEM_PROMPT = """You extract structured brand intelligence facts from documents and public external sources.
Return JSON only with this shape:
{
  "document_type": "brand_book|catalog|product_sheet|faq|reviews|ads_comments|seo_notes|company_profile|website|social|unknown",
  "document_summary": "short summary",
  "facts": [
    {
      "target_section": "brand_profile|voice_tone|product_knowledge|category_knowledge|audience|claims_compliance|seo_strategy|content_pillars|ai_guardrails|assets|unknown",
      "field_name": "snake_case field or entity attribute",
      "extracted_value": "string or array",
      "source_excerpt": "verbatim quote from source",
      "source_external_id": "uuid string if from external source, else null",
      "confidence": 0.0,
      "ai_reasoning": "why this mapping",
      "update_mode": "create|enrich|update|duplicate_candidate|unknown"
    }
  ],
  "warnings": []
}

Rules:
- Distinguish file document facts vs website vs social vs review platform facts.
- Do NOT invent information not present in the provided sources.
- If a source is not accessible (status failed/skipped), do NOT fill gaps with invented data.
- If inferred (not explicit), confidence must be <= 0.65.
- If explicit in source, confidence can be higher (up to 0.95).
- Social metadata only → lower confidence (<= 0.6) for voice/tone inferences.
- Review platforms: use aggregated insights only, not single reviews as absolute truth.
- If file and website contradict, add a warning — do not pick arbitrarily.
- Every fact MUST include source_excerpt citing the source.
- For external source facts, set source_external_id to the matching id from the prompt.
- Compare with existing brand data: propose update_mode create/enrich/update appropriately.
"""


def _build_batch_context_header(batch: BrandImportBatch) -> str:
    parts: list[str] = []
    if batch.declared_brand_name:
        parts.append(f"Declared brand name: {batch.declared_brand_name}")
    if batch.declared_website_url:
        parts.append(f"Declared website URL: {batch.declared_website_url}")
    return "\n".join(parts)


def _format_external_sources_block(sources: list[BrandExternalSource]) -> str:
    if not sources:
        return "No external sources."
    return "\n".join(format_external_source_for_prompt(s) for s in sources)


def _persist_facts_from_parsed(
    session,
    *,
    project_id: UUID,
    batch_id: UUID,
    doc_id: UUID | None,
    raw_facts: list,
    import_round: int,
    now: datetime,
    default_external_id: UUID | None = None,
) -> int:
    created = 0
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
        ext_id = item.get("source_external_id") or default_external_id
        try:
            ext_uuid = UUID(str(ext_id)) if ext_id else None
        except (ValueError, TypeError):
            ext_uuid = default_external_id
        fact = BrandExtractedFact(
            project_id=project_id,
            source_document_id=doc_id,
            source_external_id=ext_uuid,
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
        created += 1
    return created


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
        total_docs = max(len(docs), 1)
        warnings: list[str] = []

        try:
            await update_batch_progress(
                session,
                batch,
                status="extracting",
                progress_percent=15,
                current_step="Preparazione documenti",
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
            batch_header = _build_batch_context_header(batch)

            await update_batch_progress(
                session,
                batch,
                progress_percent=30,
                current_step="Estrazione testo completata",
                commit=True,
            )

            # Fetch external sources (35-50%)
            await update_batch_progress(
                session,
                batch,
                progress_percent=35,
                current_step="Recupero fonti esterne",
                status="ai_processing",
                commit=True,
            )
            fetch_warnings, _ = await fetch_batch_external_sources(session, batch_id)
            warnings.extend(fetch_warnings)

            external_sources = list(
                (
                    await session.execute(
                        select(BrandExternalSource).where(
                            BrandExternalSource.batch_id == batch_id
                        )
                    )
                ).scalars().all()
            )
            external_block = _format_external_sources_block(external_sources)

            await update_batch_progress(
                session,
                batch,
                progress_percent=50,
                current_step="Sto integrando fonti esterne con i file caricati",
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
                doc.current_step = f"Estrazione AI file {idx} di {len(docs)}"
                pct = 50 + int((idx - 1) / total_docs * 22)
                doc.progress_percent = pct
                await update_batch_progress(
                    session,
                    batch,
                    progress_percent=pct,
                    current_step=f"Estrazione AI file {idx} di {len(docs)}",
                    commit=True,
                )

                try:
                    user_prompt = (
                        f"{batch_header}\n\n"
                        f"Existing Brand Intelligence (official data, read-only context):\n{bi_summary}\n\n"
                        f"External sources (fetched public content):\n{external_block}\n\n"
                        f"Filename: {doc.filename}\n"
                        f"Content-Type: {doc.content_type}\n\n"
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
                    created_count = _persist_facts_from_parsed(
                        session,
                        project_id=project_id,
                        batch_id=batch_id,
                        doc_id=doc.id,
                        raw_facts=raw_facts,
                        import_round=import_round,
                        now=now,
                    )

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

            # External-only extraction when no files but fetched sources exist
            if not docs and external_sources:
                fetched = [s for s in external_sources if s.status == "fetched"]
                if fetched:
                    await update_batch_progress(
                        session,
                        batch,
                        progress_percent=60,
                        current_step="Estrazione AI da fonti esterne",
                        commit=True,
                    )
                    try:
                        user_prompt = (
                            f"{batch_header}\n\n"
                            f"Existing Brand Intelligence:\n{bi_summary}\n\n"
                            f"External sources only (no uploaded files):\n{external_block}"
                        )
                        parsed = await generate_structured_json(
                            system_prompt=EXTRACTION_SYSTEM_PROMPT,
                            user_prompt=user_prompt,
                            timeout=90.0,
                        )
                        raw_facts = parsed.get("facts") or []
                        now = datetime.now(timezone.utc)
                        _persist_facts_from_parsed(
                            session,
                            project_id=project_id,
                            batch_id=batch_id,
                            doc_id=None,
                            raw_facts=raw_facts if isinstance(raw_facts, list) else [],
                            import_round=import_round,
                            now=now,
                        )
                        await session.commit()
                        success_count = 1
                    except Exception as exc:
                        logger.warning("External-only extraction failed: %s", exc)
                        warnings.append(f"Estrazione da fonti esterne fallita: {exc}")

            await update_batch_progress(
                session,
                batch,
                progress_percent=73,
                current_step="Rilevamento conflitti",
                commit=True,
            )
            await apply_conflict_detection_to_batch(session, project_id, batch_id)

            await update_batch_progress(
                session,
                batch,
                progress_percent=90,
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

            has_external = bool(external_sources)
            if fail_count > 0 and success_count > 0:
                final_status = "partially_failed"
            elif fail_count > 0 and success_count == 0 and not has_external:
                final_status = "failed"
                batch.error_message = "Tutti i file sono falliti durante l'estrazione."
            else:
                final_status = "review_ready"

            await update_batch_progress(
                session,
                batch,
                status=final_status,
                progress_percent=100,
                current_step="Pronto per generare Brand Brief" if final_status != "failed" else "Elaborazione fallita",
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
