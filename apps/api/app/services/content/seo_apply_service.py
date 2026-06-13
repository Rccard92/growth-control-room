import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.seo_optimizer import SeoChangeLog, SeoOptimizationProposal
from app.models.shopify import ShopifyStore
from app.services.content.seo_apply_local_update import apply_proposed_values_to_entity
from app.services.content.seo_entity_analyze_single import (
    analyze_single_collection,
    analyze_single_product,
)
from app.services.content.seo_entity_detail_service import (
    get_collection_seo_detail,
    get_product_seo_detail,
)
from app.services.shopify.client import ShopifyAPIError, ShopifyGraphQLClient
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


def _get_proposed(proposed: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in proposed and proposed[key] is not None:
            return proposed[key]
    return None


async def _apply_product_media_alts(
    client: ShopifyGraphQLClient,
    product_gid: str,
    proposed: dict[str, Any],
    shopify_response: dict[str, Any],
) -> None:
    media_updates: list[dict[str, str]] = []
    image_alts = _get_proposed(proposed, "image_alts", "imageAlts") or []
    alt_by_id = {
        str(item.get("image_id") or item.get("imageId") or ""): str(
            item.get("proposed_alt") or item.get("proposedAlt") or ""
        )
        for item in image_alts
        if isinstance(item, dict)
    }
    media_images = _get_proposed(proposed, "media_images", "mediaImages") or []
    for image in media_images:
        if not isinstance(image, dict):
            continue
        image_id = str(image.get("id") or "")
        alt = (
            alt_by_id.get(image_id)
            or str(image.get("altText") or image.get("alt") or "").strip()
        )
        if image_id and alt:
            media_updates.append({"id": image_id, "alt": alt})

    if not media_updates:
        return

    mutation = """
    mutation ProductUpdateMedia($productId: ID!, $media: [UpdateMediaInput!]!) {
      productUpdateMedia(productId: $productId, media: $media) {
        media { id alt }
        mediaUserErrors { field message }
      }
    }
    """
    try:
        data = await client.execute(
            mutation,
            {"productId": product_gid, "media": media_updates},
        )
        shopify_response["productUpdateMedia"] = data.get("productUpdateMedia")
        errors = (data.get("productUpdateMedia") or {}).get("mediaUserErrors") or []
        if errors:
            logger.warning(
                "productUpdateMedia userErrors: %s",
                "; ".join(e.get("message", "") for e in errors[:3]),
            )
    except ShopifyAPIError:
        logger.exception("productUpdateMedia failed for product=%s", product_gid)


async def _apply_collection_image_alt(
    client: ShopifyGraphQLClient,
    collection_gid: str,
    proposed: dict[str, Any],
    shopify_response: dict[str, Any],
) -> None:
    image_alt = _get_proposed(proposed, "image_alt", "proposed_image_alt")
    if not image_alt:
        return
    mutation = """
    mutation CollectionUpdateImageAlt($input: CollectionInput!) {
      collectionUpdate(input: $input) {
        collection { id image { altText } }
        userErrors { field message }
      }
    }
    """
    try:
        data = await client.execute(
            mutation,
            {"input": {"id": collection_gid, "image": {"altText": image_alt}}},
        )
        shopify_response["collectionImageAltUpdate"] = data.get("collectionUpdate")
    except ShopifyAPIError:
        logger.exception("collection image alt update failed for %s", collection_gid)


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
    applied_values: dict[str, Any] = {}
    shopify_response: dict[str, Any] = {}

    try:
        if proposal.entity_type == "product":
            mutation = """
            mutation ProductUpdate($input: ProductInput!) {
              productUpdate(input: $input) {
                product { id title handle seo { title description } descriptionHtml }
                userErrors { field message }
              }
            }
            """
            input_data: dict[str, Any] = {"id": proposal.entity_gid}
            title = _get_proposed(
                proposed, "product_title", "proposed_product_title"
            )
            if title:
                input_data["title"] = title
            handle = _get_proposed(proposed, "handle", "proposed_handle")
            if handle:
                input_data["handle"] = handle
            seo_block: dict[str, str] = {}
            seo_title = _get_proposed(proposed, "seo_title", "proposed_seo_title")
            if seo_title:
                seo_block["title"] = seo_title
            meta = _get_proposed(proposed, "meta_description", "proposed_meta_description")
            if meta:
                seo_block["description"] = meta
            if seo_block:
                input_data["seo"] = seo_block
            desc_html = _get_proposed(
                proposed, "description_html", "proposed_description_html"
            )
            if desc_html:
                input_data["descriptionHtml"] = desc_html

            data = await client.execute(mutation, {"input": input_data})
            shopify_response = data
            applied_values = proposed
            errors = (data.get("productUpdate") or {}).get("userErrors") or []
            if errors:
                raise ShopifyAPIError(
                    "; ".join(e.get("message", "") for e in errors[:3])
                )
            await _apply_product_media_alts(
                client, proposal.entity_gid, proposed, shopify_response
            )
        elif proposal.entity_type == "collection":
            mutation = """
            mutation CollectionUpdate($input: CollectionInput!) {
              collectionUpdate(input: $input) {
                collection { id title handle seo { title description } descriptionHtml }
                userErrors { field message }
              }
            }
            """
            input_data = {"id": proposal.entity_gid}
            title = _get_proposed(
                proposed, "collection_title", "proposed_collection_title"
            )
            if title:
                input_data["title"] = title
            handle = _get_proposed(proposed, "handle", "proposed_handle")
            if handle:
                input_data["handle"] = handle
            desc_html = _get_proposed(
                proposed,
                "description_html",
                "proposed_description",
            )
            if desc_html:
                input_data["descriptionHtml"] = desc_html
            seo_block = {}
            seo_title = _get_proposed(proposed, "seo_title", "proposed_seo_title")
            if seo_title:
                seo_block["title"] = seo_title
            meta = _get_proposed(proposed, "meta_description", "proposed_meta_description")
            if meta:
                seo_block["description"] = meta
            if seo_block:
                input_data["seo"] = seo_block

            data = await client.execute(mutation, {"input": input_data})
            shopify_response = data
            applied_values = proposed
            errors = (data.get("collectionUpdate") or {}).get("userErrors") or []
            if errors:
                raise ShopifyAPIError(
                    "; ".join(e.get("message", "") for e in errors[:3])
                )
            await _apply_collection_image_alt(
                client, proposal.entity_gid, proposed, shopify_response
            )
        else:
            raise ValueError("entity_type non supportato per apply")

        local_ok = await _refresh_local_after_apply(
            store, session, proposal, proposed, shopify_response
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
