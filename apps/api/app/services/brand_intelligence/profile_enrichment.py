"""Brand Profile v1 enrichment — fetch public sources and generate AI proposal."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brand_intelligence import BrandProfile
from app.schemas.brand_profile_v1 import (
    BrandProfileApplyProposalRequest,
    BrandProfileEnrichRequest,
    BrandProfileEnrichResponse,
    BrandProfileProposal,
    BrandProfileSourceResult,
)
from app.schemas.brand_intelligence import BrandProfileRead, BrandProfileUpdate
from app.services.ai.openai_client import (
    AiRequestMetadata,
    OpenAINotConfiguredError,
    OpenAIRequestError,
    generate_structured_json,
    is_openai_configured,
)
from app.services.brand_intelligence import service as bi_service
from app.services.brand_intelligence.source_fetcher import (
    fetch_profile_sources,
    format_fetched_source_for_prompt,
)

logger = logging.getLogger(__name__)

ENRICH_SYSTEM_PROMPT = """Sei un assistente che compila un Brand Profile per un e-commerce.
Rispondi SOLO in JSON valido con i campi richiesti.

Regole:
- Scrivi in italiano, testo chiaro e revisionabile.
- NON inventare informazioni non supportate dalle fonti fornite.
- Se un dato non è disponibile, lascia il campo vuoto o null.
- Distingui mentalmente dati certi (citati esplicitamente) da deduzioni conservative.
- NON includere claim medici, terapeutici o promesse non verificabili.
- NON generare strategia SEO, ads, PED o claims avanzati.
- values e differentiators sono array di stringhe brevi.
"""

ENRICH_USER_TEMPLATE = """Brand name dichiarato: {brand_name}

Fonti recuperate:
{sources_block}

Genera un Brand Profile con questi campi JSON:
{{
  "brandName": "...",
  "shortDescription": "...",
  "story": "...",
  "mission": "...",
  "values": [],
  "differentiators": [],
  "originNotes": "...",
  "productionNotes": "...",
  "toneNotes": "...",
  "customerNotes": "...",
  "aiSummary": "..."
}}
"""


def _collect_source_urls(request: BrandProfileEnrichRequest) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    if request.website_url:
        pairs.append(("website", request.website_url.strip()))
    if request.instagram_url:
        pairs.append(("instagram", request.instagram_url.strip()))
    if request.facebook_url:
        pairs.append(("facebook", request.facebook_url.strip()))
    if request.tiktok_url:
        pairs.append(("tiktok", request.tiktok_url.strip()))
    if request.youtube_url:
        pairs.append(("youtube", request.youtube_url.strip()))
    if request.linkedin_url:
        pairs.append(("linkedin", request.linkedin_url.strip()))
    if request.trustpilot_url:
        pairs.append(("trustpilot", request.trustpilot_url.strip()))
    if request.google_business_url:
        pairs.append(("google_business", request.google_business_url.strip()))
    for item in request.other_sources or []:
        url = (item.get("url") or "").strip()
        if url:
            label = (item.get("label") or "other").strip().lower()
            pairs.append((label, url))
    return pairs


def _compute_confidence(sources: list[BrandProfileSourceResult]) -> float:
    usable = [s for s in sources if s.status == "fetched"]
    if not usable:
        return 0.0
    score = 0.25
    for s in usable:
        if s.quality == "high":
            score += 0.25
        elif s.quality == "medium":
            score += 0.15
        elif s.quality == "low":
            score += 0.08
    blocked = [s for s in sources if s.status == "blocked"]
    if blocked:
        score -= 0.05 * len(blocked)
    return round(min(0.95, max(0.1, score)), 2)


def _build_warnings(sources: list[BrandProfileSourceResult]) -> list[str]:
    warnings: list[str] = []
    for s in sources:
        if s.status == "blocked":
            warnings.append(f"{s.type}: accesso bloccato (403/429) — {s.url}")
        elif s.status == "failed" and s.warning:
            warnings.append(f"{s.type}: {s.warning}")
    if not any(s.status == "fetched" for s in sources):
        warnings.append("Nessuna fonte ha restituito contenuto utilizzabile.")
    return warnings


async def _save_enrichment_metadata(
    session: AsyncSession,
    project_id: UUID,
    request: BrandProfileEnrichRequest,
    sources: list[BrandProfileSourceResult],
    confidence: float,
    warnings: list[str],
) -> None:
    row = await bi_service.get_profile(session, project_id)
    row.brand_name = request.brand_name
    row.website_url = request.website_url
    row.instagram_url = request.instagram_url
    row.facebook_url = request.facebook_url
    row.tiktok_url = request.tiktok_url
    row.youtube_url = request.youtube_url
    row.linkedin_url = request.linkedin_url
    row.trustpilot_url = request.trustpilot_url
    row.google_business_url = request.google_business_url
    row.other_sources = request.other_sources or []
    row.source_status = [s.model_dump(by_alias=True) for s in sources]
    row.last_enriched_at = datetime.now(timezone.utc)
    row.enrichment_confidence = confidence
    row.enrichment_warnings = warnings
    await session.commit()
    await session.refresh(row)


async def enrich_brand_profile(
    session: AsyncSession,
    project_id: UUID,
    request: BrandProfileEnrichRequest,
) -> BrandProfileEnrichResponse:
    if not request.brand_name or not request.brand_name.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Il nome brand è obbligatorio.",
        )

    source_pairs = _collect_source_urls(request)
    if not source_pairs:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Inserisci almeno una fonte (sito web o social).",
        )

    if not is_openai_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OPENAI_API_KEY non configurata.",
        )

    fetched = await fetch_profile_sources(source_pairs)
    sources = [
        BrandProfileSourceResult(
            type=item["type"],
            url=item["url"],
            status=item["status"],
            quality=item.get("quality"),
            warning=item.get("warning"),
        )
        for item in fetched
    ]

    usable = [item for item in fetched if _source_usable(item)]
    if not usable:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Nessuna fonte recuperabile. Verifica gli URL o riprova più tardi.",
        )

    sources_block = "\n".join(format_fetched_source_for_prompt(item) for item in usable)
    user_prompt = ENRICH_USER_TEMPLATE.format(
        brand_name=request.brand_name.strip(),
        sources_block=sources_block,
    )

    try:
        parsed = await generate_structured_json(
            system_prompt=ENRICH_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            timeout=90.0,
            metadata=AiRequestMetadata(
                project_id=project_id,
                module="brand_intelligence",
                operation="enrich_profile",
                entity_type="brand_section",
                entity_id="profile",
            ),
        )
    except OpenAINotConfiguredError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OPENAI_API_KEY non configurata.",
        ) from None
    except OpenAIRequestError as exc:
        logger.exception("enrich_brand_profile AI error project=%s", project_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Errore generazione profilo: {exc.message}",
        ) from exc

    proposal = BrandProfileProposal.model_validate(parsed)
    if not proposal.brand_name:
        proposal.brand_name = request.brand_name.strip()

    confidence = _compute_confidence(sources)
    warnings = _build_warnings(sources)

    await _save_enrichment_metadata(
        session, project_id, request, sources, confidence, warnings
    )

    return BrandProfileEnrichResponse(
        proposal=proposal,
        sources=sources,
        confidence=confidence,
        warnings=warnings,
    )


def _source_usable(item: dict[str, Any]) -> bool:
    raw = item.get("raw") or {}
    return item.get("status") == "fetched" and bool(
        raw.get("fetched_summary") or raw.get("fetched_text") or raw.get("fetched_title")
    )


async def apply_brand_profile_proposal(
    session: AsyncSession,
    project_id: UUID,
    request: BrandProfileApplyProposalRequest,
) -> BrandProfile:
    proposal = request.proposal
    payload = BrandProfileUpdate(
        brand_name=proposal.brand_name,
        short_description=proposal.short_description,
        story=proposal.story,
        mission=proposal.mission,
        values=proposal.values or None,
        differentiators=proposal.differentiators or None,
        origin_notes=proposal.origin_notes,
        production_notes=proposal.production_notes,
        tone_notes=proposal.tone_notes,
        customer_notes=proposal.customer_notes,
        ai_summary=proposal.ai_summary,
    )
    row = await bi_service.upsert_profile(session, project_id, payload)

    if request.confidence is not None:
        row.enrichment_confidence = request.confidence
    if request.warnings is not None:
        row.enrichment_warnings = request.warnings
    await session.commit()
    await session.refresh(row)
    return row
