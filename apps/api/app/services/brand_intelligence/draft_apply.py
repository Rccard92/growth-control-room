"""Apply approved BrandSectionDraft to official Brand Intelligence tables."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brand_intelligence import BrandSectionDraft
from app.schemas.brand_intelligence import (
    BrandAiGuardrailCreate,
    BrandAssetCreate,
    BrandAudienceInsightCreate,
    BrandClaimRuleCreate,
    BrandContentPillarCreate,
    BrandProductKnowledgeCreate,
    BrandProfileUpdate,
    BrandSectionDraftApplyResponse,
    BrandSectionDraftApplyResultItem,
    BrandSeoStrategyUpdate,
    BrandVoiceUpdate,
)
from app.services.brand_intelligence import service as bi_service
from app.services.brand_intelligence.conflict_detection import _is_empty, _values_equal, load_official_snapshot
from app.services.brand_intelligence.fact_apply import _as_str

APPLY_RESULT = BrandSectionDraftApplyResultItem


def _item(draft_id: UUID, section_key: str, status: str, message: str) -> BrandSectionDraftApplyResultItem:
    return BrandSectionDraftApplyResultItem(
        draft_id=draft_id,
        section_key=section_key,
        status=status,
        message=message,
    )


async def _get_draft(session: AsyncSession, project_id: UUID, draft_id: UUID) -> BrandSectionDraft:
    draft = (
        await session.execute(
            select(BrandSectionDraft).where(
                BrandSectionDraft.id == draft_id,
                BrandSectionDraft.project_id == project_id,
            )
        )
    ).scalar_one_or_none()
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft non trovato.")
    return draft


async def apply_section_draft(
    session: AsyncSession,
    project_id: UUID,
    draft_id: UUID,
) -> BrandSectionDraftApplyResponse:
    draft = await _get_draft(session, project_id, draft_id)
    if draft.status == "applied":
        return BrandSectionDraftApplyResponse(
            skipped=[_item(draft.id, draft.section_key, "skipped", "Draft già applicato.")],
        )
    if draft.status == "rejected":
        return BrandSectionDraftApplyResponse(
            skipped=[_item(draft.id, draft.section_key, "skipped", "Draft rifiutato.")],
        )
    if draft.status != "approved":
        return BrandSectionDraftApplyResponse(
            skipped=[
                _item(
                    draft.id,
                    draft.section_key,
                    "skipped",
                    "Approva il draft prima di applicare.",
                )
            ],
        )

    payload = draft.draft_payload or {}
    section = draft.section_key
    snapshot = await load_official_snapshot(session, project_id)
    conflicts: list[BrandSectionDraftApplyResultItem] = []
    applied: list[BrandSectionDraftApplyResultItem] = []

    try:
        if section == "brand_profile":
            result, conflict_msgs = await _apply_scalar_section(
                session,
                project_id,
                payload,
                snapshot.profile,
                {
                    "brand_name",
                    "website_url",
                    "industry",
                    "country",
                    "short_description",
                    "story",
                    "mission",
                    "values",
                    "differentiators",
                },
                upsert_fn=bi_service.upsert_profile,
                schema=BrandProfileUpdate,
            )
        elif section == "voice_tone":
            result, conflict_msgs = await _apply_scalar_section(
                session,
                project_id,
                payload,
                snapshot.voice,
                {
                    "tone",
                    "style_notes",
                    "formality_level",
                    "emoji_policy",
                    "words_to_use",
                    "words_to_avoid",
                    "examples_good",
                    "examples_bad",
                },
                upsert_fn=bi_service.upsert_voice,
                schema=BrandVoiceUpdate,
            )
        elif section == "seo_strategy":
            result, conflict_msgs = await _apply_scalar_section(
                session,
                project_id,
                payload,
                snapshot.seo,
                {
                    "primary_keywords",
                    "secondary_keywords",
                    "keyword_clusters",
                    "priority_pages",
                    "internal_linking_notes",
                    "meta_title_pattern",
                    "meta_description_pattern",
                    "url_handle_pattern",
                    "competitors",
                },
                upsert_fn=bi_service.upsert_seo_strategy,
                schema=BrandSeoStrategyUpdate,
            )
        elif section == "products_categories":
            result, conflict_msgs = await _apply_products_categories(session, project_id, payload, snapshot)
        elif section == "audience":
            result, conflict_msgs = await _apply_audience(session, project_id, payload, snapshot)
        elif section == "claims_compliance":
            result, conflict_msgs = await _apply_claims(session, project_id, payload, snapshot)
        elif section == "content_pillars":
            result, conflict_msgs = await _apply_pillars(session, project_id, payload, snapshot)
        elif section == "ai_guardrails":
            result, conflict_msgs = await _apply_guardrails(session, project_id, payload, snapshot)
        elif section == "assets":
            result, conflict_msgs = await _apply_assets(session, project_id, payload, snapshot)
        else:
            return BrandSectionDraftApplyResponse(
                skipped=[_item(draft.id, section, "skipped", "Sezione non supportata.")],
            )
    except Exception as exc:
        return BrandSectionDraftApplyResponse(
            skipped=[_item(draft.id, section, "error", str(exc))],
        )

    if conflict_msgs:
        draft.status = "needs_review"
        await session.commit()
        return BrandSectionDraftApplyResponse(
            conflicts=[
                _item(draft.id, section, "conflict", msg) for msg in conflict_msgs
            ],
        )

    draft.status = "applied"
    draft.applied_at = datetime.now(timezone.utc)
    await session.commit()
    applied.append(_item(draft.id, section, "applied", result))
    return BrandSectionDraftApplyResponse(applied=applied)


async def apply_section_drafts_batch(
    session: AsyncSession,
    project_id: UUID,
    draft_ids: list[UUID],
) -> BrandSectionDraftApplyResponse:
    if not draft_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nessun draft da applicare.")

    merged = BrandSectionDraftApplyResponse()
    for draft_id in draft_ids:
        partial = await apply_section_draft(session, project_id, draft_id)
        merged.applied.extend(partial.applied)
        merged.skipped.extend(partial.skipped)
        merged.conflicts.extend(partial.conflicts)
    return merged


async def _apply_scalar_section(
    session: AsyncSession,
    project_id: UUID,
    payload: dict[str, Any],
    official_row: Any,
    fields: set[str],
    *,
    upsert_fn: Any,
    schema: Any,
) -> tuple[str, list[str]]:
    updates: dict[str, Any] = {}
    conflicts: list[str] = []

    for key, value in payload.items():
        if key not in fields or value is None:
            continue
        existing = getattr(official_row, key, None) if official_row else None
        if _is_empty(existing):
            updates[key] = value
        elif _values_equal(existing, value):
            continue
        else:
            conflicts.append(f"Conflitto su campo {key}: dato ufficiale già valorizzato.")

    if conflicts:
        return "", conflicts
    if not updates:
        return "Nessun campo da aggiornare (tutti già valorizzati o identici).", []

    await upsert_fn(session, project_id, schema(**updates))
    return f"Aggiornati {len(updates)} campi.", []


async def _apply_products_categories(
    session: AsyncSession,
    project_id: UUID,
    payload: dict[str, Any],
    snapshot: Any,
) -> tuple[str, list[str]]:
    created = 0
    conflicts: list[str] = []
    products = payload.get("products") or []
    categories = payload.get("categories") or []

    for item in products:
        if not isinstance(item, dict):
            continue
        name = _as_str(item.get("name"))
        if not name:
            continue
        existing = next(
            (p for p in snapshot.products if p.name and p.name.lower() == name.lower()),
            None,
        )
        if existing:
            conflicts.append(f"Prodotto già esistente: {name}")
            continue
        await bi_service.create_product(
            session,
            project_id,
            BrandProductKnowledgeCreate(
                name=name,
                description=_as_str(item.get("description")),
                entity_type="product",
            ),
        )
        created += 1

    for item in categories:
        if not isinstance(item, dict):
            continue
        name = _as_str(item.get("name"))
        if not name:
            continue
        existing = next(
            (c for c in snapshot.categories if c.name and c.name.lower() == name.lower()),
            None,
        )
        if existing:
            conflicts.append(f"Categoria già esistente: {name}")
            continue
        await bi_service.create_product(
            session,
            project_id,
            BrandProductKnowledgeCreate(
                name=name,
                description=_as_str(item.get("description")),
                entity_type="category",
            ),
        )
        created += 1

    if conflicts and created == 0:
        return "", conflicts
    return f"Creati {created} prodotti/categorie.", conflicts if conflicts else []


async def _apply_audience(
    session: AsyncSession,
    project_id: UUID,
    payload: dict[str, Any],
    snapshot: Any,
) -> tuple[str, list[str]]:
    created = 0
    conflicts: list[str] = []
    for item in payload.get("segments") or []:
        if not isinstance(item, dict):
            continue
        name = _as_str(item.get("segment_name") or item.get("segmentName"))
        if not name:
            continue
        existing = next(
            (a for a in snapshot.audience if a.segment_name and a.segment_name.lower() == name.lower()),
            None,
        )
        if existing:
            conflicts.append(f"Segmento già esistente: {name}")
            continue
        await bi_service.create_audience(
            session,
            project_id,
            BrandAudienceInsightCreate(segment_name=name, description=_as_str(item.get("description"))),
        )
        created += 1
    if conflicts and created == 0:
        return "", conflicts
    return f"Creati {created} segmenti audience.", conflicts if conflicts else []


async def _apply_claims(
    session: AsyncSession,
    project_id: UUID,
    payload: dict[str, Any],
    snapshot: Any,
) -> tuple[str, list[str]]:
    created = 0
    conflicts: list[str] = []
    mapping = {
        "allowed": "allowed",
        "forbidden": "forbidden",
        "caution": "caution",
        "disclaimers": "disclaimer",
    }
    existing_titles = {c.title.lower() for c in snapshot.claims if c.title}

    for key, rule_type in mapping.items():
        for item in payload.get(key) or []:
            if not isinstance(item, dict):
                continue
            title = _as_str(item.get("title"))
            if not title:
                continue
            if title.lower() in existing_titles:
                conflicts.append(f"Claim già esistente: {title}")
                continue
            severity = "critical" if rule_type == "forbidden" else "warning"
            await bi_service.create_claim(
                session,
                project_id,
                BrandClaimRuleCreate(
                    title=title,
                    description=_as_str(item.get("description")),
                    rule_type=rule_type,
                    severity=severity,
                ),
            )
            existing_titles.add(title.lower())
            created += 1

    if conflicts and created == 0:
        return "", conflicts
    return f"Creati {created} claim rules.", conflicts if conflicts else []


async def _apply_pillars(
    session: AsyncSession,
    project_id: UUID,
    payload: dict[str, Any],
    snapshot: Any,
) -> tuple[str, list[str]]:
    created = 0
    conflicts: list[str] = []
    existing = {p.name.lower() for p in snapshot.pillars if p.name}
    for item in payload.get("pillars") or []:
        if not isinstance(item, dict):
            continue
        name = _as_str(item.get("name"))
        if not name:
            continue
        if name.lower() in existing:
            conflicts.append(f"Pillar già esistente: {name}")
            continue
        await bi_service.create_pillar(
            session,
            project_id,
            BrandContentPillarCreate(name=name, description=_as_str(item.get("description"))),
        )
        existing.add(name.lower())
        created += 1
    if conflicts and created == 0:
        return "", conflicts
    return f"Creati {created} content pillars.", conflicts if conflicts else []


async def _apply_guardrails(
    session: AsyncSession,
    project_id: UUID,
    payload: dict[str, Any],
    snapshot: Any,
) -> tuple[str, list[str]]:
    created = 0
    conflicts: list[str] = []
    existing = {g.title.lower() for g in snapshot.guardrails if g.title}
    for item in payload.get("guardrails") or []:
        if not isinstance(item, dict):
            continue
        title = _as_str(item.get("title"))
        if not title:
            continue
        if title.lower() in existing:
            conflicts.append(f"Guardrail già esistente: {title}")
            continue
        rt = _as_str(item.get("rule_type") or item.get("ruleType")) or "must_not"
        if rt not in ("must", "must_not", "caution"):
            rt = "must_not"
        await bi_service.create_guardrail(
            session,
            project_id,
            BrandAiGuardrailCreate(
                title=title,
                description=_as_str(item.get("description")),
                rule_type=rt,
            ),
        )
        existing.add(title.lower())
        created += 1
    if conflicts and created == 0:
        return "", conflicts
    return f"Creati {created} guardrails.", conflicts if conflicts else []


async def _apply_assets(
    session: AsyncSession,
    project_id: UUID,
    payload: dict[str, Any],
    snapshot: Any,
) -> tuple[str, list[str]]:
    created = 0
    conflicts: list[str] = []
    existing = {a.name.lower() for a in snapshot.assets if a.name}
    for item in payload.get("assets") or []:
        if not isinstance(item, dict):
            continue
        name = _as_str(item.get("name"))
        if not name:
            continue
        if name.lower() in existing:
            conflicts.append(f"Asset già esistente: {name}")
            continue
        at = _as_str(item.get("asset_type") or item.get("assetType")) or "other"
        await bi_service.create_asset(
            session,
            project_id,
            BrandAssetCreate(
                name=name,
                value=_as_str(item.get("value")) or name,
                asset_type=at if at in ("logo", "color", "font", "image", "video", "document", "other") else "other",
            ),
        )
        existing.add(name.lower())
        created += 1
    if conflicts and created == 0:
        return "", conflicts
    return f"Creati {created} assets.", conflicts if conflicts else []
