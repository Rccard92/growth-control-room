import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.seo_optimizer import SeoChangeLog, SeoOptimizationProposal
from app.models.shopify import ShopifyStore
from app.services.content.seo_apply_local_update import apply_proposed_values_to_entity
from app.services.content.seo_proposal_diff import (
    compute_changed_proposed,
    proposal_changed_fields,
)
from app.services.content.seo_entity_analyze_single import (
    analyze_single_collection,
    analyze_single_product,
)
from app.services.content.seo_entity_detail_service import (
    get_collection_seo_detail,
    get_product_seo_detail,
)
from app.services.content.seo_apply_shopify import (
    apply_collection_image_alt,
    apply_collection_scalar_update,
    apply_product_media_alts,
    apply_product_scalar_update,
)
from app.services.shopify.client import ShopifyAPIError, ShopifyGraphQLClient
from app.services.shopify.metafield_apply import apply_product_metafields
from app.services.shopify.scopes import can_apply_with_write_products

logger = logging.getLogger(__name__)


def write_products_required_response(
    *,
    message: str | None = None,
    requires_reconnect: bool = True,
) -> dict[str, Any]:
    return {
        "applied": False,
        "requires_scope": "write_products",
        "requires_reconnect": requires_reconnect,
        "message": message
        or (
            "Il token Shopify corrente non include write_products. Riconnetti Shopify."
        ),
    }


def _proposal_payload(proposal: SeoOptimizationProposal) -> dict[str, Any]:
    return {
        "id": str(proposal.id),
        "entityType": proposal.entity_type,
        "entityId": str(proposal.entity_id),
        "entityGid": proposal.entity_gid,
        "status": proposal.status,
        "source": proposal.source,
        "currentValues": proposal.current_values,
        "proposedValues": proposal.proposed_values,
        "reasoning": proposal.reasoning,
        "riskLevel": proposal.risk_level,
        "changedFields": proposal_changed_fields(
            proposal.current_values,
            proposal.proposed_values,
        ),
        "approvedAt": proposal.approved_at,
        "appliedAt": proposal.applied_at,
        "createdAt": proposal.created_at,
    }


async def _refresh_local_after_apply(
    store: ShopifyStore,
    session: AsyncSession,
    proposal: SeoOptimizationProposal,
    proposed: dict[str, Any],
    shopify_response: dict[str, Any],
) -> bool:
    try:
        updated = await apply_proposed_values_to_entity(
            session,
            proposal.entity_type,
            proposal.entity_id,
            proposed,
            shopify_response=shopify_response,
            store_id=store.id,
        )
        if updated is None:
            return False
        if proposal.entity_type == "product":
            await analyze_single_product(store, session, proposal.entity_id)
        else:
            await analyze_single_collection(store, session, proposal.entity_id)
        return True
    except Exception:
        logger.exception(
            "Local SEO refresh failed after Shopify apply proposal=%s",
            proposal.id,
        )
        return False


async def _build_apply_success_response(
    store: ShopifyStore,
    session: AsyncSession,
    proposal: SeoOptimizationProposal,
    *,
    local_update_failed: bool,
) -> dict[str, Any]:
    detail: dict[str, Any] | None = None
    if proposal.entity_type == "product":
        detail = await get_product_seo_detail(store, session, proposal.entity_id)
    else:
        detail = await get_collection_seo_detail(store, session, proposal.entity_id)

    message = (
        "Modifica applicata su Shopify, ma aggiornamento locale non riuscito. "
        "Usa 'Sincronizza da Shopify'."
        if local_update_failed
        else "Modifiche applicate su Shopify e dati locali aggiornati."
    )

    return {
        "applied": True,
        "local_update_failed": local_update_failed,
        "entity_type": proposal.entity_type,
        "entity_id": str(proposal.entity_id),
        "updated_entity": detail.get("current_values") if detail else None,
        "updated_analysis": detail.get("analysis") if detail else None,
        "detail": detail,
        "proposal": _proposal_payload(proposal),
        "proposal_id": str(proposal.id),
        "message": message,
    }


async def approve_proposal(
    proposal: SeoOptimizationProposal,
    session: AsyncSession,
) -> SeoOptimizationProposal:
    if proposal.status not in ("draft", "rejected"):
        raise ValueError("Solo proposte draft possono essere approvate")
    proposal.status = "approved"
    proposal.approved_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(proposal)
    return proposal


async def reject_proposal(
    proposal: SeoOptimizationProposal,
    session: AsyncSession,
) -> SeoOptimizationProposal:
    if proposal.status in ("applied",):
        raise ValueError("Proposta già applicata")
    proposal.status = "rejected"
    await session.commit()
    await session.refresh(proposal)
    return proposal


async def apply_proposal(
    store: ShopifyStore,
    client: ShopifyGraphQLClient,
    proposal: SeoOptimizationProposal,
    session: AsyncSession,
) -> dict[str, Any]:
    if proposal.status != "approved":
        raise ValueError("La proposta deve essere approved prima dell'apply")

    scope_check = await can_apply_with_write_products(store, session)
    if not scope_check["allowed"]:
        return write_products_required_response(
            message=scope_check["message"],
            requires_reconnect=scope_check["requires_reconnect"],
        )

    proposed = proposal.proposed_values or {}
    effective_proposed, _ = compute_changed_proposed(
        proposal.current_values,
        proposed,
    )
    if not effective_proposed:
        raise ValueError("Nessun campo da applicare nella proposta")
    applied_values: dict[str, Any] = {}
    shopify_response: dict[str, Any] = {}

    try:
        if proposal.entity_type == "product":
            scalar_keys = {
                "product_title",
                "handle",
                "seo_title",
                "meta_description",
                "description_html",
            }
            scalar_delta = {k: v for k, v in effective_proposed.items() if k in scalar_keys}
            if scalar_delta:
                await apply_product_scalar_update(
                    client, proposal.entity_gid, scalar_delta, shopify_response
                )
            applied_values = effective_proposed
            if "image_alts" in effective_proposed:
                await apply_product_media_alts(
                    client, proposal.entity_gid, effective_proposed, shopify_response
                )
            metafield_entries = effective_proposed.get("metafields")
            if isinstance(metafield_entries, list) and metafield_entries:
                mf_warnings = await apply_product_metafields(
                    client,
                    proposal.entity_gid,
                    metafield_entries,
                    shopify_response,
                )
                if mf_warnings:
                    logger.warning(
                        "metafield apply warnings proposal=%s: %s",
                        proposal.id,
                        "; ".join(mf_warnings[:3]),
                    )
        elif proposal.entity_type == "collection":
            scalar_keys = {
                "collection_title",
                "handle",
                "seo_title",
                "meta_description",
                "description_html",
            }
            scalar_delta = {k: v for k, v in effective_proposed.items() if k in scalar_keys}
            if scalar_delta:
                await apply_collection_scalar_update(
                    client, proposal.entity_gid, scalar_delta, shopify_response
                )
            applied_values = effective_proposed
            if "image_alt" in effective_proposed:
                await apply_collection_image_alt(
                    client, proposal.entity_gid, effective_proposed, shopify_response
                )
        else:
            raise ValueError("entity_type non supportato per apply")

        local_ok = await _refresh_local_after_apply(
            store, session, proposal, effective_proposed, shopify_response
        )

        proposal.status = "applied"
        proposal.applied_at = datetime.now(UTC)
        log = SeoChangeLog(
            project_id=store.project_id,
            shopify_store_id=store.id,
            proposal_id=proposal.id,
            entity_type=proposal.entity_type,
            entity_gid=proposal.entity_gid,
            applied_values=applied_values,
            shopify_response=shopify_response,
            status="success",
        )
        session.add(log)
        await session.commit()
        await session.refresh(proposal)

        return await _build_apply_success_response(
            store, session, proposal, local_update_failed=not local_ok
        )

    except ShopifyAPIError as exc:
        log = SeoChangeLog(
            project_id=store.project_id,
            shopify_store_id=store.id,
            proposal_id=proposal.id,
            entity_type=proposal.entity_type,
            entity_gid=proposal.entity_gid,
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
            "proposal_id": str(proposal.id),
        }


async def get_proposal_for_store(
    store: ShopifyStore,
    session: AsyncSession,
    proposal_id: UUID,
) -> SeoOptimizationProposal | None:
    result = await session.execute(
        select(SeoOptimizationProposal).where(
            SeoOptimizationProposal.id == proposal_id,
            SeoOptimizationProposal.project_id == store.project_id,
            SeoOptimizationProposal.shopify_store_id == store.id,
        )
    )
    return result.scalar_one_or_none()
