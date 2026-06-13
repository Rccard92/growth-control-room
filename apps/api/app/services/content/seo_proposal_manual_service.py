from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_seo import ShopifyCollection
from app.models.seo_optimizer import SeoOptimizationProposal
from app.models.shopify import ShopifyProduct, ShopifyStore
from app.services.content.seo_current_values import normalize_proposal_values
from app.services.content.seo_proposal_diff import compute_changed_proposed
from app.services.content.seo_proposal_engine import (
    collection_current_values,
    product_current_values,
)

PRODUCT_ALLOWED_KEYS = {
    "product_title",
    "handle",
    "seo_title",
    "meta_description",
    "description_html",
    "description_text",
    "media_images",
    "image_alts",
}

COLLECTION_ALLOWED_KEYS = {
    "collection_title",
    "handle",
    "seo_title",
    "meta_description",
    "description_html",
    "description_text",
    "image_alt",
}


def _validate_proposed_values(entity_type: str, proposed: dict[str, Any]) -> dict[str, Any]:
    allowed = PRODUCT_ALLOWED_KEYS if entity_type == "product" else COLLECTION_ALLOWED_KEYS
    cleaned = {k: v for k, v in proposed.items() if k in allowed}
    if not cleaned:
        raise ValueError("proposed_values non contiene campi validi")
    return cleaned


async def create_manual_proposal(
    store: ShopifyStore,
    session: AsyncSession,
    *,
    entity_type: str,
    entity_id: UUID,
    proposed_values: dict[str, Any],
) -> SeoOptimizationProposal:
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

    cleaned = _validate_proposed_values(
        entity_type,
        normalize_proposal_values(entity_type, proposed_values),
    )
    proposed_delta, changed_fields = compute_changed_proposed(current, cleaned)
    if not changed_fields:
        raise ValueError("Nessuna modifica da salvare")
    proposal = SeoOptimizationProposal(
        project_id=store.project_id,
        shopify_store_id=store.id,
        entity_type=entity_type,
        entity_id=entity_id,
        entity_gid=entity_gid,
        status="draft",
        source="manual",
        current_values=current,
        proposed_values=proposed_delta,
        reasoning=["Proposta creata manualmente dall'utente"],
        risk_level="low",
    )
    session.add(proposal)
    await session.commit()
    await session.refresh(proposal)
    return proposal
