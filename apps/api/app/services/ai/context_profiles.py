"""Centralized AI Context Profiles — compact brand context per task."""

from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_seo import ShopifyCollection
from app.models.shopify import ShopifyProduct
from app.schemas.brand_intelligence import (
    BrandContextBundleResponse,
    BrandKnowledgeScoreResponse,
)
from app.services.ai.ai_client import AiRequestMetadata
from app.services.brand_intelligence.context import BrandIntelligenceContextBuilder
from app.services.brand_intelligence.editorial_guidelines_service import (
    editorial_guidelines_completion,
)
from app.services.brand_intelligence.faq_objections_service import faq_objections_completion
from app.services.brand_intelligence.product_knowledge_context import (
    get_product_knowledge_prompt_for_entity,
)
from app.services.brand_intelligence.safe_claims_service import safe_claims_completion


class AiContextProfile(str, Enum):
    MINIMAL = "minimal"
    IMAGE_ALT = "image_alt"
    PRODUCT_SEO_FIELD = "product_seo_field"
    COLLECTION_SEO_FIELD = "collection_seo_field"
    PRODUCT_SEO_FULL = "product_seo_full"
    COLLECTION_SEO_FULL = "collection_seo_full"
    BLOG_BRIEF = "blog_brief"
    ARTICLE_DRAFT = "article_draft"
    EDITORIAL_IMAGE = "editorial_image"
    BRAND_IMPORT = "brand_import"
    COMPLIANCE_REVIEW = "compliance_review"
    SOCIAL_RESPONSE = "social_response"
    GENERIC = "generic"


CLAIM_RISK_PROFILES = frozenset(
    {
        AiContextProfile.PRODUCT_SEO_FIELD,
        AiContextProfile.COLLECTION_SEO_FIELD,
        AiContextProfile.PRODUCT_SEO_FULL,
        AiContextProfile.COLLECTION_SEO_FULL,
        AiContextProfile.BLOG_BRIEF,
        AiContextProfile.ARTICLE_DRAFT,
        AiContextProfile.EDITORIAL_IMAGE,
        AiContextProfile.COMPLIANCE_REVIEW,
    }
)


class AiContextResult(BaseModel):
    profile: str
    context_text: str = Field(serialization_alias="contextText")
    context_blocks_used: list[str] = Field(serialization_alias="contextBlocksUsed")
    estimated_chars: int = Field(serialization_alias="estimatedChars")
    warnings: list[str] = Field(default_factory=list)
    context_hash: str = Field(serialization_alias="contextHash")

    model_config = {"populate_by_name": True}


def hash_context(text: str | None) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()[:16]


def build_prompt_cache_key(
    project_id: UUID,
    module: str,
    context_hash: str,
) -> str:
    return f"project:{project_id}:ctx:{context_hash}:module:{module}"


def enrich_ai_metadata(metadata: AiRequestMetadata, ctx: AiContextResult) -> AiRequestMetadata:
    return metadata.model_copy(
        update={
            "context_profile": ctx.profile,
            "context_hash": ctx.context_hash,
            "context_chars": ctx.estimated_chars,
            "context_blocks_used": ctx.context_blocks_used,
        }
    )


def _join_blocks(blocks: list[str | None]) -> str:
    parts = [b.strip() for b in blocks if b and b.strip()]
    return "\n\n".join(parts)


def _empty_knowledge_score() -> BrandKnowledgeScoreResponse:
    return BrandKnowledgeScoreResponse.model_validate(
        {
            "overall_score": 0,
            "status": "incomplete",
            "section_scores": {},
            "missing_required": [],
            "recommendations": [],
        }
    )


def _compact_profile(bundle: BrandContextBundleResponse) -> str | None:
    if not bundle.profile:
        return None
    p = bundle.profile
    parts: list[str] = ["BRAND PROFILE"]
    brand_name = getattr(p, "brand_name", None)
    if brand_name:
        parts.append(f"- Nome: {brand_name}")
    short_description = getattr(p, "short_description", None)
    if short_description:
        parts.append(f"- Descrizione: {short_description[:300]}")
    mission = getattr(p, "mission", None)
    if mission:
        parts.append(f"- Missione: {mission[:200]}")
    values = getattr(p, "values", None)
    if values:
        parts.append(f"- Valori: {', '.join(values[:5])}")
    return "\n".join(parts) if len(parts) > 1 else None


def _compact_identity(bundle: BrandContextBundleResponse) -> str | None:
    if not bundle.brand_identity:
        return None
    identity = bundle.brand_identity
    parts: list[str] = ["BRAND IDENTITY"]
    if identity.positioning:
        parts.append(f"- Posizionamento: {identity.positioning[:300]}")
    if identity.what_brand_is:
        parts.append(f"- Il brand è: {identity.what_brand_is[:250]}")
    if identity.what_brand_is_not:
        parts.append(f"- Il brand NON è: {identity.what_brand_is_not[:250]}")
    if identity.storytelling_notes:
        parts.append(f"- Storytelling: {identity.storytelling_notes[:200]}")
    return "\n".join(parts) if len(parts) > 1 else None


def _compact_visual(bundle: BrandContextBundleResponse) -> str | None:
    if not bundle.visual_identity:
        return None
    visual = bundle.visual_identity
    parts: list[str] = ["VISUAL IDENTITY"]
    if visual.image_style_notes:
        parts.append(f"- Stile immagini: {visual.image_style_notes[:200]}")
    if visual.visual_style_notes:
        parts.append(f"- Stile visuale: {visual.visual_style_notes[:150]}")
    if visual.do_show:
        parts.append(f"- Mostrare: {', '.join(visual.do_show[:4])}")
    if visual.do_not_show:
        parts.append(f"- Evitare: {', '.join(visual.do_not_show[:4])}")
    return "\n".join(parts) if len(parts) > 1 else None


def _compact_tone(bundle: BrandContextBundleResponse) -> str | None:
    if not bundle.editorial_guidelines:
        return None
    row = bundle.editorial_guidelines
    parts: list[str] = ["TONO"]
    if row.content_philosophy:
        parts.append(f"- Filosofia: {row.content_philosophy[:200]}")
    if row.reading_style:
        parts.append(f"- Stile lettura: {row.reading_style[:150]}")
    voice_rules = row.author_voice_rules or []
    if voice_rules:
        parts.append("Regole voce:")
        parts.extend(f"- {r[:120]}" for r in voice_rules[:3] if r)
    return "\n".join(parts) if len(parts) > 1 else None


def _essential_safe_claims(bundle: BrandContextBundleResponse) -> str | None:
    if not bundle.safe_claims or safe_claims_completion(bundle.safe_claims) == "empty":
        return None
    sc = bundle.safe_claims
    parts: list[str] = ["SAFE CLAIMS"]
    if sc.allowed_claims:
        parts.append("Consentiti:")
        parts.extend(f"- {c}" for c in sc.allowed_claims[:8])
    if sc.forbidden_claims:
        parts.append("Vietati:")
        parts.extend(f"- {c}" for c in sc.forbidden_claims[:8])
    if sc.caution_claims:
        parts.append("Con cautela:")
        parts.extend(f"- {c}" for c in sc.caution_claims[:6])
    if sc.tone_red_flags:
        parts.append("Red flags tono:")
        parts.extend(f"- {f}" for f in sc.tone_red_flags[:6])
    return "\n".join(parts) if len(parts) > 1 else None


def _full_safe_claims(bundle: BrandContextBundleResponse) -> str | None:
    if not bundle.safe_claims or safe_claims_completion(bundle.safe_claims) == "empty":
        return None
    return BrandIntelligenceContextBuilder.format_safe_claims_for_prompt(bundle.safe_claims)


def _compact_product_knowledge_general(bundle: BrandContextBundleResponse, *, max_lines: int = 12) -> str | None:
    pc = bundle.prompt_context
    if pc and pc.product_knowledge:
        lines = [ln for ln in pc.product_knowledge.splitlines() if ln.strip()]
        if len(lines) <= max_lines + 2:
            return pc.product_knowledge
        header = lines[0] if lines else "PRODUCT KNOWLEDGE"
        body = lines[1 : max_lines + 1]
        return "\n".join([header, *body, "[... product knowledge troncato ...]"])
    if bundle.product_knowledge and bundle.product_knowledge.general_rules:
        gr = bundle.product_knowledge.general_rules
        parts: list[str] = ["PRODUCT KNOWLEDGE — GENERAL"]
        if gr.general_principles:
            parts.append("Principi:")
            parts.extend(f"- {p}" for p in gr.general_principles[:4])
        if gr.common_strengths:
            parts.append("Punti di forza:")
            parts.extend(f"- {s}" for s in gr.common_strengths[:3])
        if gr.communication_rules:
            parts.append("Comunicazione:")
            parts.extend(f"- {r}" for r in gr.communication_rules[:3])
        return "\n".join(parts) if len(parts) > 1 else None
    return None


def _editorial_guidelines_block(bundle: BrandContextBundleResponse) -> str | None:
    guidelines = getattr(bundle, "editorial_guidelines", None)
    if not guidelines:
        return None
    if editorial_guidelines_completion(guidelines) == "empty":
        return None
    return BrandIntelligenceContextBuilder.format_editorial_guidelines_for_prompt(
        guidelines
    )


def _faq_block(bundle: BrandContextBundleResponse, *, filter_terms: list[str] | None = None) -> str | None:
    if not bundle.faq_objections:
        return None
    if faq_objections_completion(bundle.faq_objections) == "empty":
        return None
    full = BrandIntelligenceContextBuilder.format_faq_objections_for_prompt(bundle.faq_objections)
    if not full:
        return None
    if not filter_terms:
        return full
    terms = [t.lower() for t in filter_terms if t and t.strip()]
    if not terms:
        return full
    lines = full.splitlines()
    matched: list[str] = [lines[0]] if lines else ["FAQ & OBJECTIONS"]
    for line in lines[1:]:
        low = line.lower()
        if any(term in low for term in terms):
            matched.append(line)
    return "\n".join(matched) if len(matched) > 1 else None


def _format_brief_payload_block(brief_payload: dict[str, Any]) -> str:
    from app.services.content.editorial_structure_utils import (
        coerce_h2_h3_structure,
        format_h2_h3_for_prompt,
    )

    parts: list[str] = ["BRIEF APPROVATO"]
    mapping = [
        ("proposedTitle", "Titolo proposto"),
        ("primaryKeyword", "Keyword principale"),
        ("searchIntent", "Search intent"),
        ("targetAudience", "Audience"),
        ("contentAngle", "Angolo contenuto"),
        ("recommendedCta", "CTA consigliata"),
        ("metaTitle", "Meta title"),
        ("metaDescription", "Meta description"),
        ("authorSuggestion", "Autore suggerito"),
        ("contentLengthProfile", "Lunghezza"),
        ("structureComplexity", "Complessità struttura"),
    ]
    for key, label in mapping:
        val = brief_payload.get(key) or brief_payload.get(
            key[0].lower() + key[1:] if key[0].isupper() else key
        )
        if val and str(val).strip():
            parts.append(f"- {label}: {str(val).strip()[:400]}")
    word_min = brief_payload.get("recommendedWordCountMin")
    word_max = brief_payload.get("recommendedWordCountMax")
    if word_min or word_max:
        parts.append(f"- Parole consigliate: {word_min or '—'}-{word_max or '—'}")
    max_h2 = brief_payload.get("maxH2")
    max_h3 = brief_payload.get("maxH3")
    if max_h2 or max_h3:
        parts.append(f"- Max struttura: {max_h2 or '—'} H2, {max_h3 or '—'} H3")
    h2_raw = brief_payload.get("h2H3Structure")
    if h2_raw:
        sections = coerce_h2_h3_structure(h2_raw)
        if sections:
            parts.append("Struttura H2/H3:")
            parts.append(format_h2_h3_for_prompt(sections))
    for list_key, label in [
        ("secondaryKeywords", "Keyword secondarie"),
        ("productsToLink", "Prodotti da linkare"),
        ("faqToInclude", "FAQ da includere"),
        ("safeClaimsToUse", "Safe claims da usare"),
        ("claimsToAvoid", "Claim da evitare"),
        ("internalLinksSuggestions", "Link interni"),
        ("editorialToneNotes", "Note tono"),
        ("avoidRepetitions", "Evita ripetizioni"),
    ]:
        items = brief_payload.get(list_key)
        if isinstance(items, list) and items:
            parts.append(f"{label}:")
            parts.extend(f"  - {str(i)[:200]}" for i in items[:12] if i)
    notes = brief_payload.get("notes")
    if notes and str(notes).strip():
        parts.append(f"Note: {str(notes).strip()[:500]}")
    return "\n".join(parts)


async def _load_shopify_product(
    session: AsyncSession,
    entity_id: str | UUID,
) -> ShopifyProduct | None:
    try:
        pid = UUID(str(entity_id))
    except ValueError:
        return None
    return (
        await session.execute(select(ShopifyProduct).where(ShopifyProduct.id == pid))
    ).scalar_one_or_none()


async def _load_shopify_collection(
    session: AsyncSession,
    entity_id: str | UUID,
) -> ShopifyCollection | None:
    try:
        cid = UUID(str(entity_id))
    except ValueError:
        return None
    return (
        await session.execute(select(ShopifyCollection).where(ShopifyCollection.id == cid))
    ).scalar_one_or_none()


def _product_entity_block(product: ShopifyProduct) -> str:
    parts: list[str] = ["ENTITY — PRODUCT"]
    parts.append(f"- Titolo: {product.title}")
    if product.handle:
        parts.append(f"- Handle: {product.handle}")
    if product.vendor:
        parts.append(f"- Vendor: {product.vendor}")
    if product.product_type:
        parts.append(f"- Tipo: {product.product_type}")
    if product.description_text:
        parts.append(f"- Descrizione: {product.description_text[:400]}")
    return "\n".join(parts)


def _collection_entity_block(collection: ShopifyCollection) -> str:
    parts: list[str] = ["ENTITY — COLLECTION"]
    parts.append(f"- Titolo: {collection.title}")
    if collection.handle:
        parts.append(f"- Handle: {collection.handle}")
    if collection.description_text:
        parts.append(f"- Descrizione: {collection.description_text[:500]}")
    if collection.products_count is not None:
        parts.append(f"- Prodotti in collection: {collection.products_count}")
    raw = collection.raw_payload or {}
    products = raw.get("products") or raw.get("productTitles")
    if isinstance(products, list) and products:
        titles = [str(p.get("title", p) if isinstance(p, dict) else p) for p in products[:8]]
        titles = [t for t in titles if t]
        if titles:
            parts.append(f"- Prodotti principali: {', '.join(titles)}")
    return "\n".join(parts)


def _editorial_item_block(item: dict[str, Any]) -> str:
    parts: list[str] = ["EDITORIAL ITEM"]
    for key, label in [
        ("title", "Titolo"),
        ("content_type", "Tipo contenuto"),
        ("primary_keyword", "Keyword"),
        ("content_angle", "Angolo"),
        ("notes", "Note"),
    ]:
        val = item.get(key)
        if val and str(val).strip():
            parts.append(f"- {label}: {str(val).strip()[:300]}")
    return "\n".join(parts) if len(parts) > 1 else ""


def _brand_import_block(options: dict[str, Any]) -> str:
    parts: list[str] = ["BRAND IMPORT CONTEXT"]
    section = options.get("brand_import_section")
    if section:
        parts.append(f"Sezione target: {section}")
    schema = options.get("brand_import_schema")
    if schema:
        parts.append(f"Schema target:\n{schema}")
    instructions = options.get("brand_import_instructions")
    if instructions:
        parts.append(f"Istruzioni estrazione:\n{instructions}")
    existing = options.get("brand_import_existing")
    if existing:
        if isinstance(existing, dict):
            parts.append(
                "Sezioni esistenti (evita duplicati):\n"
                + json.dumps(existing, ensure_ascii=False, indent=0)[:4000]
            )
        else:
            parts.append(f"Dati esistenti:\n{str(existing)[:4000]}")
    snapshot = options.get("brand_import_snapshot")
    if snapshot:
        parts.append(f"Snapshot BI compatto:\n{str(snapshot)[:3000]}")
    return "\n".join(parts)


def _track_block(
    blocks: list[str | None],
    used: list[str],
    key: str,
    text: str | None,
    *,
    missing_warning: str | None = None,
    warnings: list[str],
) -> None:
    if text and text.strip():
        blocks.append(text)
        used.append(key)
    elif missing_warning:
        warnings.append(missing_warning)


async def _assemble_profile_blocks(
    session: AsyncSession,
    project_id: UUID,
    profile: AiContextProfile,
    bundle: BrandContextBundleResponse,
    entity_type: str | None,
    entity_id: str | None,
    options: dict[str, Any] | None,
) -> tuple[list[str | None], list[str], list[str]]:
    opts = options or {}
    blocks: list[str | None] = []
    used: list[str] = []
    warnings: list[str] = []

    shopify_product_id: UUID | None = None
    if opts.get("shopify_product_id"):
        try:
            shopify_product_id = UUID(str(opts["shopify_product_id"]))
        except ValueError:
            pass
    elif entity_type == "product" and entity_id:
        try:
            shopify_product_id = UUID(str(entity_id))
        except ValueError:
            pass

    if profile == AiContextProfile.MINIMAL:
        _track_block(blocks, used, "brand_profile", _compact_profile(bundle), warnings=warnings)
        _track_block(blocks, used, "tone", _compact_tone(bundle), warnings=warnings)
        _track_block(
            blocks,
            used,
            "safe_claims",
            _essential_safe_claims(bundle),
            missing_warning="Safe Claims missing",
            warnings=warnings,
        )

    elif profile == AiContextProfile.IMAGE_ALT:
        _track_block(blocks, used, "brand_profile", _compact_profile(bundle), warnings=warnings)
        _track_block(blocks, used, "visual_identity", _compact_visual(bundle), warnings=warnings)
        _track_block(blocks, used, "tone", _compact_tone(bundle), warnings=warnings)
        _track_block(
            blocks,
            used,
            "safe_claims",
            _essential_safe_claims(bundle),
            missing_warning="Safe Claims missing",
            warnings=warnings,
        )
        if entity_type == "product" and entity_id:
            product = await _load_shopify_product(session, entity_id)
            if product:
                blocks.append(_product_entity_block(product))
                used.append("entity_product")
        elif entity_type == "collection" and entity_id:
            collection = await _load_shopify_collection(session, entity_id)
            if collection:
                blocks.append(_collection_entity_block(collection))
                used.append("entity_collection")
        elif opts.get("entity_title"):
            blocks.append(f"ENTITY\n- Titolo: {opts['entity_title']}")
            used.append("entity_title")

    elif profile == AiContextProfile.PRODUCT_SEO_FIELD:
        _track_block(blocks, used, "brand_profile", _compact_profile(bundle), warnings=warnings)
        _track_block(blocks, used, "brand_identity", _compact_identity(bundle), warnings=warnings)
        _track_block(blocks, used, "tone", _compact_tone(bundle), warnings=warnings)
        _track_block(
            blocks,
            used,
            "safe_claims",
            _essential_safe_claims(bundle),
            missing_warning="Safe Claims missing",
            warnings=warnings,
        )
        _track_block(
            blocks,
            used,
            "product_knowledge_general",
            _compact_product_knowledge_general(bundle, max_lines=8),
            missing_warning="Product Knowledge missing",
            warnings=warnings,
        )
        if shopify_product_id:
            pk = await get_product_knowledge_prompt_for_entity(
                session, project_id, shopify_product_id=shopify_product_id
            )
            if pk:
                blocks.append(pk)
                used.append("product_knowledge_specific")
        if entity_type == "product" and entity_id:
            product = await _load_shopify_product(session, entity_id)
            if product:
                blocks.append(_product_entity_block(product))
                used.append("entity_product")

    elif profile == AiContextProfile.COLLECTION_SEO_FIELD:
        _track_block(blocks, used, "brand_profile", _compact_profile(bundle), warnings=warnings)
        _track_block(blocks, used, "brand_identity", _compact_identity(bundle), warnings=warnings)
        _track_block(blocks, used, "tone", _compact_tone(bundle), warnings=warnings)
        _track_block(
            blocks,
            used,
            "safe_claims",
            _essential_safe_claims(bundle),
            missing_warning="Safe Claims missing",
            warnings=warnings,
        )
        _track_block(
            blocks,
            used,
            "product_knowledge_general",
            _compact_product_knowledge_general(bundle, max_lines=8),
            missing_warning="Product Knowledge missing",
            warnings=warnings,
        )
        if entity_type == "collection" and entity_id:
            collection = await _load_shopify_collection(session, entity_id)
            if collection:
                blocks.append(_collection_entity_block(collection))
                used.append("entity_collection")

    elif profile == AiContextProfile.PRODUCT_SEO_FULL:
        _track_block(blocks, used, "brand_profile", _compact_profile(bundle), warnings=warnings)
        _track_block(blocks, used, "brand_identity", _compact_identity(bundle), warnings=warnings)
        _track_block(
            blocks,
            used,
            "safe_claims",
            _full_safe_claims(bundle),
            missing_warning="Safe Claims missing",
            warnings=warnings,
        )
        _track_block(
            blocks,
            used,
            "product_knowledge_general",
            _compact_product_knowledge_general(bundle, max_lines=15),
            missing_warning="Product Knowledge missing",
            warnings=warnings,
        )
        if shopify_product_id:
            pk = await get_product_knowledge_prompt_for_entity(
                session, project_id, shopify_product_id=shopify_product_id
            )
            if pk:
                blocks.append(pk)
                used.append("product_knowledge_specific")
        faq = _faq_block(bundle)
        if faq:
            blocks.append(faq)
            used.append("faq_objections")
        if entity_type == "product" and entity_id:
            product = await _load_shopify_product(session, entity_id)
            if product:
                blocks.append(_product_entity_block(product))
                used.append("entity_product")

    elif profile == AiContextProfile.COLLECTION_SEO_FULL:
        _track_block(blocks, used, "brand_profile", _compact_profile(bundle), warnings=warnings)
        _track_block(blocks, used, "brand_identity", _compact_identity(bundle), warnings=warnings)
        _track_block(
            blocks,
            used,
            "safe_claims",
            _full_safe_claims(bundle),
            missing_warning="Safe Claims missing",
            warnings=warnings,
        )
        _track_block(
            blocks,
            used,
            "product_knowledge_general",
            _compact_product_knowledge_general(bundle, max_lines=12),
            missing_warning="Product Knowledge missing",
            warnings=warnings,
        )
        faq = _faq_block(bundle)
        if faq:
            blocks.append(faq)
            used.append("faq_objections")
        if entity_type == "collection" and entity_id:
            collection = await _load_shopify_collection(session, entity_id)
            if collection:
                blocks.append(_collection_entity_block(collection))
                used.append("entity_collection")

    elif profile == AiContextProfile.BLOG_BRIEF:
        _track_block(
            blocks,
            used,
            "brand_profile",
            _compact_profile(bundle),
            warnings=warnings,
        )
        _track_block(blocks, used, "brand_identity", _compact_identity(bundle), warnings=warnings)
        _track_block(
            blocks,
            used,
            "safe_claims",
            _full_safe_claims(bundle),
            missing_warning="Safe Claims missing",
            warnings=warnings,
        )
        if shopify_product_id:
            pk = await get_product_knowledge_prompt_for_entity(
                session, project_id, shopify_product_id=shopify_product_id
            )
            if pk:
                blocks.append(pk)
                used.append("product_knowledge_specific")
        else:
            pk_gen = _compact_product_knowledge_general(bundle, max_lines=12)
            _track_block(
                blocks,
                used,
                "product_knowledge_general",
                pk_gen,
                missing_warning="Product Knowledge missing",
                warnings=warnings,
            )
        faq = _faq_block(bundle)
        if faq:
            blocks.append(faq)
            used.append("faq_objections")
        editorial = _editorial_guidelines_block(bundle)
        _track_block(
            blocks,
            used,
            "editorial_guidelines",
            editorial,
            missing_warning="Editorial Guidelines missing",
            warnings=warnings,
        )
        editorial_item = opts.get("editorial_item")
        if isinstance(editorial_item, dict):
            item_block = _editorial_item_block(editorial_item)
            if item_block:
                blocks.append(item_block)
                used.append("editorial_item")

    elif profile == AiContextProfile.ARTICLE_DRAFT:
        brief_payload = opts.get("brief_payload")
        if isinstance(brief_payload, dict) and brief_payload:
            blocks.append(_format_brief_payload_block(brief_payload))
            used.append("approved_brief")
        else:
            warnings.append("Approved brief missing")
        editorial = _editorial_guidelines_block(bundle)
        _track_block(
            blocks,
            used,
            "editorial_guidelines",
            editorial,
            missing_warning="Editorial Guidelines missing",
            warnings=warnings,
        )
        _track_block(
            blocks,
            used,
            "safe_claims",
            _full_safe_claims(bundle),
            missing_warning="Safe Claims missing",
            warnings=warnings,
        )
        faq_filter: list[str] = []
        if isinstance(brief_payload, dict):
            faq_filter = list(brief_payload.get("faqToInclude") or brief_payload.get("faq_to_include") or [])
        faq = _faq_block(bundle, filter_terms=faq_filter if faq_filter else None)
        if faq and faq_filter:
            blocks.append(faq)
            used.append("faq_selected")
        if shopify_product_id:
            pk = await get_product_knowledge_prompt_for_entity(
                session, project_id, shopify_product_id=shopify_product_id
            )
            if pk:
                blocks.append(pk)
                used.append("product_knowledge_specific")

    elif profile == AiContextProfile.EDITORIAL_IMAGE:
        brief_payload = opts.get("brief_payload")
        if isinstance(brief_payload, dict) and brief_payload:
            blocks.append(_format_brief_payload_block(brief_payload))
            used.append("approved_brief")
        article_summary = opts.get("article_summary")
        if article_summary:
            blocks.append(f"ARTICOLO\n{str(article_summary)[:2000]}")
            used.append("article_summary")
        editorial = _editorial_guidelines_block(bundle)
        _track_block(
            blocks,
            used,
            "editorial_guidelines",
            editorial,
            missing_warning="Editorial Guidelines missing",
            warnings=warnings,
        )
        _track_block(
            blocks,
            used,
            "safe_claims",
            _full_safe_claims(bundle),
            missing_warning="Safe Claims missing",
            warnings=warnings,
        )
        if bundle.visual_identity:
            from app.services.brand_intelligence.context import BrandIntelligenceContextBuilder

            visual_text = BrandIntelligenceContextBuilder.format_visual_for_prompt(
                bundle.visual_identity
            )
            if visual_text and len(visual_text.splitlines()) > 1:
                blocks.append(visual_text)
                used.append("visual_identity")
        editorial_item = opts.get("editorial_item")
        if isinstance(editorial_item, dict):
            item_block = _editorial_item_block(editorial_item)
            if item_block:
                blocks.append(item_block)
                used.append("editorial_item")
        if shopify_product_id:
            pk = await get_product_knowledge_prompt_for_entity(
                session, project_id, shopify_product_id=shopify_product_id
            )
            if pk:
                blocks.append(pk)
                used.append("product_knowledge_specific")
        linked_products = opts.get("linked_products")
        if isinstance(linked_products, list) and linked_products:
            titles = [str(p).strip() for p in linked_products if str(p).strip()]
            if titles:
                blocks.append(f"PRODOTTI COLLEGATI\n- {', '.join(titles[:8])}")
                used.append("linked_products")
        linked_collections = opts.get("linked_collections")
        if isinstance(linked_collections, list) and linked_collections:
            titles = [str(c).strip() for c in linked_collections if str(c).strip()]
            if titles:
                blocks.append(f"COLLEZIONI COLLEGATE\n- {', '.join(titles[:8])}")
                used.append("linked_collections")

    elif profile == AiContextProfile.BRAND_IMPORT:
        import_block = _brand_import_block(opts)
        blocks.append(import_block)
        used.append("brand_import_schema")

    elif profile == AiContextProfile.COMPLIANCE_REVIEW:
        _track_block(
            blocks,
            used,
            "safe_claims",
            _full_safe_claims(bundle),
            missing_warning="Safe Claims missing",
            warnings=warnings,
        )
        text_review = opts.get("text_to_review")
        if text_review:
            blocks.append(f"TESTO DA VALUTARE\n{str(text_review)[:8000]}")
            used.append("text_to_review")

    elif profile == AiContextProfile.SOCIAL_RESPONSE:
        _track_block(blocks, used, "brand_profile", _compact_profile(bundle), warnings=warnings)
        _track_block(blocks, used, "tone", _compact_tone(bundle), warnings=warnings)
        _track_block(
            blocks,
            used,
            "safe_claims",
            _essential_safe_claims(bundle),
            warnings=warnings,
        )

    else:  # GENERIC
        _track_block(blocks, used, "brand_profile", _compact_profile(bundle), warnings=warnings)
        _track_block(blocks, used, "brand_identity", _compact_identity(bundle), warnings=warnings)
        _track_block(
            blocks,
            used,
            "safe_claims",
            _essential_safe_claims(bundle),
            warnings=warnings,
        )

    return blocks, used, warnings


async def brand_import_metadata(
    session: AsyncSession,
    project_id: UUID,
    base: AiRequestMetadata,
    *,
    section: str | None = None,
    schema: str | None = None,
    instructions: str | None = None,
    snapshot: str | None = None,
    existing: Any = None,
) -> tuple[AiRequestMetadata, AiContextResult]:
    """Build brand_import context and enrich metadata for BI import/extraction calls."""
    options: dict[str, Any] = {}
    if section:
        options["brand_import_section"] = section
    if schema:
        options["brand_import_schema"] = schema
    if instructions:
        options["brand_import_instructions"] = instructions
    if snapshot:
        options["brand_import_snapshot"] = snapshot
    if existing is not None:
        options["brand_import_existing"] = existing
    ctx = await build_context_for_profile(
        session,
        project_id,
        AiContextProfile.BRAND_IMPORT,
        options=options or None,
    )
    return enrich_ai_metadata(base, ctx), ctx


async def minimal_metadata(
    session: AsyncSession,
    project_id: UUID,
    base: AiRequestMetadata,
) -> tuple[AiRequestMetadata, AiContextResult]:
    ctx = await build_context_for_profile(session, project_id, AiContextProfile.MINIMAL)
    return enrich_ai_metadata(base, ctx), ctx


async def build_context_for_profile(
    session: AsyncSession,
    project_id: UUID,
    profile: AiContextProfile,
    *,
    entity_type: str | None = None,
    entity_id: str | None = None,
    options: dict[str, Any] | None = None,
) -> AiContextResult:
    if profile == AiContextProfile.BRAND_IMPORT:
        bundle = BrandContextBundleResponse(
            primary_source="minimal",
            missing_context=[],
            knowledge_score=_empty_knowledge_score(),
        )
    else:
        bundle = await BrandIntelligenceContextBuilder.build_brand_context(session, project_id)
    profile_blocks, blocks_used, warnings = await _assemble_profile_blocks(
        session,
        project_id,
        profile,
        bundle,
        entity_type,
        entity_id,
        options,
    )

    header = f"CONTEXT PROFILE: {profile.value}"
    body = _join_blocks(profile_blocks)
    context_text = f"{header}\n\n{body}" if body else header
    context_hash = hash_context(context_text)

    if profile in CLAIM_RISK_PROFILES and "safe_claims" not in blocks_used:
        if "Safe Claims missing" not in warnings:
            warnings.append("Safe Claims missing")

    return AiContextResult(
        profile=profile.value,
        context_text=context_text,
        context_blocks_used=blocks_used,
        estimated_chars=len(context_text),
        warnings=warnings,
        context_hash=context_hash,
    )
