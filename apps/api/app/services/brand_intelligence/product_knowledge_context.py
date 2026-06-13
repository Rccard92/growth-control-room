"""Product Knowledge prompt helpers for BrandContextBuilder and Product SEO."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brand_intelligence import BrandProductKnowledgeGeneral, BrandProductKnowledgeItem
from app.schemas.brand_product_knowledge import (
    BrandProductKnowledgeContext,
    BrandProductKnowledgeGeneralRulesContext,
    BrandProductKnowledgeGeneralRead,
    BrandProductKnowledgeItemRead,
    BrandProductKnowledgeSpecificProductContext,
)
from app.services.brand_intelligence.product_knowledge_general_service import general_has_content


def build_product_knowledge_context(
    general: BrandProductKnowledgeGeneral | None,
    items: list[BrandProductKnowledgeItem],
) -> BrandProductKnowledgeContext | None:
    general_rules = None
    if general and general_has_content(general):
        general_rules = BrandProductKnowledgeGeneralRulesContext(
            general_principles=general.general_principles or [],
            common_strengths=general.common_strengths or [],
            quality_rules=general.common_quality_rules or [],
            production_notes=general.common_production_notes or [],
            usage_notes=general.common_usage_notes or [],
            common_objections=general.common_objections or [],
            common_faq=general.common_faq or [],
            communication_rules=general.communication_rules or [],
            storytelling_rules=general.product_storytelling_rules or [],
        )

    specific = [
        BrandProductKnowledgeSpecificProductContext(
            shopify_product_id=str(item.shopify_product_id) if item.shopify_product_id else None,
            shopify_gid=item.shopify_product_gid,
            title=item.shopify_title or item.product_name,
            handle=item.shopify_handle,
            product_line=item.product_line,
            strategic_description=item.strategic_description,
            origin=item.origin,
            ingredients=item.ingredients,
            usage_suggestions=item.usage_suggestions,
            faq=item.faq or [],
            allowed_claims=item.allowed_claims or [],
            forbidden_claims=item.forbidden_claims or [],
            seo_notes=item.seo_notes,
        )
        for item in items
    ]

    if not general_rules and not specific:
        return None

    return BrandProductKnowledgeContext(
        general_rules=general_rules,
        specific_products=specific,
    )


def format_general_for_prompt(general: BrandProductKnowledgeGeneralRead) -> str:
    parts: list[str] = ["PRODUCT KNOWLEDGE — GENERAL"]
    if general.general_principles:
        parts.append("Principi generali:")
        parts.extend(f"- {p}" for p in general.general_principles[:10])
    if general.common_strengths:
        parts.append("Punti di forza comuni:")
        parts.extend(f"- {s}" for s in general.common_strengths[:8])
    if general.common_quality_rules:
        parts.append("Regole qualità:")
        parts.extend(f"- {r}" for r in general.common_quality_rules[:8])
    if general.common_production_notes:
        parts.append("Note produzione:")
        parts.extend(f"- {n}" for n in general.common_production_notes[:6])
    if general.common_usage_notes:
        parts.append("Note uso:")
        parts.extend(f"- {n}" for n in general.common_usage_notes[:6])
    if general.common_objections:
        parts.append("Obiezioni comuni:")
        parts.extend(f"- {o}" for o in general.common_objections[:6])
    if general.common_faq:
        parts.append("FAQ comuni:")
        for entry in general.common_faq[:5]:
            if isinstance(entry, dict):
                q = entry.get("question", "")
                a = entry.get("answer", "")
                if q:
                    parts.append(f"- Q: {q} A: {a[:200]}")
    if general.communication_rules:
        parts.append("Regole comunicazione:")
        parts.extend(f"- {r}" for r in general.communication_rules[:6])
    if general.product_storytelling_rules:
        parts.append("Regole storytelling:")
        parts.extend(f"- {r}" for r in general.product_storytelling_rules[:6])
    if general.notes:
        parts.append(f"Note: {general.notes[:400]}")
    return "\n".join(parts)


def format_item_for_prompt(item: BrandProductKnowledgeItemRead) -> str:
    title = item.shopify_title or item.product_name
    parts: list[str] = [f"Prodotto: {title}"]
    if item.shopify_handle:
        parts.append(f"- Handle: {item.shopify_handle}")
    if item.product_line:
        parts.append(f"- Linea: {item.product_line}")
    if item.strategic_description:
        parts.append(f"- Descrizione strategica: {item.strategic_description[:400]}")
    if item.origin:
        parts.append(f"- Origine: {item.origin[:300]}")
    if item.ingredients:
        parts.append(f"- Ingredienti: {item.ingredients[:300]}")
    if item.production_process:
        parts.append(f"- Processo: {item.production_process[:300]}")
    if item.usage_suggestions:
        parts.append(f"- Uso consigliato: {item.usage_suggestions[:300]}")
    if item.allowed_claims:
        parts.append(f"- Claim consentiti: {', '.join(item.allowed_claims[:6])}")
    if item.forbidden_claims:
        parts.append(f"- Claim vietati: {', '.join(item.forbidden_claims[:6])}")
    if item.seo_notes:
        parts.append(f"- Note SEO: {item.seo_notes[:300]}")
    if item.faq:
        for entry in item.faq[:4]:
            if isinstance(entry, dict):
                q = entry.get("question", "")
                a = entry.get("answer", "")
                if q:
                    parts.append(f"- FAQ: {q} → {a[:150]}")
    return "\n".join(parts)


def format_items_for_prompt(items: list[BrandProductKnowledgeItemRead]) -> str | None:
    if not items:
        return None
    blocks = ["PRODUCT KNOWLEDGE — SPECIFIC PRODUCTS"]
    for item in items[:15]:
        block = format_item_for_prompt(item)
        if len(block.splitlines()) > 1:
            blocks.append(block)
    if len(blocks) == 1:
        return None
    return "\n\n".join(blocks)


async def get_product_knowledge_prompt_for_entity(
    session: AsyncSession,
    project_id: UUID,
    *,
    shopify_product_id: UUID | None = None,
) -> str | None:
    general = (
        await session.execute(
            select(BrandProductKnowledgeGeneral).where(
                BrandProductKnowledgeGeneral.project_id == project_id
            )
        )
    ).scalar_one_or_none()

    blocks: list[str] = []
    if general and general_has_content(general):
        general_read = BrandProductKnowledgeGeneralRead.model_validate(general)
        general_text = format_general_for_prompt(general_read)
        if len(general_text.splitlines()) > 1:
            blocks.append(general_text)

    if shopify_product_id is not None:
        item = (
            await session.execute(
                select(BrandProductKnowledgeItem).where(
                    BrandProductKnowledgeItem.project_id == project_id,
                    BrandProductKnowledgeItem.shopify_product_id == shopify_product_id,
                )
            )
        ).scalar_one_or_none()
        if item is not None:
            item_read = BrandProductKnowledgeItemRead.model_validate(item)
            item_text = format_item_for_prompt(item_read)
            if len(item_text.splitlines()) > 1:
                if not blocks:
                    blocks.append("PRODUCT KNOWLEDGE — SPECIFIC PRODUCTS")
                blocks.append(item_text)

    if not blocks:
        return None
    return "\n\n".join(blocks)
