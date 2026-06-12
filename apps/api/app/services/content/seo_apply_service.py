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
            "Per applicare modifiche su Shopify serve riconnettere l'app con write_products."
        ),
    }


def _get_proposed(proposed: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in proposed and proposed[key] is not None:
            return proposed[key]
    return None


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
            title = _get_proposed(
                proposed, "product_title", "proposed_product_title"
            )
            if title:
                input_data["title"] = title
            handle = _get_proposed(proposed, "handle", "proposed_handle")
            if handle:
                input_data["handle"] = handle
            tags = _get_proposed(proposed, "tags", "proposed_tags")
            if tags is not None:
                input_data["tags"] = tags
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
