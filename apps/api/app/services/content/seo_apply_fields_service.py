"""Direct field-level apply — whitelist via changedFields, no historical proposals."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_seo import ShopifyCollection
from app.models.seo_optimizer import SeoChangeLog, SeoOptimizationProposal
from app.models.shopify import ShopifyProduct, ShopifyStore
from app.services.content.seo_apply_local_update import apply_proposed_values_to_entity
from app.services.content.seo_apply_service import (
    _build_apply_success_response,
    write_products_required_response,
)
from app.services.content.seo_apply_shopify import (
    apply_collection_image_alt,
    apply_collection_scalar_update,
    apply_product_media_alts,
    apply_product_scalar_update,
)
from app.services.content.seo_entity_analyze_single import (
    analyze_single_collection,
    analyze_single_product,
)
from app.services.content.seo_field_keys import (
    filter_proposed_by_whitelist,
    normalize_api_fields_to_snake,
    whitelist_changed_fields,
)
from app.services.content.seo_proposal_diff import compute_changed_proposed
from app.services.content.seo_proposal_engine import (
    collection_current_values,
)
from app.services.content.seo_proposal_manual_service import _product_current_with_metafields
from app.services.shopify.client import ShopifyAPIError, ShopifyGraphQLClient
from app.services.shopify.metafield_apply import apply_product_metafields
from app.services.shopify.scopes import can_apply_with_write_products

logger = logging.getLogger(__name__)


async def _load_entity(
    store: ShopifyStore,
    session: AsyncSession,
    entity_type: str,
    entity_id: UUID,
) -> tuple[ShopifyProduct | ShopifyCollection, str, dict[str, Any]]:
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
        return entity, entity.shopify_gid, current

    if entity_type == "collection":
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
        return entity, entity.shopify_gid, current

    raise ValueError("entity_type non supportato")


async def apply_entity_fields(
    store: ShopifyStore,
    client: ShopifyGraphQLClient,
    session: AsyncSession,
    *,
    entity_type: str,
    entity_id: UUID,
    fields: dict[str, Any],
    changed_fields: list[str],
) -> dict[str, Any]:
    scope_check = await can_apply_with_write_products(store, session)
    if not scope_check["allowed"]:
        return write_products_required_response(
            message=scope_check["message"],
            requires_reconnect=scope_check["requires_reconnect"],
        )

    whitelist = whitelist_changed_fields(entity_type, changed_fields)
    if not whitelist:
        raise ValueError("changedFields vuoto o non valido")

    _entity, entity_gid, current = await _load_entity(store, session, entity_type, entity_id)
    proposed_snake = normalize_api_fields_to_snake(entity_type, fields)
    proposed_snake = filter_proposed_by_whitelist(proposed_snake, whitelist)

    effective_delta, _ = compute_changed_proposed(current, proposed_snake)
    if not effective_delta:
        raise ValueError("Nessun campo da applicare")

    applied_values: dict[str, Any] = {}
    shopify_response: dict[str, Any] = {}

    try:
        if entity_type == "product":
            scalar_keys = {
                "product_title",
                "handle",
                "seo_title",
                "meta_description",
                "description_html",
            }
            scalar_delta = {k: v for k, v in effective_delta.items() if k in scalar_keys}
            if scalar_delta:
                await apply_product_scalar_update(
                    client, entity_gid, scalar_delta, shopify_response
                )
            if "image_alts" in effective_delta:
                await apply_product_media_alts(
                    client, entity_gid, effective_delta, shopify_response
                )
            if "metafields" in effective_delta:
                mf_entries = effective_delta.get("metafields")
                if isinstance(mf_entries, list) and mf_entries:
                    warnings = await apply_product_metafields(
                        client,
                        entity_gid,
                        mf_entries,
                        shopify_response,
                    )
                    if warnings:
                        logger.warning(
                            "metafield apply warnings entity=%s: %s",
                            entity_id,
                            "; ".join(warnings[:3]),
                        )
        elif entity_type == "collection":
            scalar_keys = {
                "collection_title",
                "handle",
                "seo_title",
                "meta_description",
                "description_html",
            }
            scalar_delta = {k: v for k, v in effective_delta.items() if k in scalar_keys}
            if scalar_delta:
                await apply_collection_scalar_update(
                    client, entity_gid, scalar_delta, shopify_response
                )
            if "image_alt" in effective_delta:
                await apply_collection_image_alt(
                    client, entity_gid, effective_delta, shopify_response
                )
        else:
            raise ValueError("entity_type non supportato")

        applied_values = effective_delta

        updated = await apply_proposed_values_to_entity(
            session,
            entity_type,
            entity_id,
            effective_delta,
            shopify_response=shopify_response,
            store_id=store.id,
        )
        local_ok = updated is not None
        if local_ok:
            if entity_type == "product":
                await analyze_single_product(store, session, entity_id)
            else:
                await analyze_single_collection(store, session, entity_id)

        now = datetime.now(UTC)
        audit_proposal = SeoOptimizationProposal(
            project_id=store.project_id,
            shopify_store_id=store.id,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_gid=entity_gid,
            status="applied",
            source="field_apply",
            current_values=current,
            proposed_values=effective_delta,
            reasoning=["Apply diretto campo-per-campo"],
            risk_level="low",
            approved_at=now,
            applied_at=now,
        )
        session.add(audit_proposal)
        await session.flush()

        log = SeoChangeLog(
            project_id=store.project_id,
            shopify_store_id=store.id,
            proposal_id=audit_proposal.id,
            entity_type=entity_type,
            entity_gid=entity_gid,
            applied_values=applied_values,
            shopify_response=shopify_response,
            status="success",
        )
        session.add(log)
        await session.commit()
        await session.refresh(audit_proposal)

        result = await _build_apply_success_response(
            store, session, audit_proposal, local_update_failed=not local_ok
        )
        result["applied_fields"] = list(whitelist)
        return result

    except ShopifyAPIError as exc:
        audit_proposal = SeoOptimizationProposal(
            project_id=store.project_id,
            shopify_store_id=store.id,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_gid=entity_gid,
            status="draft",
            source="field_apply",
            current_values=current,
            proposed_values=effective_delta,
            reasoning=["Apply diretto fallito"],
            risk_level="low",
        )
        session.add(audit_proposal)
        await session.flush()
        log = SeoChangeLog(
            project_id=store.project_id,
            shopify_store_id=store.id,
            proposal_id=audit_proposal.id,
            entity_type=entity_type,
            entity_gid=entity_gid,
            applied_values=applied_values,
            shopify_response=shopify_response,
            status="failed",
            error_message=exc.message,
        )
        session.add(log)
        await session.commit()
        return {
            "applied": False,
            "message": exc.message,
            "proposal_id": str(audit_proposal.id),
        }
