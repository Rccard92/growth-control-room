"""Detect conflicts between extracted facts and official Brand Intelligence data."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brand_intelligence import (
    BrandAiGuardrail,
    BrandAsset,
    BrandAudienceInsight,
    BrandClaimRule,
    BrandContentPillar,
    BrandExtractedFact,
    BrandProductKnowledge,
    BrandProfile,
    BrandSeoStrategy,
    BrandVoice,
)

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
class OfficialSnapshot:
    profile: BrandProfile | None = None
    voice: BrandVoice | None = None
    seo: BrandSeoStrategy | None = None
    products: list[BrandProductKnowledge] = field(default_factory=list)
    categories: list[BrandProductKnowledge] = field(default_factory=list)
    audience: list[BrandAudienceInsight] = field(default_factory=list)
    claims: list[BrandClaimRule] = field(default_factory=list)
    pillars: list[BrandContentPillar] = field(default_factory=list)
    guardrails: list[BrandAiGuardrail] = field(default_factory=list)
    assets: list[BrandAsset] = field(default_factory=list)


def _as_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        s = value.strip()
        return s or None
    return str(value).strip() or None


def _normalize_name(value: Any) -> str | None:
    s = _as_str(value)
    return s.lower() if s else None


def _values_equal(a: Any, b: Any) -> bool:
    if a is None and b is None:
        return True
    if isinstance(a, list) and isinstance(b, list):
        return sorted(str(x) for x in a) == sorted(str(x) for x in b)
    return str(a).strip().lower() == str(b).strip().lower()


def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, list):
        return len(value) == 0
    if isinstance(value, str):
        return not value.strip()
    return False


def _serialize_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool, list, dict)):
        return value
    return str(value)


async def load_official_snapshot(session: AsyncSession, project_id: UUID) -> OfficialSnapshot:
    profile = (
        await session.execute(select(BrandProfile).where(BrandProfile.project_id == project_id))
    ).scalar_one_or_none()
    voice = (
        await session.execute(select(BrandVoice).where(BrandVoice.project_id == project_id))
    ).scalar_one_or_none()
    seo = (
        await session.execute(
            select(BrandSeoStrategy).where(BrandSeoStrategy.project_id == project_id)
        )
    ).scalar_one_or_none()
    products = list(
        (
            await session.execute(
                select(BrandProductKnowledge).where(
                    BrandProductKnowledge.project_id == project_id,
                    BrandProductKnowledge.entity_type == "product",
                )
            )
        ).scalars().all()
    )
    categories = list(
        (
            await session.execute(
                select(BrandProductKnowledge).where(
                    BrandProductKnowledge.project_id == project_id,
                    BrandProductKnowledge.entity_type == "category",
                )
            )
        ).scalars().all()
    )
    audience = list(
        (
            await session.execute(
                select(BrandAudienceInsight).where(BrandAudienceInsight.project_id == project_id)
            )
        ).scalars().all()
    )
    claims = list(
        (
            await session.execute(
                select(BrandClaimRule).where(BrandClaimRule.project_id == project_id)
            )
        ).scalars().all()
    )
    pillars = list(
        (
            await session.execute(
                select(BrandContentPillar).where(BrandContentPillar.project_id == project_id)
            )
        ).scalars().all()
    )
    guardrails = list(
        (
            await session.execute(
                select(BrandAiGuardrail).where(BrandAiGuardrail.project_id == project_id)
            )
        ).scalars().all()
    )
    assets = list(
        (
            await session.execute(
                select(BrandAsset).where(BrandAsset.project_id == project_id)
            )
        ).scalars().all()
    )
    return OfficialSnapshot(
        profile=profile,
        voice=voice,
        seo=seo,
        products=products,
        categories=categories,
        audience=audience,
        claims=claims,
        pillars=pillars,
        guardrails=guardrails,
        assets=assets,
    )


def build_bi_summary(snapshot: OfficialSnapshot) -> str:
    parts: list[str] = []
    if snapshot.profile:
        p = snapshot.profile
        if p.brand_name:
            parts.append(f"Brand: {p.brand_name}")
        if p.short_description:
            parts.append(f"Descrizione: {p.short_description[:200]}")
        if p.industry:
            parts.append(f"Settore: {p.industry}")
    if snapshot.voice and snapshot.voice.tone:
        parts.append(f"Tono: {snapshot.voice.tone}")
    if snapshot.products:
        names = [x.name for x in snapshot.products[:5] if x.name]
        if names:
            parts.append(f"Prodotti esistenti: {', '.join(names)}")
    if snapshot.categories:
        names = [x.name for x in snapshot.categories[:5] if x.name]
        if names:
            parts.append(f"Categorie esistenti: {', '.join(names)}")
    if snapshot.audience:
        names = [x.segment_name for x in snapshot.audience[:5] if x.segment_name]
        if names:
            parts.append(f"Audience: {', '.join(names)}")
    if snapshot.seo and snapshot.seo.primary_keywords:
        parts.append(f"Keyword SEO: {', '.join(snapshot.seo.primary_keywords[:10])}")
    return "\n".join(parts) if parts else "Nessun dato ufficiale Brand Intelligence presente."


def _extract_entity_name(fact: BrandExtractedFact) -> str | None:
    value = fact.extracted_value
    if isinstance(value, dict):
        for key in ("name", "product_name", "title", "segment_name", "pillar", "claim"):
            n = _normalize_name(value.get(key))
            if n:
                return n
    return _normalize_name(value)


def classify_fact_against_official(
    fact: BrandExtractedFact,
    snapshot: OfficialSnapshot,
) -> None:
    section = fact.target_section
    field_name = fact.field_name

    if section == "unknown":
        fact.update_mode = "unknown"
        fact.conflict_status = "none"
        fact.is_update_suggestion = False
        return

    if section == "brand_profile" and snapshot.profile:
        if field_name and field_name in PROFILE_FIELDS:
            existing = getattr(snapshot.profile, field_name, None)
            return _classify_scalar_field(fact, existing, field_name)
        if not field_name:
            existing = snapshot.profile.short_description
            return _classify_scalar_field(fact, existing, "short_description")
        fact.update_mode = "unknown"
        return

    if section == "voice_tone" and snapshot.voice:
        if field_name and field_name in VOICE_FIELDS:
            existing = getattr(snapshot.voice, field_name, None)
            return _classify_scalar_field(fact, existing, field_name)
        if not field_name:
            existing = snapshot.voice.tone
            return _classify_scalar_field(fact, existing, "tone")
        fact.update_mode = "unknown"
        return

    if section == "seo_strategy" and snapshot.seo:
        if field_name and field_name in SEO_FIELDS:
            existing = getattr(snapshot.seo, field_name, None)
            return _classify_scalar_field(fact, existing, field_name)
        if field_name is None or field_name == "primary_keywords":
            existing = snapshot.seo.primary_keywords
            return _classify_scalar_field(fact, existing, "primary_keywords")
        fact.update_mode = "unknown"
        return

    if section == "product_knowledge":
        return _classify_list_entity(fact, snapshot.products, name_attr="name")
    if section == "category_knowledge":
        return _classify_list_entity(fact, snapshot.categories, name_attr="name")
    if section == "audience":
        return _classify_list_entity(fact, snapshot.audience, name_attr="segment_name")
    if section == "claims_compliance":
        return _classify_list_entity(fact, snapshot.claims, name_attr="title")
    if section == "content_pillars":
        return _classify_list_entity(fact, snapshot.pillars, name_attr="name")
    if section == "ai_guardrails":
        return _classify_list_entity(fact, snapshot.guardrails, name_attr="title")
    if section == "assets":
        return _classify_list_entity(fact, snapshot.assets, name_attr="name")

    fact.update_mode = "create"
    fact.conflict_status = "none"
    fact.is_update_suggestion = False


def _classify_scalar_field(
    fact: BrandExtractedFact,
    existing: Any,
    field_name: str,
) -> None:
    if _is_empty(existing):
        fact.update_mode = "enrich"
        fact.conflict_status = "none"
        fact.is_update_suggestion = True
        fact.previous_value = None
        fact.field_name = fact.field_name or field_name
        if fact.status == "suggested":
            fact.status = "needs_review"
        return

    if _values_equal(existing, fact.extracted_value):
        fact.update_mode = "duplicate_candidate"
        fact.conflict_status = "none"
        fact.is_update_suggestion = True
        fact.previous_value = _serialize_value(existing)
        if fact.status == "suggested":
            fact.status = "needs_review"
        return

    fact.update_mode = "update"
    fact.conflict_status = "possible_conflict"
    fact.is_update_suggestion = True
    fact.previous_value = _serialize_value(existing)
    fact.field_name = fact.field_name or field_name
    fact.status = "needs_review"


def _classify_list_entity(
    fact: BrandExtractedFact,
    entities: list[Any],
    *,
    name_attr: str,
) -> None:
    name = _extract_entity_name(fact)
    if not name:
        fact.update_mode = "unknown"
        fact.conflict_status = "none"
        return

    for entity in entities:
        entity_name = _normalize_name(getattr(entity, name_attr, None))
        if entity_name and entity_name == name:
            fact.update_mode = "duplicate_candidate"
            fact.conflict_status = "none"
            fact.is_update_suggestion = True
            fact.existing_target_id = entity.id
            fact.previous_value = {
                name_attr: getattr(entity, name_attr, None),
                "description": getattr(entity, "description", None),
            }
            if fact.status == "suggested":
                fact.status = "needs_review"
            return

    fact.update_mode = "create"
    fact.conflict_status = "none"
    fact.is_update_suggestion = len(entities) > 0


async def apply_conflict_detection_to_facts(
    session: AsyncSession,
    project_id: UUID,
    facts: list[BrandExtractedFact],
) -> int:
    if not facts:
        return 0
    snapshot = await load_official_snapshot(session, project_id)
    conflicts = 0
    for fact in facts:
        classify_fact_against_official(fact, snapshot)
        if fact.conflict_status == "possible_conflict":
            conflicts += 1
    await session.commit()
    return conflicts


async def apply_conflict_detection_to_batch(
    session: AsyncSession,
    project_id: UUID,
    batch_id: UUID,
) -> int:
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
    return await apply_conflict_detection_to_facts(session, project_id, facts)
