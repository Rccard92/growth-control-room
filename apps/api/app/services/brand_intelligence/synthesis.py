"""AI synthesis of Brand Intelligence section drafts from extracted facts."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brand_intelligence import (
    BrandExtractedFact,
    BrandExternalSource,
    BrandImportBatch,
    BrandSectionDraft,
    BrandSourceDocument,
)
from app.schemas.brand_intelligence import BrandSectionDraftSynthesizeResponse, BrandSectionDraftSynthesizeSectionItem
from app.schemas.section_drafts import (
    FACT_SECTION_TO_DRAFT,
    SECTION_DRAFT_KEYS,
    SECTION_DRAFT_LABELS,
    SectionDraftWarnings,
    validate_draft_payload,
)
from app.services.ai.context_profiles import brand_import_metadata
from app.services.ai.openai_client import (
    AiRequestMetadata,
    OpenAINotConfiguredError,
    OpenAIRequestError,
    generate_structured_json,
    is_openai_configured,
)
from app.services.brand_intelligence.batch_service import update_batch_progress
from app.services.brand_intelligence.conflict_detection import (
    OfficialSnapshot,
    build_bi_summary,
    load_official_snapshot,
)
from app.services.brand_intelligence.source_fetcher import format_external_source_for_prompt

logger = logging.getLogger(__name__)

ACTIVE_DRAFT_STATUSES = frozenset({"draft", "needs_review", "approved"})

SECTION_SYNTHESIS_ORDER = [
    "brand_profile",
    "voice_tone",
    "products_categories",
    "audience",
    "claims_compliance",
    "seo_strategy",
    "content_pillars",
    "ai_guardrails",
    "assets",
]

SECTION_PAYLOAD_HINTS: dict[str, str] = {
    "brand_profile": '{"brand_name":"","short_description":"","story":"","mission":"","values":[],"differentiators":[]}',
    "voice_tone": '{"tone":"","style_notes":"","words_to_use":[],"words_to_avoid":[],"examples_good":[],"examples_bad":[]}',
    "products_categories": '{"products":[{"name":"","description":"","entityType":"product"}],"categories":[{"name":"","description":"","entityType":"category"}]}',
    "audience": '{"segments":[{"segmentName":"","description":""}]}',
    "claims_compliance": '{"allowed":[],"forbidden":[],"caution":[],"disclaimers":[]}',
    "seo_strategy": '{"primary_keywords":[],"secondary_keywords":[],"priority_pages":[],"competitors":[]}',
    "content_pillars": '{"pillars":[{"name":"","description":""}]}',
    "ai_guardrails": '{"guardrails":[{"title":"","description":"","ruleType":"must_not"}]}',
    "assets": '{"assets":[{"name":"","value":"","assetType":"other"}]}',
}

SYNTHESIS_SYSTEM_PROMPT = """You synthesize a complete Brand Intelligence section draft from extracted facts and documents.
Return JSON only with this shape:
{
  "draft_payload": { structured fields for the section },
  "summary": "2-3 sentence human summary of the draft",
  "confidence": 0.0,
  "warnings": ["..."],
  "missing_information": ["..."],
  "source_fact_ids": ["uuid strings from input facts used"],
  "source_external_ids": ["uuid strings from external sources used"],
  "ai_reasoning": "how you built this draft"
}

Rules:
- Do NOT invent data not supported by the provided facts/documents/external sources.
- Always cite whether data comes from file facts (source_fact_ids) or external sources (source_external_ids).
- If file facts and website/social/review sources conflict, add warnings — do not pick arbitrarily.
- If inferred (not explicit), confidence must be <= 0.65.
- Social sources with limited metadata → confidence <= 0.6 for voice/tone.
- Review platforms: aggregated customer insights only, not single reviews as truth.
- If external source status is failed/skipped, do NOT fill gaps with invented data.
- If documents conflict, add warnings — do not pick arbitrarily.
- If data is sparse, produce partial draft and list missing_information.
- Do not mix sections (claims vs products vs audience).
- Claims/compliance: be conservative; only include explicit claims.
- Priority sections for enrichment: brand_profile, voice_tone, audience, claims_compliance, seo_strategy, content_pillars.
- Use only source_fact_ids and source_external_ids that appear in the input.
"""


def _serialize_official_snapshot(snapshot: OfficialSnapshot) -> dict[str, Any]:
    def _profile() -> dict[str, Any] | None:
        if not snapshot.profile:
            return None
        p = snapshot.profile
        return {
            "brand_name": p.brand_name,
            "website_url": p.website_url,
            "industry": p.industry,
            "country": p.country,
            "short_description": p.short_description,
            "story": p.story,
            "mission": p.mission,
            "values": p.values,
            "differentiators": p.differentiators,
        }

    def _voice() -> dict[str, Any] | None:
        if not snapshot.voice:
            return None
        v = snapshot.voice
        return {
            "tone": v.tone,
            "style_notes": v.style_notes,
            "formality_level": v.formality_level,
            "emoji_policy": v.emoji_policy,
            "words_to_use": v.words_to_use,
            "words_to_avoid": v.words_to_avoid,
            "examples_good": v.examples_good,
            "examples_bad": v.examples_bad,
        }

    return {
        "brand_profile": _profile(),
        "voice_tone": _voice(),
        "products": [{"id": str(x.id), "name": x.name, "description": x.description} for x in snapshot.products],
        "categories": [{"id": str(x.id), "name": x.name, "description": x.description} for x in snapshot.categories],
        "audience": [
            {"id": str(x.id), "segment_name": x.segment_name, "description": x.description}
            for x in snapshot.audience
        ],
        "claims": [{"id": str(x.id), "title": x.title, "rule_type": x.rule_type} for x in snapshot.claims],
        "seo_strategy": {
            "primary_keywords": snapshot.seo.primary_keywords if snapshot.seo else None,
            "secondary_keywords": snapshot.seo.secondary_keywords if snapshot.seo else None,
        }
        if snapshot.seo
        else None,
        "content_pillars": [{"id": str(x.id), "name": x.name} for x in snapshot.pillars],
        "ai_guardrails": [{"id": str(x.id), "title": x.title} for x in snapshot.guardrails],
        "assets": [{"id": str(x.id), "name": x.name} for x in snapshot.assets],
    }


def _facts_for_section(facts: list[BrandExtractedFact], section_key: str) -> list[BrandExtractedFact]:
    if section_key == "products_categories":
        return [f for f in facts if f.target_section in ("product_knowledge", "category_knowledge")]
    reverse = {v: k for k, v in FACT_SECTION_TO_DRAFT.items()}
    target = reverse.get(section_key)
    if not target:
        return []
    return [f for f in facts if f.target_section == target]


def _format_facts_for_prompt(facts: list[BrandExtractedFact]) -> str:
    lines: list[str] = []
    for fact in facts:
        lines.append(
            json.dumps(
                {
                    "id": str(fact.id),
                    "target_section": fact.target_section,
                    "field_name": fact.field_name,
                    "extracted_value": fact.extracted_value,
                    "source_excerpt": fact.source_excerpt,
                    "confidence": fact.confidence,
                    "update_mode": fact.update_mode,
                },
                ensure_ascii=False,
            )
        )
    return "\n".join(lines) if lines else "Nessun fact per questa sezione."


async def _get_batch(session: AsyncSession, project_id: UUID, batch_id: UUID) -> BrandImportBatch:
    batch = (
        await session.execute(
            select(BrandImportBatch).where(
                BrandImportBatch.id == batch_id,
                BrandImportBatch.project_id == project_id,
            )
        )
    ).scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch non trovato.")
    return batch


async def _persist_section_draft(
    session: AsyncSession,
    *,
    project_id: UUID,
    batch_id: UUID,
    section_key: str,
    draft_payload: dict[str, Any],
    summary: str | None,
    source_fact_ids: list[str],
    source_document_ids: list[str],
    source_external_ids: list[str],
    confidence: float | None,
    draft_status: str,
    ai_reasoning: str | None,
    warnings: dict[str, Any],
    official_snapshot: dict[str, Any],
) -> BrandSectionDraft:
    existing = (
        await session.execute(
            select(BrandSectionDraft).where(
                BrandSectionDraft.project_id == project_id,
                BrandSectionDraft.batch_id == batch_id,
                BrandSectionDraft.section_key == section_key,
                BrandSectionDraft.status.in_(tuple(ACTIVE_DRAFT_STATUSES)),
            )
        )
    ).scalar_one_or_none()

    payload = validate_draft_payload(section_key, draft_payload)
    now = datetime.now(timezone.utc)

    if existing:
        existing.draft_payload = payload
        existing.summary = summary
        existing.source_fact_ids = source_fact_ids or None
        existing.source_document_ids = source_document_ids or None
        existing.source_external_ids = source_external_ids or None
        existing.confidence = confidence
        existing.status = draft_status
        existing.ai_reasoning = ai_reasoning
        existing.warnings = warnings
        existing.previous_official_snapshot = official_snapshot
        existing.approved_at = None
        existing.applied_at = None
        existing.updated_at = now
        await session.commit()
        await session.refresh(existing)
        return existing

    draft = BrandSectionDraft(
        project_id=project_id,
        batch_id=batch_id,
        section_key=section_key,
        title=SECTION_DRAFT_LABELS.get(section_key, section_key),
        draft_payload=payload,
        summary=summary,
        source_fact_ids=source_fact_ids or None,
        source_document_ids=source_document_ids or None,
        source_external_ids=source_external_ids or None,
        confidence=confidence,
        status=draft_status,
        ai_reasoning=ai_reasoning,
        warnings=warnings,
        previous_official_snapshot=official_snapshot,
    )
    session.add(draft)
    await session.commit()
    await session.refresh(draft)
    return draft


async def synthesize_section(
    session: AsyncSession,
    project_id: UUID,
    batch_id: UUID,
    section_key: str,
    *,
    extra_instructions: str | None = None,
    include_fact_ids: list[UUID] | None = None,
    update_progress: bool = True,
) -> BrandSectionDraft | None:
    if section_key not in SECTION_DRAFT_KEYS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sezione non valida.")

    if not is_openai_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OPENAI_API_KEY non configurata. La sintesi AI è disabilitata.",
        )

    batch = await _get_batch(session, project_id, batch_id)
    facts = list(
        (
            await session.execute(
                select(BrandExtractedFact).where(
                    BrandExtractedFact.project_id == project_id,
                    BrandExtractedFact.batch_id == batch_id,
                )
            )
        ).scalars().all()
    )
    if include_fact_ids:
        id_set = {str(i) for i in include_fact_ids}
        facts = [f for f in facts if str(f.id) in id_set]

    section_facts = _facts_for_section(facts, section_key)
    external_sources = list(
        (
            await session.execute(
                select(BrandExternalSource).where(BrandExternalSource.batch_id == batch_id)
            )
        ).scalars().all()
    )
    has_external_content = any(
        s.status == "fetched" or s.url for s in external_sources
    )
    if not section_facts and not extra_instructions and not has_external_content:
        return None

    docs = list(
        (
            await session.execute(
                select(BrandSourceDocument).where(BrandSourceDocument.batch_id == batch_id)
            )
        ).scalars().all()
    )
    doc_ids = list({str(f.source_document_id) for f in section_facts if f.source_document_id})
    ext_ids_from_facts = list(
        {str(f.source_external_id) for f in section_facts if f.source_external_id}
    )
    snapshot = await load_official_snapshot(session, project_id)
    official_json = _serialize_official_snapshot(snapshot)
    external_block = "\n".join(
        format_external_source_for_prompt(s) for s in external_sources
    ) or "No external sources."

    if update_progress:
        await update_batch_progress(
            session,
            batch,
            current_step=f"Sto generando {SECTION_DRAFT_LABELS.get(section_key, section_key)}",
            commit=True,
        )

    batch_header = ""
    if batch.declared_brand_name:
        batch_header += f"Declared brand name: {batch.declared_brand_name}\n"
    if batch.declared_website_url:
        batch_header += f"Declared website URL: {batch.declared_website_url}\n"

    bi_summary = build_bi_summary(snapshot)
    metadata, ctx = await brand_import_metadata(
        session,
        project_id,
        AiRequestMetadata(
            project_id=project_id,
            module="brand_intelligence",
            operation="synthesize_section",
            entity_type="brand_section",
            entity_id=section_key,
            job_id=str(batch_id),
        ),
        section=section_key,
        schema=SECTION_PAYLOAD_HINTS.get(section_key, "{}"),
        snapshot=bi_summary,
        existing=json.dumps(official_json, ensure_ascii=False)[:3000],
        instructions="Sintesi draft sezione Brand Intelligence da facts estratti",
    )

    user_prompt = (
        f"Section: {section_key}\n"
        f"Expected draft_payload shape example: {SECTION_PAYLOAD_HINTS.get(section_key, '{}')}\n\n"
        f"{batch_header}\n"
        f"{ctx.context_text}\n\n"
        f"Extracted facts for this section:\n{_format_facts_for_prompt(section_facts)}\n\n"
        f"External sources (public URLs — cite source_external_ids when used):\n{external_block}\n\n"
        f"Document summaries:\n"
        + "\n".join(
            f"- {d.filename}: {d.document_summary or 'N/A'}"
            for d in docs
            if str(d.id) in doc_ids or not doc_ids
        )
    )
    if extra_instructions:
        user_prompt += f"\n\nAdditional instructions:\n{extra_instructions}"

    try:
        parsed = await generate_structured_json(
            system_prompt=SYNTHESIS_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            timeout=120.0,
            metadata=metadata,
        )
    except OpenAINotConfiguredError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OPENAI_API_KEY non configurata.",
        ) from None
    except OpenAIRequestError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=exc.message) from exc

    raw_payload = parsed.get("draft_payload") or {}
    summary = str(parsed.get("summary") or "")
    confidence = float(parsed.get("confidence") or 0.0)
    confidence = max(0.0, min(1.0, confidence))
    raw_warnings = parsed.get("warnings") or []
    raw_missing = parsed.get("missing_information") or []
    if not isinstance(raw_warnings, list):
        raw_warnings = []
    if not isinstance(raw_missing, list):
        raw_missing = []

    warnings_obj = SectionDraftWarnings(
        messages=[str(w) for w in raw_warnings if str(w).strip()],
        missing_information=[str(m) for m in raw_missing if str(m).strip()],
    ).model_dump(by_alias=True)

    source_fact_ids = parsed.get("source_fact_ids") or [str(f.id) for f in section_facts]
    if not isinstance(source_fact_ids, list):
        source_fact_ids = [str(f.id) for f in section_facts]
    source_fact_ids = [str(x) for x in source_fact_ids]

    source_external_ids = parsed.get("source_external_ids") or ext_ids_from_facts
    if not isinstance(source_external_ids, list):
        source_external_ids = ext_ids_from_facts
    source_external_ids = [str(x) for x in source_external_ids]

    draft_status = "draft"
    if (
        confidence < 0.5
        or warnings_obj.get("missing_information")
        or (not section_facts and not source_external_ids)
    ):
        draft_status = "needs_review"

    return await _persist_section_draft(
        session,
        project_id=project_id,
        batch_id=batch_id,
        section_key=section_key,
        draft_payload=raw_payload if isinstance(raw_payload, dict) else {},
        summary=summary[:2000] if summary else None,
        source_fact_ids=source_fact_ids,
        source_document_ids=doc_ids,
        source_external_ids=source_external_ids,
        confidence=confidence,
        draft_status=draft_status,
        ai_reasoning=str(parsed.get("ai_reasoning") or "")[:4000] or None,
        warnings=warnings_obj,
        official_snapshot=official_json,
    )


async def synthesize_batch(
    session: AsyncSession,
    project_id: UUID,
    batch_id: UUID,
    *,
    update_progress: bool = True,
) -> BrandSectionDraftSynthesizeResponse:
    if not is_openai_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OPENAI_API_KEY non configurata. La sintesi AI è disabilitata.",
        )

    batch = await _get_batch(session, project_id, batch_id)
    sections_out: list[BrandSectionDraftSynthesizeSectionItem] = []
    created = 0

    for idx, section_key in enumerate(SECTION_SYNTHESIS_ORDER):
        if update_progress:
            pct = 75 + int((idx / len(SECTION_SYNTHESIS_ORDER)) * 20)
            await update_batch_progress(
                session,
                batch,
                progress_percent=pct,
                current_step=f"Sto generando {SECTION_DRAFT_LABELS.get(section_key, section_key)}",
                commit=True,
            )
        try:
            draft = await synthesize_section(
                session,
                project_id,
                batch_id,
                section_key,
                update_progress=False,
            )
            if draft:
                created += 1
                sections_out.append(
                    BrandSectionDraftSynthesizeSectionItem(
                        section_key=section_key,
                        status=draft.status,
                        confidence=draft.confidence,
                    )
                )
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("Synthesis failed for section %s batch %s", section_key, batch_id)
            batch_warnings = list(batch.warnings or [])
            batch_warnings.append(f"Sintesi {section_key} fallita: {exc}")
            batch.warnings = batch_warnings
            await session.commit()

    if update_progress:
        await update_batch_progress(
            session,
            batch,
            progress_percent=95,
            current_step="Bozze pronte per revisione",
            commit=True,
        )

    return BrandSectionDraftSynthesizeResponse(
        batch_id=batch_id,
        drafts_created=created,
        sections=sections_out,
    )
