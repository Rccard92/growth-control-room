from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_seo import ShopifyCollection
from app.models.seo_optimizer import SeoChangeLog, SeoEntityAnalysis, SeoOptimizationProposal
from app.models.shopify import ShopifyProduct, ShopifyStore
from app.services.content.seo_current_values import (
    collection_api_current_values,
    product_api_current_values,
)
from app.services.content.seo_scoring_engine import rebuild_score_breakdown_from_analysis
from app.services.shopify.analytics import compute_best_sellers, product_lookup


async def _latest_proposal(
    store: ShopifyStore,
    session: AsyncSession,
    entity_type: str,
    entity_id: UUID,
) -> SeoOptimizationProposal | None:
    result = await session.execute(
        select(SeoOptimizationProposal)
        .where(
            SeoOptimizationProposal.shopify_store_id == store.id,
            SeoOptimizationProposal.entity_type == entity_type,
            SeoOptimizationProposal.entity_id == entity_id,
        )
        .order_by(SeoOptimizationProposal.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _proposal_history(
    store: ShopifyStore,
    session: AsyncSession,
    entity_type: str,
    entity_id: UUID,
    limit: int = 10,
) -> list[SeoOptimizationProposal]:
    result = await session.execute(
        select(SeoOptimizationProposal)
        .where(
            SeoOptimizationProposal.shopify_store_id == store.id,
            SeoOptimizationProposal.entity_type == entity_type,
            SeoOptimizationProposal.entity_id == entity_id,
        )
        .order_by(SeoOptimizationProposal.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def _change_logs_for_entity(
    store: ShopifyStore,
    session: AsyncSession,
    entity_type: str,
    entity_id: UUID,
    limit: int = 10,
) -> list[SeoChangeLog]:
    result = await session.execute(
        select(SeoChangeLog)
        .join(
            SeoOptimizationProposal,
            SeoChangeLog.proposal_id == SeoOptimizationProposal.id,
        )
        .where(
            SeoChangeLog.shopify_store_id == store.id,
            SeoOptimizationProposal.entity_type == entity_type,
            SeoOptimizationProposal.entity_id == entity_id,
        )
        .order_by(SeoChangeLog.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


def _analysis_payload(analysis: SeoEntityAnalysis | None) -> dict[str, Any] | None:
    if analysis is None:
        return None
    breakdown = rebuild_score_breakdown_from_analysis(analysis)
    return {
        "id": str(analysis.id),
        "entityType": analysis.entity_type,
        "entityId": str(analysis.entity_id),
        "entityTitle": analysis.entity_title,
        "scoreTotal": analysis.score_total,
        "scoreTitle": analysis.score_title,
        "scoreSeoTitle": analysis.score_seo_title,
        "scoreMetaDescription": analysis.score_meta_description,
        "scoreDescription": analysis.score_description,
        "scoreImageAlt": analysis.score_image_alt,
        "scoreHandle": analysis.score_handle,
        "scoreTags": analysis.score_tags,
        "severity": analysis.severity,
        "issues": analysis.issues,
        "recommendations": analysis.recommendations,
        "scoreBreakdown": breakdown,
        "lastAnalyzedAt": analysis.last_analyzed_at,
    }


def _proposal_payload(proposal: SeoOptimizationProposal | None) -> dict[str, Any] | None:
    if proposal is None:
        return None
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


async def get_product_seo_detail(
    store: ShopifyStore,
    session: AsyncSession,
    product_id: UUID,
) -> dict[str, Any] | None:
    product = (
        await session.execute(
            select(ShopifyProduct).where(
                ShopifyProduct.id == product_id,
                ShopifyProduct.shopify_store_id == store.id,
            )
        )
    ).scalar_one_or_none()
    if product is None:
        return None

    analysis = (
        await session.execute(
            select(SeoEntityAnalysis).where(
                SeoEntityAnalysis.shopify_store_id == store.id,
                SeoEntityAnalysis.entity_type == "product",
                SeoEntityAnalysis.entity_id == product_id,
            )
        )
    ).scalar_one_or_none()

    products_by_gid = product_lookup([product])
    best_sellers = await compute_best_sellers(session, store.id, products_by_gid, limit=50)
    sales = next((b for b in best_sellers if b.get("product_title") == product.title), {})

    latest = await _latest_proposal(store, session, "product", product_id)
    history = await _proposal_history(store, session, "product", product_id)
    change_logs = await _change_logs_for_entity(store, session, "product", product_id)

    images = product.media_images or []
    if not images and product.featured_image_url:
        images = [{"url": product.featured_image_url, "altText": None}]

    current_values = product_api_current_values(product, images=images)

    return {
        "product": {
            "id": str(product.id),
            "shopify_gid": product.shopify_gid,
            "title": product.title,
            "handle": product.handle,
            "status": product.status,
            "product_type": product.product_type,
            "vendor": product.vendor,
            "featured_image_url": product.featured_image_url,
        },
        "analysis": _analysis_payload(analysis),
        "score_breakdown": (
            rebuild_score_breakdown_from_analysis(analysis) if analysis else None
        ),
        "current_values": current_values,
        "images": images,
        "quantity_sold": int(sales.get("quantity_sold") or 0),
        "revenue": float(sales.get("revenue") or 0),
        "stock": product.total_inventory,
        "latest_proposal": _proposal_payload(latest),
        "proposal_history": [_proposal_payload(p) for p in history if p],
        "change_logs": [
            {
                "id": str(log.id),
                "status": log.status,
                "appliedValues": log.applied_values,
                "errorMessage": log.error_message,
                "createdAt": log.created_at,
                "proposalId": str(log.proposal_id),
            }
            for log in change_logs
        ],
    }


async def get_collection_seo_detail(
    store: ShopifyStore,
    session: AsyncSession,
    collection_id: UUID,
) -> dict[str, Any] | None:
    collection = (
        await session.execute(
            select(ShopifyCollection).where(
                ShopifyCollection.id == collection_id,
                ShopifyCollection.shopify_store_id == store.id,
            )
        )
    ).scalar_one_or_none()
    if collection is None:
        return None

    analysis = (
        await session.execute(
            select(SeoEntityAnalysis).where(
                SeoEntityAnalysis.shopify_store_id == store.id,
                SeoEntityAnalysis.entity_type == "collection",
                SeoEntityAnalysis.entity_id == collection_id,
            )
        )
    ).scalar_one_or_none()

    latest = await _latest_proposal(store, session, "collection", collection_id)
    history = await _proposal_history(store, session, "collection", collection_id)
    change_logs = await _change_logs_for_entity(store, session, "collection", collection_id)

    return {
        "collection": {
            "id": str(collection.id),
            "shopify_gid": collection.shopify_gid,
            "title": collection.title,
            "handle": collection.handle,
            "image_url": collection.image_url,
            "products_count": collection.products_count,
        },
        "analysis": _analysis_payload(analysis),
        "score_breakdown": (
            rebuild_score_breakdown_from_analysis(analysis) if analysis else None
        ),
        "current_values": collection_api_current_values(collection),
        "image": {
            "url": collection.image_url,
            "alt": collection.image_alt,
        },
        "latest_proposal": _proposal_payload(latest),
        "proposal_history": [_proposal_payload(p) for p in history if p],
        "change_logs": [
            {
                "id": str(log.id),
                "status": log.status,
                "appliedValues": log.applied_values,
                "errorMessage": log.error_message,
                "createdAt": log.created_at,
                "proposalId": str(log.proposal_id),
            }
            for log in change_logs
        ],
    }
