"""Apply approved extracted facts to official Brand Intelligence tables."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brand_intelligence import BrandExtractedFact
from app.schemas.brand_intelligence import (
    BrandAiGuardrailCreate,
    BrandAssetCreate,
    BrandAudienceInsightCreate,
    BrandClaimRuleCreate,
    BrandContentPillarCreate,
    BrandProductKnowledgeCreate,
    BrandProfileUpdate,
    BrandSeoStrategyUpdate,
    BrandVoiceUpdate,
)
from app.services.brand_intelligence import service as bi_service

PROFILE_FIELDS = frozenset(
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
    }
)
VOICE_FIELDS = frozenset(
    {
        "tone",
        "style_notes",
        "formality_level",
        "emoji_policy",
        "words_to_use",
        "words_to_avoid",
        "examples_good",
        "examples_bad",
    }
)
SEO_FIELDS = frozenset(
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
    }
)


@dataclass
class ApplyResultItem:
    fact_id: UUID
    target_section: str
    field_name: str | None
    message: str


@dataclass
class ApplyResult:
    saved: list[ApplyResultItem] = field(default_factory=list)
    skipped: list[ApplyResultItem] = field(default_factory=list)
    needs_review: int = 0
    rejected: int = 0


def _as_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        s = value.strip()
        return s or None
    if isinstance(value, (int, float, bool)):
        return str(value)
    return None


def _as_list(value: Any) -> list[str] | None:
    if value is None:
        return None
    if isinstance(value, list):
        items = [str(v).strip() for v in value if str(v).strip()]
        return items or None
    if isinstance(value, str):
        if "," in value:
            items = [p.strip() for p in value.split(",") if p.strip()]
            return items or None
        s = value.strip()
        return [s] if s else None
    return None


async def apply_approved_facts(
    session: AsyncSession,
    project_id: UUID,
    fact_ids: list[UUID],
) -> ApplyResult:
    if not fact_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nessun fact da applicare.")

    facts = list(
        (
            await session.execute(
                select(BrandExtractedFact).where(
                    BrandExtractedFact.project_id == project_id,
                    BrandExtractedFact.id.in_(fact_ids),
                )
            )
        ).scalars().all()
    )
    if len(facts) != len(fact_ids):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Uno o più facts non trovati.")

    result = ApplyResult()
    profile_updates: dict[str, Any] = {}
    voice_updates: dict[str, Any] = {}
    seo_updates: dict[str, Any] = {}
    seo_keyword_append: list[str] = []

    for fact in facts:
        if fact.status == "rejected":
            result.rejected += 1
            result.skipped.append(
                ApplyResultItem(
                    fact.id,
                    fact.target_section,
                    fact.field_name,
                    "Fact rifiutato, non applicato.",
                )
            )
            continue
        if fact.status != "approved":
            result.needs_review += 1
            result.skipped.append(
                ApplyResultItem(
                    fact.id,
                    fact.target_section,
                    fact.field_name,
                    "Fact non approvato. Approva prima di applicare.",
                )
            )
            continue

        if getattr(fact, "update_mode", "create") == "duplicate_candidate":
            result.skipped.append(
                ApplyResultItem(
                    fact.id,
                    fact.target_section,
                    fact.field_name,
                    "Duplicato rilevato: nessuna modifica applicata.",
                )
            )
            fact.status = "needs_review"
            result.needs_review += 1
            continue

        applied = await _apply_single_fact(
            session,
            project_id,
            fact,
            profile_updates,
            voice_updates,
            seo_updates,
            seo_keyword_append,
        )
        if applied:
            result.saved.append(applied)
        else:
            fact.status = "needs_review"
            result.needs_review += 1
            result.skipped.append(
                ApplyResultItem(
                    fact.id,
                    fact.target_section,
                    fact.field_name,
                    "Fact non mappabile automaticamente.",
                )
            )

    if profile_updates:
        await bi_service.upsert_profile(session, project_id, BrandProfileUpdate(**profile_updates))
    if voice_updates:
        await bi_service.upsert_voice(session, project_id, BrandVoiceUpdate(**voice_updates))
    if seo_updates or seo_keyword_append:
        seo_row = await bi_service.get_seo_strategy(session, project_id)
        merged = dict(seo_updates)
        if seo_keyword_append:
            existing = list(seo_row.primary_keywords or [])
            for kw in seo_keyword_append:
                if kw not in existing:
                    existing.append(kw)
            merged["primary_keywords"] = existing
        await bi_service.upsert_seo_strategy(session, project_id, BrandSeoStrategyUpdate(**merged))

    await session.commit()
    return result


async def _apply_single_fact(
    session: AsyncSession,
    project_id: UUID,
    fact: BrandExtractedFact,
    profile_updates: dict[str, Any],
    voice_updates: dict[str, Any],
    seo_updates: dict[str, Any],
    seo_keyword_append: list[str],
) -> ApplyResultItem | None:
    section = fact.target_section
    field_name = fact.field_name
    value = fact.extracted_value

    if section == "unknown":
        return None

    if section == "brand_profile":
        if field_name and field_name in PROFILE_FIELDS:
            if getattr(fact, "update_mode", "create") == "enrich":
                profile = await bi_service.get_profile(session, project_id)
                existing = getattr(profile, field_name, None)
                if not _is_empty_official(existing):
                    return ApplyResultItem(
                        fact.id,
                        section,
                        field_name,
                        "Campo profilo già valorizzato; enrich saltato.",
                    )
            profile_updates[field_name] = _coerce_profile_field(field_name, value)
            return ApplyResultItem(fact.id, section, field_name, "Campo profilo aggiornato.")
        if not field_name:
            text = _as_str(value)
            if text:
                profile_updates["short_description"] = text
                return ApplyResultItem(fact.id, section, "short_description", "Descrizione profilo aggiornata.")
        return None

    if section == "voice_tone":
        if field_name and field_name in VOICE_FIELDS:
            if getattr(fact, "update_mode", "create") == "enrich":
                voice = await bi_service.get_voice(session, project_id)
                existing = getattr(voice, field_name, None)
                if not _is_empty_official(existing):
                    return ApplyResultItem(
                        fact.id,
                        section,
                        field_name,
                        "Campo voice già valorizzato; enrich saltato.",
                    )
            voice_updates[field_name] = _coerce_voice_field(field_name, value)
            return ApplyResultItem(fact.id, section, field_name, "Voice aggiornata.")
        if not field_name:
            text = _as_str(value)
            if text:
                voice_updates["tone"] = text
                return ApplyResultItem(fact.id, section, "tone", "Tono voice aggiornato.")
        return None

    if section == "product_knowledge":
        return await _apply_product_fact(session, project_id, fact, "product")

    if section == "category_knowledge":
        return await _apply_product_fact(session, project_id, fact, "category")

    if section == "audience":
        return await _apply_audience_fact(session, project_id, fact)

    if section == "claims_compliance":
        return await _apply_claim_fact(session, project_id, fact)

    if section == "seo_strategy":
        if field_name == "primary_keywords" or field_name is None:
            keywords = _as_list(value)
            if keywords:
                seo_keyword_append.extend(keywords)
                return ApplyResultItem(fact.id, section, "primary_keywords", "Keyword SEO aggiunte.")
        if field_name and field_name in SEO_FIELDS:
            if getattr(fact, "update_mode", "create") == "enrich":
                seo_row = await bi_service.get_seo_strategy(session, project_id)
                existing = getattr(seo_row, field_name, None)
                if not _is_empty_official(existing):
                    return ApplyResultItem(
                        fact.id,
                        section,
                        field_name,
                        "Campo SEO già valorizzato; enrich saltato.",
                    )
            seo_updates[field_name] = _coerce_seo_field(field_name, value)
            return ApplyResultItem(fact.id, section, field_name, "Strategia SEO aggiornata.")
        return None

    if section == "content_pillars":
        return await _apply_pillar_fact(session, project_id, fact)

    if section == "ai_guardrails":
        return await _apply_guardrail_fact(session, project_id, fact)

    if section == "assets":
        return await _apply_asset_fact(session, project_id, fact)

    return None


def _coerce_profile_field(field_name: str, value: Any) -> Any:
    if field_name in ("values", "differentiators"):
        return _as_list(value)
    return _as_str(value)


def _coerce_voice_field(field_name: str, value: Any) -> Any:
    if field_name in ("words_to_use", "words_to_avoid", "examples_good", "examples_bad"):
        return _as_list(value)
    return _as_str(value)


def _coerce_seo_field(field_name: str, value: Any) -> Any:
    if field_name in ("primary_keywords", "secondary_keywords", "priority_pages", "competitors"):
        return _as_list(value)
    return _as_str(value)


def _is_empty_official(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, list):
        return len(value) == 0
    if isinstance(value, str):
        return not value.strip()
    return False


async def _apply_product_fact(
    session: AsyncSession,
    project_id: UUID,
    fact: BrandExtractedFact,
    entity_type: str,
) -> ApplyResultItem | None:
    value = fact.extracted_value
    name: str | None = None
    description: str | None = None

    if isinstance(value, dict):
        name = _as_str(value.get("name") or value.get("product_name") or value.get("title"))
        description = _as_str(value.get("description") or value.get("desc"))
    elif fact.field_name == "name":
        name = _as_str(value)
    elif fact.field_name == "description":
        description = _as_str(value)
    else:
        text = _as_str(value)
        if text:
            if fact.field_name == "description":
                description = text
            else:
                name = text

    if not name and description:
        name = description[:120]
    if not name:
        return None
    if getattr(fact, "update_mode", "create") == "duplicate_candidate":
        return ApplyResultItem(
            fact.id,
            fact.target_section,
            fact.field_name,
            f"{'Prodotto' if entity_type == 'product' else 'Categoria'} già esistente: {name}",
        )
    if not description:
        description = _as_str(value) if not isinstance(value, dict) else None
    if not description:
        description = name

    await bi_service.create_product(
        session,
        project_id,
        BrandProductKnowledgeCreate(
            name=name,
            description=description,
            entity_type=entity_type,
        ),
    )
    return ApplyResultItem(
        fact.id,
        fact.target_section,
        fact.field_name,
        f"{'Prodotto' if entity_type == 'product' else 'Categoria'} creato: {name}",
    )


async def _apply_audience_fact(
    session: AsyncSession,
    project_id: UUID,
    fact: BrandExtractedFact,
) -> ApplyResultItem | None:
    value = fact.extracted_value
    segment_name: str | None = None
    description: str | None = None
    if isinstance(value, dict):
        segment_name = _as_str(value.get("segment_name") or value.get("name"))
        description = _as_str(value.get("description"))
    elif fact.field_name == "segment_name":
        segment_name = _as_str(value)
    else:
        segment_name = _as_str(value)
    if not segment_name:
        return None
    await bi_service.create_audience(
        session,
        project_id,
        BrandAudienceInsightCreate(segment_name=segment_name, description=description),
    )
    return ApplyResultItem(fact.id, fact.target_section, fact.field_name, f"Segmento audience creato: {segment_name}")


async def _apply_claim_fact(
    session: AsyncSession,
    project_id: UUID,
    fact: BrandExtractedFact,
) -> ApplyResultItem | None:
    value = fact.extracted_value
    title: str | None = None
    description: str | None = None
    rule_type = "caution"
    if fact.field_name == "rule_type" and _as_str(value) in ("forbidden", "caution", "allowed", "disclaimer"):
        rule_type = _as_str(value) or "caution"
    if isinstance(value, dict):
        title = _as_str(value.get("title") or value.get("claim"))
        description = _as_str(value.get("description"))
        rt = _as_str(value.get("rule_type"))
        if rt in ("forbidden", "caution", "allowed", "disclaimer"):
            rule_type = rt
    else:
        title = _as_str(value)
    if not title:
        return None
    severity = "critical" if rule_type == "forbidden" else "warning"
    await bi_service.create_claim(
        session,
        project_id,
        BrandClaimRuleCreate(
            title=title,
            description=description,
            rule_type=rule_type,
            severity=severity,
        ),
    )
    return ApplyResultItem(fact.id, fact.target_section, fact.field_name, f"Claim creato: {title}")


async def _apply_pillar_fact(
    session: AsyncSession,
    project_id: UUID,
    fact: BrandExtractedFact,
) -> ApplyResultItem | None:
    value = fact.extracted_value
    name: str | None = None
    description: str | None = None
    if isinstance(value, dict):
        name = _as_str(value.get("name") or value.get("pillar"))
        description = _as_str(value.get("description"))
    elif fact.field_name == "name":
        name = _as_str(value)
    else:
        name = _as_str(value)
    if not name:
        return None
    await bi_service.create_pillar(
        session,
        project_id,
        BrandContentPillarCreate(name=name, description=description),
    )
    return ApplyResultItem(fact.id, fact.target_section, fact.field_name, f"Content pillar creato: {name}")


async def _apply_guardrail_fact(
    session: AsyncSession,
    project_id: UUID,
    fact: BrandExtractedFact,
) -> ApplyResultItem | None:
    value = fact.extracted_value
    title: str | None = None
    description: str | None = None
    rule_type = "must_not"
    if isinstance(value, dict):
        title = _as_str(value.get("title") or value.get("rule"))
        description = _as_str(value.get("description"))
        rt = _as_str(value.get("rule_type"))
        if rt in ("must", "must_not", "caution"):
            rule_type = rt
    else:
        title = _as_str(value)
    if fact.field_name == "rule_type" and _as_str(value) in ("must", "must_not", "caution"):
        rule_type = _as_str(value) or "must_not"
    if not title:
        return None
    await bi_service.create_guardrail(
        session,
        project_id,
        BrandAiGuardrailCreate(title=title, description=description, rule_type=rule_type),
    )
    return ApplyResultItem(fact.id, fact.target_section, fact.field_name, f"Guardrail creato: {title}")


async def _apply_asset_fact(
    session: AsyncSession,
    project_id: UUID,
    fact: BrandExtractedFact,
) -> ApplyResultItem | None:
    value = fact.extracted_value
    name: str | None = None
    asset_value: str | None = None
    asset_type = "other"
    if isinstance(value, dict):
        name = _as_str(value.get("name"))
        asset_value = _as_str(value.get("value") or value.get("url"))
        at = _as_str(value.get("asset_type"))
        if at in ("logo", "color", "font", "image", "video", "document", "other"):
            asset_type = at
    else:
        name = _as_str(value)
        asset_value = name
    if not name:
        return None
    await bi_service.create_asset(
        session,
        project_id,
        BrandAssetCreate(name=name, value=asset_value, asset_type=asset_type),
    )
    return ApplyResultItem(fact.id, fact.target_section, fact.field_name, f"Asset creato: {name}")
