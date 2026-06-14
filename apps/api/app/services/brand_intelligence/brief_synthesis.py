"""Brand Intelligence Brief synthesis from import batch."""

from __future__ import annotations

import json
import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brand_intelligence import (
    BrandExtractedFact,
    BrandExternalSource,
    BrandImportBatch,
    BrandIntelligenceBrief,
    BrandSourceDocument,
)
from app.schemas.brand_brief import build_markdown_summary, sanitize_brief_payload
from app.services.ai.context_profiles import brand_import_metadata
from app.services.ai.openai_client import (
    AiRequestMetadata,
    OpenAINotConfiguredError,
    OpenAIRequestError,
    generate_structured_json,
    is_openai_configured,
)
from app.services.brand_intelligence.conflict_detection import (
    build_bi_summary,
    load_official_snapshot,
)
from app.services.brand_intelligence.source_fetcher import format_external_source_for_prompt

logger = logging.getLogger(__name__)

BRIEF_SYSTEM_PROMPT = """You synthesize a complete Brand Intelligence Brief from extracted facts, documents, and external sources.
Return JSON only with this shape:
{
  "title": "Short brief title",
  "confidence": 0.0,
  "brief_payload": {
    "brand_identity": { "brand_name": "", "short_description": "", "story": "", "mission": "", "values": [], "differentiators": [] },
    "voice_and_tone": { "tone": "", "style_notes": "", "words_to_use": [], "words_to_avoid": [], "examples": [] },
    "products_and_categories": [ { "name": "", "type": "product|category|line", "description": "", "notes": [], "claims": [], "faq": [] } ],
    "audience": [ { "segment": "", "description": "", "motivations": [], "objections": [], "questions": [], "buying_triggers": [] } ],
    "questions_objections_feedback": { "common_questions": [], "common_objections": [], "customer_feedback": [], "social_comments_insights": [] },
    "claims_compliance": { "allowed_claims": [], "forbidden_claims": [], "caution_claims": [], "disclaimers": [] },
    "seo_guidelines": { "primary_keywords": [], "secondary_keywords": [], "content_clusters": [], "priority_pages": [], "internal_linking_notes": "", "meta_guidelines": "" },
    "content_pillars": [ { "name": "", "objective": "", "topics": [], "products": [], "channels": [] } ],
    "ads_social_guidelines": { "hooks": [], "angles": [], "pain_points": [], "creative_rules": [], "cta_examples": [] },
    "ai_guardrails": { "must_follow": [], "must_not": [], "needs_review": [] },
    "missing_information": [],
    "source_warnings": []
  }
}

Rules:
- Do NOT invent data not supported by the provided sources.
- If inferred (not explicit), note it in missing_information or source_warnings.
- Distinguish certain facts from items to verify.
- Do not mix allowed claims with forbidden claims.
- Do not generate medical/therapeutic claims.
- Separate products/categories from audience.
- Separate customer objections from SEO content.
- priority_pages may be strings OR objects with label/url — both are acceptable.
- claims may use text/title/label fields — structure flexibly.
- Always populate missing_information with gaps you could not fill from sources.
- Include source_warnings for inaccessible sources or low-confidence areas.
- Produce a useful brief for SEO, product copy, ads, email and future AI modules.
- Use clear, human-reviewable language.
"""

BRIEF_USER_TEMPLATE = """Build a Brand Intelligence Brief from these inputs.

## Batch context
Brand name (declared): {brand_name}
Website (declared): {website_url}

## Existing official Brand Intelligence (read-only context, do not overwrite)
{official_summary}

## Extracted facts ({fact_count})
{facts_json}

## Documents ({doc_count})
{docs_json}

## External sources ({ext_count})
{external_json}

Return the complete JSON brief. Partial sections are OK — list gaps in missing_information.
"""


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


async def _next_brief_version(session: AsyncSession, project_id: UUID) -> int:
    current = (
        await session.execute(
            select(func.max(BrandIntelligenceBrief.version)).where(
                BrandIntelligenceBrief.project_id == project_id
            )
        )
    ).scalar_one_or_none()
    return int(current or 0) + 1


def _serialize_facts(facts: list[BrandExtractedFact]) -> list[dict]:
    return [
        {
            "id": str(f.id),
            "target_section": f.target_section,
            "field_name": f.field_name,
            "extracted_value": f.extracted_value,
            "status": f.status,
            "confidence": f.confidence,
        }
        for f in facts
        if f.status != "rejected"
    ]


def _serialize_docs(docs: list[BrandSourceDocument]) -> list[dict]:
    return [
        {
            "id": str(d.id),
            "filename": d.filename,
            "extraction_status": d.extraction_status,
            "summary": (d.extracted_text or "")[:2000] if d.extracted_text else None,
        }
        for d in docs
    ]


def _serialize_external(sources: list[BrandExternalSource]) -> list[dict]:
    out = []
    for s in sources:
        if s.status == "skipped":
            continue
        out.append(
            {
                "id": str(s.id),
                "source_type": s.source_type,
                "url": s.url,
                "status": s.status,
                "content": format_external_source_for_prompt(s),
            }
        )
    return out


async def generate_brief_from_batch(
    session: AsyncSession,
    project_id: UUID,
    batch_id: UUID,
) -> BrandIntelligenceBrief:
    if not is_openai_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OPENAI_API_KEY non configurata. La generazione brief è disabilitata.",
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
    docs = list(
        (
            await session.execute(
                select(BrandSourceDocument).where(BrandSourceDocument.batch_id == batch_id)
            )
        ).scalars().all()
    )
    external = list(
        (
            await session.execute(
                select(BrandExternalSource).where(BrandExternalSource.batch_id == batch_id)
            )
        ).scalars().all()
    )

    active_facts = [f for f in facts if f.status != "rejected"]
    if not active_facts and not docs and not external:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dati insufficienti: servono facts, documenti o fonti esterne nel batch.",
        )

    snapshot = await load_official_snapshot(session, project_id)
    official_summary = build_bi_summary(snapshot)

    user_prompt = BRIEF_USER_TEMPLATE.format(
        brand_name=batch.declared_brand_name or "(non dichiarato)",
        website_url=batch.declared_website_url or "(non dichiarato)",
        official_summary=official_summary or "(nessun dato ufficiale)",
        fact_count=len(active_facts),
        facts_json=json.dumps(_serialize_facts(facts), ensure_ascii=False)[:12000],
        doc_count=len(docs),
        docs_json=json.dumps(_serialize_docs(docs), ensure_ascii=False)[:8000],
        ext_count=len(external),
        external_json=json.dumps(_serialize_external(external), ensure_ascii=False)[:8000],
    )

    try:
        metadata, _ctx = await brand_import_metadata(
            session,
            project_id,
            AiRequestMetadata(
                project_id=project_id,
                module="brand_intelligence",
                operation="generate_brief_from_batch",
                operation_key="brand_brief_synthesis",
                entity_type="brand_section",
                entity_id="intelligence_brief",
                job_id=str(batch_id),
            ),
            section="intelligence_brief",
            snapshot=official_summary,
            instructions="Sintesi Brand Intelligence Brief da batch import",
        )
        parsed = await generate_structured_json(
            system_prompt=BRIEF_SYSTEM_PROMPT,
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
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=exc.message,
        ) from exc

    raw_payload = parsed.get("brief_payload") if isinstance(parsed, dict) else {}
    if not isinstance(raw_payload, dict):
        raw_payload = parsed if isinstance(parsed, dict) else {}

    brief_payload, sanitize_warnings = sanitize_brief_payload(raw_payload)

    ai_warnings = parsed.get("source_warnings") or []
    if isinstance(ai_warnings, list):
        brief_payload["source_warnings"] = list(brief_payload.get("source_warnings") or []) + [
            str(w) for w in ai_warnings
        ]
    for w in sanitize_warnings:
        brief_payload["source_warnings"].append(w)

    confidence = parsed.get("confidence")
    if confidence is not None:
        try:
            confidence = max(0.0, min(1.0, float(confidence)))
        except (TypeError, ValueError):
            confidence = None

    title = str(parsed.get("title") or "").strip()
    if not title:
        brand_name = (brief_payload.get("brand_identity") or {}).get("brand_name") or ""
        title = f"Brand Intelligence Brief{f' — {brand_name}' if brand_name else ''}"

    version = await _next_brief_version(session, project_id)
    doc_ids = [str(d.id) for d in docs]
    ext_ids = [str(s.id) for s in external if s.status != "skipped"]
    fact_ids = [str(f.id) for f in active_facts]

    brief = BrandIntelligenceBrief(
        project_id=project_id,
        source_batch_id=batch_id,
        version=version,
        status="draft",
        title=title,
        brief_payload=brief_payload,
        markdown_summary=build_markdown_summary(brief_payload),
        confidence=confidence,
        warnings={"messages": sanitize_warnings} if sanitize_warnings else None,
        source_document_ids=doc_ids,
        source_external_ids=ext_ids,
        source_fact_ids=fact_ids,
    )
    session.add(brief)
    await session.commit()
    await session.refresh(brief)
    return brief
