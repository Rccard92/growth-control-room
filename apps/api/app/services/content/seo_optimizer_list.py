from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_seo import ShopifyCollection
from app.models.seo_optimizer import SeoEntityAnalysis, SeoOptimizationProposal
from app.models.shopify import ShopifyProduct, ShopifyStore
from app.schemas.seo_optimizer import SeoEntityAnalysisRead
from app.services.content.seo_scoring_engine import rebuild_score_breakdown_from_analysis
from app.services.shopify.analytics import compute_best_sellers, product_lookup


def analysis_to_read(analysis: SeoEntityAnalysis) -> SeoEntityAnalysisRead:
    breakdown = rebuild_score_breakdown_from_analysis(analysis)
    return SeoEntityAnalysisRead(
        id=analysis.id,
        entity_type=analysis.entity_type,
        entity_id=analysis.entity_id,
        entity_title=analysis.entity_title,
        score_total=analysis.score_total,
        score_title=analysis.score_title,
        score_seo_title=analysis.score_seo_title,
        score_meta_description=analysis.score_meta_description,
        score_description=analysis.score_description,
        score_image_alt=analysis.score_image_alt,
        score_handle=analysis.score_handle,
        score_tags=analysis.score_tags,
        severity=analysis.severity,
        issues=analysis.issues,
        recommendations=analysis.recommendations,
        score_breakdown=breakdown,
        last_analyzed_at=analysis.last_analyzed_at,
    )


def _main_issues(issues: list[dict[str, Any]] | None, limit: int = 3) -> list[str]:
    if not issues:
        return []
    return [i.get("message", i.get("code", "")) for i in issues[:limit] if i]


async def list_product_seo_items(
    store: ShopifyStore,
    session: AsyncSession,
) -> list[dict[str, Any]]:
    products = (
        await session.execute(
            select(ShopifyProduct).where(ShopifyProduct.shopify_store_id == store.id)
        )
    ).scalars().all()

    analyses = (
        await session.execute(
            select(SeoEntityAnalysis).where(
                SeoEntityAnalysis.shopify_store_id == store.id,
                SeoEntityAnalysis.entity_type == "product",
            )
        )
    ).scalars().all()
    analysis_by_entity = {a.entity_id: a for a in analyses}

    proposals = (
        await session.execute(
            select(SeoOptimizationProposal).where(
                SeoOptimizationProposal.shopify_store_id == store.id,
                SeoOptimizationProposal.entity_type == "product",
                SeoOptimizationProposal.status.in_(("draft", "approved")),
            )
        )
    ).scalars().all()
    proposal_entities = {p.entity_id for p in proposals}

    products_by_gid = product_lookup(list(products))
    best_sellers = await compute_best_sellers(session, store.id, products_by_gid, limit=50)
    qty_by_title = {b.get("product_title"): b for b in best_sellers}

    items: list[dict[str, Any]] = []
    for product in products:
        if (product.status or "").upper() != "ACTIVE":
            continue
        analysis = analysis_by_entity.get(product.id)
        sales = qty_by_title.get(product.title) or {}
        items.append(
            {
                "id": str(product.id),
                "shopify_gid": product.shopify_gid,
                "title": product.title,
                "handle": product.handle,
                "score": analysis.score_total if analysis else None,
                "severity": analysis.severity if analysis else None,
                "main_issues": _main_issues(analysis.issues if analysis else None),
                "quantity_sold": int(sales.get("quantity_sold") or 0),
                "revenue": float(sales.get("revenue") or 0),
                "stock": product.total_inventory,
                "has_proposal": product.id in proposal_entities,
                "analysis_id": str(analysis.id) if analysis else None,
            }
        )

    items.sort(key=lambda x: (x["score"] is None, x["score"] or 0))
    return items


async def list_collection_seo_items(
    store: ShopifyStore,
    session: AsyncSession,
) -> list[dict[str, Any]]:
    collections = (
        await session.execute(
            select(ShopifyCollection).where(
                ShopifyCollection.shopify_store_id == store.id
            )
        )
    ).scalars().all()

    analyses = (
        await session.execute(
            select(SeoEntityAnalysis).where(
                SeoEntityAnalysis.shopify_store_id == store.id,
                SeoEntityAnalysis.entity_type == "collection",
            )
        )
    ).scalars().all()
    analysis_by_entity = {a.entity_id: a for a in analyses}

    proposals = (
        await session.execute(
            select(SeoOptimizationProposal).where(
                SeoOptimizationProposal.shopify_store_id == store.id,
                SeoOptimizationProposal.entity_type == "collection",
                SeoOptimizationProposal.status.in_(("draft", "approved")),
            )
        )
    ).scalars().all()
    proposal_entities = {p.entity_id for p in proposals}

    items: list[dict[str, Any]] = []
    for collection in collections:
        analysis = analysis_by_entity.get(collection.id)
        items.append(
            {
                "id": str(collection.id),
                "shopify_gid": collection.shopify_gid,
                "title": collection.title,
                "handle": collection.handle,
                "score": analysis.score_total if analysis else None,
                "severity": analysis.severity if analysis else None,
                "main_issues": _main_issues(analysis.issues if analysis else None),
                "products_count": collection.products_count,
                "has_proposal": collection.id in proposal_entities,
                "analysis_id": str(analysis.id) if analysis else None,
            }
        )

    items.sort(key=lambda x: (x["score"] is None, x["score"] or 0))
    return items


async def list_proposals(
    store: ShopifyStore,
    session: AsyncSession,
    *,
    status: str | None = None,
) -> list[SeoOptimizationProposal]:
    query = select(SeoOptimizationProposal).where(
        SeoOptimizationProposal.shopify_store_id == store.id,
        SeoOptimizationProposal.project_id == store.project_id,
    )
    if status:
        query = query.where(SeoOptimizationProposal.status == status)
    query = query.order_by(SeoOptimizationProposal.created_at.desc())
    result = await session.execute(query)
    return list(result.scalars().all())


async def get_analysis_detail(
    store: ShopifyStore,
    session: AsyncSession,
    entity_type: str,
    entity_id: UUID,
) -> SeoEntityAnalysis | None:
    result = await session.execute(
        select(SeoEntityAnalysis).where(
            SeoEntityAnalysis.shopify_store_id == store.id,
            SeoEntityAnalysis.entity_type == entity_type,
            SeoEntityAnalysis.entity_id == entity_id,
        )
    )
    return result.scalar_one_or_none()
