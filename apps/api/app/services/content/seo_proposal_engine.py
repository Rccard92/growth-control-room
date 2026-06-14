from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.content_seo import ShopifyCollection
from app.models.seo_optimizer import SeoEntityAnalysis, SeoOptimizationProposal
from app.models.shopify import ShopifyProduct, ShopifyStore
from app.services.ai.openai_client import (
    AiRequestMetadata,
    OpenAINotConfiguredError,
    OpenAIRequestError,
    generate_structured_json,
    is_openai_configured,
)
from app.services.content.seo_current_values import normalize_proposal_values
from app.services.content.seo_proposal_diff import compute_changed_proposed
from app.services.ai.context_profiles import (
    AiContextProfile,
    build_context_for_profile,
    build_prompt_cache_key,
    enrich_ai_metadata,
)
from app.services.content.seo_skill_loader import load_seo_skill_context


def _truncate_alt(text: str, *, max_len: int = 125) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= max_len:
        return cleaned
    return cleaned[: max_len - 1].rstrip() + "…"


def _proposed_alt_for_product(product: ShopifyProduct, image: dict[str, Any]) -> str:
    base = product.title or "Prodotto"
    if product.product_type:
        base = f"{base} — {product.product_type}"
    if product.vendor:
        base = f"{base} di {product.vendor}"
    alt = _truncate_alt(base)
    return alt if len(alt) >= 10 else _truncate_alt(f"Immagine {base}")


def _build_image_alts(
    product: ShopifyProduct,
    media_images: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    image_alts: list[dict[str, Any]] = []
    for image in media_images or []:
        image_id = image.get("id")
        if not image_id:
            continue
        current_alt = image.get("altText") or image.get("alt") or ""
        if isinstance(current_alt, str) and current_alt.strip():
            continue
        proposed_alt = _proposed_alt_for_product(product, image)
        image_alts.append(
            {
                "image_id": image_id,
                "current_alt": current_alt or "",
                "proposed_alt": proposed_alt,
                "reason": "Alt text descrittivo derivato da titolo e contesto prodotto",
            }
        )
    return image_alts


def _apply_image_alts_to_media(
    media_images: list[dict[str, Any]] | None,
    image_alts: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    if not media_images:
        return []
    alt_by_id = {
        str(item.get("image_id")): item.get("proposed_alt")
        for item in image_alts or []
        if item.get("image_id") and item.get("proposed_alt")
    }
    updated: list[dict[str, Any]] = []
    for index, image in enumerate(media_images):
        row = dict(image)
        image_id = str(row.get("id") or "")
        proposed_alt = alt_by_id.get(image_id)
        if proposed_alt:
            row["altText"] = proposed_alt
        row.setdefault("position", index + 1)
        updated.append(row)
    return updated


def product_current_values(product: ShopifyProduct) -> dict[str, Any]:
    return {
        "product_title": product.title,
        "seo_title": product.seo_title,
        "meta_description": product.seo_description,
        "handle": product.handle,
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
    media = product.media_images or []
    image_alts = _build_image_alts(product, media)
    proposed = {
        "product_title": product.title,
        "seo_title": product.seo_title
        or (product.title[:60] if "seo_title" in weak else product.seo_title),
        "meta_description": product.seo_description or "",
        "handle": product.handle or "",
        "description_html": product.description_html,
        "media_images": _apply_image_alts_to_media(media, image_alts),
        "image_alts": image_alts,
        "reasoning": ["Proposta rule-based: solo campi mancanti o deboli compilati con dati esistenti"],
        "risk_level": "low",
    }
    if not product.seo_title and "seo_title" in weak:
        proposed["reasoning"].append("SEO title derivato dal titolo prodotto")
    if image_alts:
        proposed["reasoning"].append("Alt text proposto per immagini senza alt")
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


def _safe_claims_guardrail_suffix(brand_context: str | None) -> str:
    if not brand_context:
        return ""
    if "SAFE CLAIMS" in brand_context.upper():
        return (
            "\n\nREGOLE SAFE CLAIMS (priorità massima): non usare claim vietati; "
            "evitare claim medici/terapeutici; non attaccare competitor; "
            "non divulgare process secrets."
        )
    return ""


def _ai_system_prompt(skill_context: str, brand_context: str | None = None) -> str:
    base = (
        "Sei un SEO specialist ecommerce Shopify. "
        "Rispondi SOLO con JSON valido strutturato. "
        "Non inventare claim non presenti nei dati forniti. "
        "Non modificare il significato del prodotto/collection. "
        "Evita keyword stuffing. "
        "Non generare tag prodotto. "
        "Rispetta brand guardrails, regole SEO title, meta description, alt image. "
        "Modalità fill_missing_and_improve: compila campi mancanti e migliora solo quelli deboli; "
        "non sovrascrivere campi già ottimali.\n\n"
        f"{skill_context}"
    )
    if brand_context:
        base += f"\n\n{brand_context}"
        base += _safe_claims_guardrail_suffix(brand_context)
    return base


def _ai_user_prompt(
    *,
    entity_type: str,
    current: dict[str, Any],
    analysis: SeoEntityAnalysis,
    mode: str,
) -> str:
    image_alt_hint = ""
    if entity_type == "product":
        image_alt_hint = (
            ' Per prodotti includi anche "image_alts": '
            '[{"image_id":"...","current_alt":"...","proposed_alt":"...","reason":"..."}] '
            "per ogni immagine in media_images senza alt o con alt debole. "
            "Alt text: descrittivo, naturale, 10-125 caratteri, coerente con prodotto."
        )
    return (
        f"mode={mode}\n"
        f"entity_type={entity_type}\n"
        f"current_values={current}\n"
        f"issues={analysis.issues}\n"
        f"recommendations={analysis.recommendations}\n"
        f"score_breakdown={analysis.score_breakdown}\n"
        "Genera proposta JSON con chiavi allineate a current_values (stessi nomi), "
        "più reasoning (array stringhe) e risk_level (low|medium|high)."
        f"{image_alt_hint}"
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
    profile = (
        AiContextProfile.PRODUCT_SEO_FULL
        if entity_type == "product"
        else AiContextProfile.COLLECTION_SEO_FULL
    )
    ctx = await build_context_for_profile(
        session,
        store.project_id,
        profile,
        entity_type=entity_type,
        entity_id=entity_id,
        options={"shopify_product_id": entity_id} if entity_type == "product" else None,
    )
    brand_ctx = ctx.context_text

    if use_ai and is_openai_configured():
        system_prompt = _ai_system_prompt(
            skill_ctx.as_proposal_prompt_context(),
            brand_ctx,
        )
        user_prompt = _ai_user_prompt(
            entity_type=entity_type,
            current=current,
            analysis=analysis,
            mode=mode,
        )
        seo_module = "product_seo" if entity_type == "product" else "content_seo"
        cache_key = build_prompt_cache_key(store.project_id, seo_module, ctx.context_hash)
        try:
            proposed = await generate_structured_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                metadata=enrich_ai_metadata(
                    AiRequestMetadata(
                        project_id=store.project_id,
                        module=seo_module,
                        operation="generate_proposal",
                        operation_key=(
                            "product_seo_full_proposal"
                            if entity_type == "product"
                            else "collection_seo_full_proposal"
                        ),
                        entity_type=entity_type,
                        entity_id=entity_id,
                    ),
                    ctx,
                ),
                prompt_cache_key=cache_key,
            )
            proposed = normalize_proposal_values(entity_type, proposed)
            if entity_type == "product" and proposed.get("image_alts"):
                proposed["media_images"] = _apply_image_alts_to_media(
                    proposed.get("media_images") or current.get("media_images"),
                    proposed.get("image_alts"),
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
    proposed_delta, _changed = compute_changed_proposed(current, proposed)
    if not _changed:
        raise ValueError("Nessun campo da proporre")
    proposal = SeoOptimizationProposal(
        project_id=store.project_id,
        shopify_store_id=store.id,
        entity_type=entity_type,
        entity_id=entity_id,
        entity_gid=entity_gid,
        status="draft",
        source=source,
        current_values=current,
        proposed_values=proposed_delta,
        reasoning=reasoning if isinstance(reasoning, list) else [str(reasoning)],
        risk_level=risk_level if risk_level in ("low", "medium", "high") else "low",
    )
    session.add(proposal)
    await session.commit()
    await session.refresh(proposal)
    return proposal


def openai_status() -> dict[str, Any]:
    if not is_openai_configured():
        return {"configured": False, "model": None, "tierModels": None}
    return {
        "configured": True,
        "model": settings.openai_model,
        "tierModels": {
            "cheap": settings.openai_model_cheap or settings.openai_model,
            "standard": settings.openai_model_standard or settings.openai_model,
            "premium": settings.openai_model_premium or "gpt-4o",
            "reasoning": settings.openai_model_reasoning,
            "fallback": (
                settings.openai_model_fallback
                or settings.openai_model_standard
                or settings.openai_model
            ),
        },
    }
