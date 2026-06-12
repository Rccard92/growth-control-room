from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.content_seo import ShopifyCollection
from app.models.seo_optimizer import SeoEntityAnalysis, SeoOptimizationProposal
from app.models.shopify import ShopifyProduct, ShopifyStore
from app.services.ai.openai_client import (
    OpenAINotConfiguredError,
    OpenAIRequestError,
    generate_structured_json,
    is_openai_configured,
)

SKILL_DIR = Path(__file__).resolve().parents[5] / "packages" / "skills" / "seo" / "shopify-product-collection"


def _load_skill_excerpt() -> str:
    parts: list[str] = []
    for name in (
        "SKILL.md",
        "seo-proposal-rules.md",
        "brand-guardrails.md",
    ):
        path = SKILL_DIR / name
        if path.exists():
            parts.append(path.read_text(encoding="utf-8")[:3000])
    return "\n\n".join(parts)


def _product_current_values(product: ShopifyProduct) -> dict[str, Any]:
    return {
        "product_title": product.title,
        "seo_title": product.seo_title,
        "meta_description": product.seo_description,
        "handle": product.handle,
        "tags": product.tags or [],
        "description_html": product.description_html,
        "media_images": product.media_images or [],
    }


def _collection_current_values(collection: ShopifyCollection) -> dict[str, Any]:
    return {
        "collection_title": collection.title,
        "seo_title": collection.seo_title,
        "meta_description": collection.seo_description,
        "description_html": collection.description_html,
        "handle": collection.handle,
        "image_alt": collection.image_alt,
    }


def _rules_product_proposal(product: ShopifyProduct, analysis: SeoEntityAnalysis) -> dict[str, Any]:
    proposed = {
        "proposed_product_title": product.title,
        "proposed_seo_title": product.seo_title or product.title[:60],
        "proposed_meta_description": product.seo_description or "",
        "proposed_handle": product.handle or "",
        "proposed_tags": product.tags or [],
        "proposed_image_alts": [],
        "reasoning": ["Proposta rule-based: solo campi mancanti compilati con dati esistenti"],
        "risk_level": "low",
    }
    if not product.seo_title:
        proposed["reasoning"].append("SEO title derivato dal titolo prodotto")
    return proposed


def _rules_collection_proposal(
    collection: ShopifyCollection,
    analysis: SeoEntityAnalysis,
) -> dict[str, Any]:
    return {
        "proposed_collection_title": collection.title,
        "proposed_seo_title": collection.seo_title or collection.title[:60],
        "proposed_meta_description": collection.seo_description or "",
        "proposed_description": collection.description_html or "",
        "proposed_handle": collection.handle or "",
        "proposed_image_alt": collection.image_alt or collection.title,
        "reasoning": ["Proposta rule-based conservativa"],
        "risk_level": "low",
    }


async def generate_seo_proposal(
    store: ShopifyStore,
    session: AsyncSession,
    *,
    entity_type: str,
    entity_id: UUID,
    use_ai: bool = True,
) -> SeoOptimizationProposal:
    analysis = (
        await session.execute(
            select(SeoEntityAnalysis).where(
                SeoEntityAnalysis.project_id == store.project_id,
                SeoEntityAnalysis.shopify_store_id == store.id,
                SeoEntityAnalysis.entity_type == entity_type,
                SeoEntityAnalysis.entity_id == entity_id,
            )
        )
    ).scalar_one_or_none()
    if analysis is None:
        raise ValueError("Esegui prima l'analisi SEO su questa entità")

    if entity_type == "product":
        entity = (
            await session.execute(
                select(ShopifyProduct).where(
                    ShopifyProduct.id == entity_id,
                    ShopifyProduct.shopify_store_id == store.id,
                )
            )
        ).scalar_one_or_none()
        if entity is None:
            raise ValueError("Prodotto non trovato")
        current = _product_current_values(entity)
        entity_gid = entity.shopify_gid
    elif entity_type == "collection":
        entity = (
            await session.execute(
                select(ShopifyCollection).where(
                    ShopifyCollection.id == entity_id,
                    ShopifyCollection.shopify_store_id == store.id,
                )
            )
        ).scalar_one_or_none()
        if entity is None:
            raise ValueError("Collection non trovata")
        current = _collection_current_values(entity)
        entity_gid = entity.shopify_gid
    else:
        raise ValueError("entity_type non supportato")

    source = "rules"
    proposed: dict[str, Any]
    reasoning: list[Any]

    if use_ai and is_openai_configured():
        skill = _load_skill_excerpt()
        system_prompt = (
            "Sei un SEO specialist ecommerce Shopify. "
            "Rispondi SOLO con JSON valido. Non inventare claim non presenti nei dati. "
            f"Regole skill:\n{skill}"
        )
        user_prompt = (
            f"entity_type={entity_type}\n"
            f"current_values={current}\n"
            f"issues={analysis.issues}\n"
            f"recommendations={analysis.recommendations}\n"
            "Genera proposta JSON secondo seo-proposal-rules."
        )
        try:
            proposed = await generate_structured_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
            source = "ai"
            reasoning = proposed.get("reasoning") or []
        except (OpenAINotConfiguredError, OpenAIRequestError):
            if entity_type == "product":
                proposed = _rules_product_proposal(entity, analysis)
            else:
                proposed = _rules_collection_proposal(entity, analysis)
            reasoning = proposed.get("reasoning") or []
    else:
        if entity_type == "product":
            proposed = _rules_product_proposal(entity, analysis)
        else:
            proposed = _rules_collection_proposal(entity, analysis)
        reasoning = proposed.get("reasoning") or []

    risk_level = str(proposed.get("risk_level") or "low")
    proposal = SeoOptimizationProposal(
        project_id=store.project_id,
        shopify_store_id=store.id,
        entity_type=entity_type,
        entity_id=entity_id,
        entity_gid=entity_gid,
        status="draft",
        source=source,
        current_values=current,
        proposed_values=proposed,
        reasoning=reasoning if isinstance(reasoning, list) else [str(reasoning)],
        risk_level=risk_level if risk_level in ("low", "medium", "high") else "low",
    )
    session.add(proposal)
    await session.commit()
    await session.refresh(proposal)
    return proposal


def openai_status() -> dict[str, Any]:
    return {
        "configured": is_openai_configured(),
        "model": settings.openai_model if is_openai_configured() else None,
    }
