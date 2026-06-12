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
from app.services.content.seo_skill_loader import load_seo_skill_context


def product_current_values(product: ShopifyProduct) -> dict[str, Any]:
    return {
        "product_title": product.title,
        "seo_title": product.seo_title,
        "meta_description": product.seo_description,
        "handle": product.handle,
        "tags": product.tags or [],
        "description_html": product.description_html,
        "description_text": product.description_text,
        "media_images": product.media_images or [],
    }


def collection_current_values(collection: ShopifyCollection) -> dict[str, Any]:
    return {
        "collection_title": collection.title,
        "seo_title": collection.seo_title,
        "meta_description": collection.seo_description,
        "description_html": collection.description_html,
        "description_text": collection.description_text,
        "handle": collection.handle,
        "image_alt": collection.image_alt,
    }


def _weak_issue_fields(issues: list[dict[str, Any]] | None) -> set[str]:
    weak: set[str] = set()
    for issue in issues or []:
        sev = str(issue.get("severity", ""))
        if sev in ("critical", "warning", "opportunity", "info"):
            field = issue.get("field")
            if field:
                weak.add(str(field))
    return weak


def _rules_product_proposal(product: ShopifyProduct, analysis: SeoEntityAnalysis) -> dict[str, Any]:
    weak = _weak_issue_fields(analysis.issues)
    proposed = {
        "product_title": product.title,
        "seo_title": product.seo_title or (product.title[:60] if "seo_title" in weak else product.seo_title),
        "meta_description": product.seo_description or "",
        "handle": product.handle or "",
        "tags": product.tags or [],
        "description_html": product.description_html,
        "media_images": product.media_images or [],
        "reasoning": ["Proposta rule-based: solo campi mancanti o deboli compilati con dati esistenti"],
        "risk_level": "low",
    }
    if not product.seo_title and "seo_title" in weak:
        proposed["reasoning"].append("SEO title derivato dal titolo prodotto")
    return proposed


def _rules_collection_proposal(
    collection: ShopifyCollection,
    analysis: SeoEntityAnalysis,
) -> dict[str, Any]:
    return {
        "collection_title": collection.title,
        "seo_title": collection.seo_title or collection.title[:60],
        "meta_description": collection.seo_description or "",
        "description_html": collection.description_html or "",
        "handle": collection.handle or "",
        "image_alt": collection.image_alt or collection.title,
        "reasoning": ["Proposta rule-based conservativa"],
        "risk_level": "low",
    }


def _ai_system_prompt(skill_context: str) -> str:
    return (
        "Sei un SEO specialist ecommerce Shopify. "
        "Rispondi SOLO con JSON valido strutturato. "
        "Non inventare claim non presenti nei dati forniti. "
        "Non modificare il significato del prodotto/collection. "
        "Evita keyword stuffing. "
        "Rispetta brand guardrails, regole SEO title, meta description, alt image. "
        "Modalità fill_missing_and_improve: compila campi mancanti e migliora solo quelli deboli; "
        "non sovrascrivere campi già ottimali.\n\n"
        f"{skill_context}"
    )


def _ai_user_prompt(
    *,
    entity_type: str,
    current: dict[str, Any],
    analysis: SeoEntityAnalysis,
    mode: str,
) -> str:
    return (
        f"mode={mode}\n"
        f"entity_type={entity_type}\n"
        f"current_values={current}\n"
        f"issues={analysis.issues}\n"
        f"recommendations={analysis.recommendations}\n"
        f"score_breakdown={analysis.score_breakdown}\n"
        "Genera proposta JSON con chiavi allineate a current_values (stessi nomi), "
        "più reasoning (array stringhe) e risk_level (low|medium|high)."
    )


async def generate_seo_proposal(
    store: ShopifyStore,
    session: AsyncSession,
    *,
    entity_type: str,
    entity_id: UUID,
    use_ai: bool = True,
    mode: str = "fill_missing_and_improve",
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
        current = product_current_values(entity)
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
        current = collection_current_values(entity)
        entity_gid = entity.shopify_gid
    else:
        raise ValueError("entity_type non supportato")

    source = "rules"
    proposed: dict[str, Any]
    reasoning: list[Any]

    skill_ctx = load_seo_skill_context()

    if use_ai and is_openai_configured():
        system_prompt = _ai_system_prompt(skill_ctx.as_prompt_context())
        user_prompt = _ai_user_prompt(
            entity_type=entity_type,
            current=current,
            analysis=analysis,
            mode=mode,
        )
        try:
            proposed = await generate_structured_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
            source = "ai"
            reasoning = proposed.pop("reasoning", []) or []
            risk_from_ai = proposed.pop("risk_level", "low")
            proposed["risk_level"] = risk_from_ai
        except (OpenAINotConfiguredError, OpenAIRequestError):
            if entity_type == "product":
                proposed = _rules_product_proposal(entity, analysis)
            else:
                proposed = _rules_collection_proposal(entity, analysis)
            reasoning = proposed.pop("reasoning", []) or []
    else:
        if entity_type == "product":
            proposed = _rules_product_proposal(entity, analysis)
        else:
            proposed = _rules_collection_proposal(entity, analysis)
        reasoning = proposed.pop("reasoning", []) or []

    risk_level = str(proposed.pop("risk_level", "low"))
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
