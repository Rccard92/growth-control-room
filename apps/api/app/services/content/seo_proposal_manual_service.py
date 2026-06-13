from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_seo import ShopifyCollection
from app.models.seo_optimizer import SeoOptimizationProposal
from app.models.shopify import ShopifyProduct, ShopifyProductMetafield, ShopifyStore
from app.services.content.seo_current_values import normalize_proposal_values
from app.services.content.seo_field_keys import whitelist_changed_fields
from app.services.content.seo_proposal_diff import compute_changed_proposed
from app.services.content.seo_proposal_engine import (
    collection_current_values,
    product_current_values,
)
from app.services.shopify.metafield_merge import build_product_metafields_merged
from app.services.shopify.metafield_utils import (
    is_editable_metafield_type,
    metafields_current_snapshot,
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
    "metafields",
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
    if entity_type == "product" and "metafields" in cleaned:
        entries = cleaned["metafields"]
        if not isinstance(entries, list) or not entries:
            del cleaned["metafields"]
        else:
            validated: list[dict[str, Any]] = []
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                mid = str(entry.get("id") or entry.get("metafield_id") or entry.get("metafieldId") or "").strip()
                definition_id = entry.get("definition_id") or entry.get("definitionId")
                namespace = str(entry.get("namespace") or "").strip()
                key = str(entry.get("key") or "").strip()
                type_name = str(entry.get("type") or "").strip()
                value = entry.get("value")
                if value is None:
                    value = ""
                value_str = str(value)
                if not namespace or not key or not type_name:
                    continue
                if not mid and not definition_id:
                    continue
                if not is_editable_metafield_type(type_name, value_str):
                    raise ValueError(
                        "Questo tipo di metafield non è ancora modificabile da Growth Control Room."
                    )
                validated.append(
                    {
                        "id": mid or None,
                        "metafield_id": mid or None,
                        "definition_id": definition_id,
                        "namespace": namespace,
                        "key": key,
                        "type": type_name,
                        "value": value_str,
                    }
                )
            if validated:
                cleaned["metafields"] = validated
            else:
                cleaned.pop("metafields", None)
    if not cleaned:
        raise ValueError("proposed_values non contiene campi validi")
    return cleaned


async def _product_current_with_metafields(
    store: ShopifyStore,
    session: AsyncSession,
    product: ShopifyProduct,
) -> dict[str, Any]:
    current = product_current_values(product)
    merged, _ = await build_product_metafields_merged(store, session, product.id)
    current["metafields"] = [
        {
            "id": m.get("metafield_id") or m.get("definition_id"),
            "metafield_id": m.get("metafield_id"),
            "definition_id": m.get("definition_id"),
            "namespace": m["namespace"],
            "key": m["key"],
            "type": m["type"],
            "value": m.get("display_value") or m.get("value") or "",
            "display_value": m.get("display_value") or m.get("value") or "",
        }
        for m in merged
        if m.get("exists_on_product")
    ]
    if not current["metafields"]:
        rows = list(
            (
                await session.execute(
                    select(ShopifyProductMetafield).where(
                        ShopifyProductMetafield.shopify_store_id == store.id,
                        ShopifyProductMetafield.product_id == product.id,
                    )
                )
            ).scalars().all()
        )
        current["metafields"] = metafields_current_snapshot(rows)
    return current


async def create_manual_proposal(
    store: ShopifyStore,
    session: AsyncSession,
    *,
    entity_type: str,
    entity_id: UUID,
    proposed_values: dict[str, Any],
    changed_fields: list[str] | None = None,
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
        current = await _product_current_with_metafields(store, session, entity)
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
    if changed_fields:
        whitelist = whitelist_changed_fields(entity_type, changed_fields)
        cleaned = {k: v for k, v in cleaned.items() if k in whitelist or (k == "media_images" and "image_alts" in whitelist)}
    proposed_delta, computed_fields = compute_changed_proposed(current, cleaned)
    if not computed_fields:
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
