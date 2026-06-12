from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.seo_optimizer import SeoChangeLog, SeoOptimizationProposal
from app.models.shopify import ShopifyStore
from app.services.shopify.client import ShopifyAPIError, ShopifyGraphQLClient


def has_write_products_scope() -> bool:
    scopes = {s.strip() for s in settings.shopify_scopes.split(",") if s.strip()}
    return "write_products" in scopes


def write_products_required_response() -> dict[str, Any]:
    return {
        "applied": False,
        "requires_scope": "write_products",
        "message": (
            "Per applicare modifiche prodotto o collection serve riconnettere Shopify "
            "con write_products."
        ),
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

    if not has_write_products_scope():
        return write_products_required_response()

    proposed = proposal.proposed_values or {}
    applied_values: dict[str, Any] = {}
    shopify_response: dict[str, Any] = {}

    try:
        if proposal.entity_type == "product":
            mutation = """
            mutation ProductUpdate($input: ProductInput!) {
              productUpdate(input: $input) {
                product { id title handle seo { title description } }
                userErrors { field message }
              }
            }
            """
            input_data: dict[str, Any] = {"id": proposal.entity_gid}
            if proposed.get("proposed_product_title"):
                input_data["title"] = proposed["proposed_product_title"]
            if proposed.get("proposed_handle"):
                input_data["handle"] = proposed["proposed_handle"]
            if proposed.get("proposed_tags") is not None:
                input_data["tags"] = proposed["proposed_tags"]
            seo_block: dict[str, str] = {}
            if proposed.get("proposed_seo_title"):
                seo_block["title"] = proposed["proposed_seo_title"]
            if proposed.get("proposed_meta_description"):
                seo_block["description"] = proposed["proposed_meta_description"]
            if seo_block:
                input_data["seo"] = seo_block
            if proposed.get("proposed_description_html"):
                input_data["descriptionHtml"] = proposed["proposed_description_html"]

            data = await client.execute(mutation, {"input": input_data})
            shopify_response = data
            applied_values = proposed
            errors = (data.get("productUpdate") or {}).get("userErrors") or []
            if errors:
                raise ShopifyAPIError(
                    "; ".join(e.get("message", "") for e in errors[:3])
                )
        elif proposal.entity_type == "collection":
            mutation = """
            mutation CollectionUpdate($input: CollectionInput!) {
              collectionUpdate(input: $input) {
                collection { id title handle seo { title description } }
                userErrors { field message }
              }
            }
            """
            input_data = {"id": proposal.entity_gid}
            if proposed.get("proposed_collection_title"):
                input_data["title"] = proposed["proposed_collection_title"]
            if proposed.get("proposed_handle"):
                input_data["handle"] = proposed["proposed_handle"]
            if proposed.get("proposed_description"):
                input_data["descriptionHtml"] = proposed["proposed_description"]
            seo_block = {}
            if proposed.get("proposed_seo_title"):
                seo_block["title"] = proposed["proposed_seo_title"]
            if proposed.get("proposed_meta_description"):
                seo_block["description"] = proposed["proposed_meta_description"]
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
        else:
            raise ValueError("entity_type non supportato per apply")

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
        return {"applied": True, "proposal_id": str(proposal.id)}

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
