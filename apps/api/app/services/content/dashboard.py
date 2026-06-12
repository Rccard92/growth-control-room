import logging
from typing import Any

from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shopify import ShopifyStore

logger = logging.getLogger(__name__)


def build_empty_content_seo_dashboard() -> dict[str, Any]:
    return {
        "summary": {
            "total_issues": 0,
            "critical_issues": 0,
            "warnings": 0,
            "opportunities": 0,
            "content_opportunities": 0,
            "products_without_meta": 0,
            "collections_weak": 0,
            "articles_weak": 0,
            "has_synced_content": False,
            "content_entities_count": 0,
        },
        "issues": [],
        "opportunities": [],
        "top_product_opportunities": [],
        "top_collection_opportunities": [],
        "internal_linking_opportunities": [],
    }


def _issue_to_dict(issue) -> dict[str, Any]:
    return {
        "id": str(issue.id),
        "entity_type": issue.entity_type,
        "entity_id": str(issue.entity_id),
        "issue_type": issue.issue_type,
        "severity": issue.severity,
        "title": issue.title,
        "description": issue.description,
        "recommendation": issue.recommendation,
        "status": issue.status,
        "created_at": issue.created_at,
    }


def _opportunity_to_dict(opp) -> dict[str, Any]:
    return {
        "id": str(opp.id),
        "opportunity_type": opp.opportunity_type,
        "priority": opp.priority,
        "title": opp.title,
        "description": opp.description,
        "target_entity_type": opp.target_entity_type,
        "target_entity_id": str(opp.target_entity_id) if opp.target_entity_id else None,
        "suggested_keyword": opp.suggested_keyword,
        "search_intent": opp.search_intent,
        "suggested_products": opp.suggested_products,
        "suggested_collections": opp.suggested_collections,
        "reason": opp.reason,
        "status": opp.status,
        "created_at": opp.created_at,
    }


async def _build_content_seo_dashboard_inner(
    store: ShopifyStore,
    session: AsyncSession,
    *,
    list_limit: int = 50,
) -> dict[str, Any]:
    from sqlalchemy import func, select

    from app.models.content_seo import (
        ContentOpportunity,
        SeoAuditIssue,
        ShopifyArticle,
        ShopifyBlog,
        ShopifyCollection,
        ShopifyPage,
    )

    project_id = store.project_id
    store_id = store.id

    issues = (
        await session.execute(
            select(SeoAuditIssue)
            .where(
                SeoAuditIssue.project_id == project_id,
                SeoAuditIssue.shopify_store_id == store_id,
                SeoAuditIssue.status == "open",
            )
            .order_by(SeoAuditIssue.created_at.desc())
            .limit(list_limit)
        )
    ).scalars().all()

    opportunities = (
        await session.execute(
            select(ContentOpportunity)
            .where(
                ContentOpportunity.project_id == project_id,
                ContentOpportunity.shopify_store_id == store_id,
                ContentOpportunity.status == "new",
            )
            .order_by(ContentOpportunity.created_at.desc())
            .limit(list_limit)
        )
    ).scalars().all()

    total_issues = (
        await session.execute(
            select(func.count())
            .select_from(SeoAuditIssue)
            .where(
                SeoAuditIssue.project_id == project_id,
                SeoAuditIssue.shopify_store_id == store_id,
                SeoAuditIssue.status == "open",
            )
        )
    ).scalar_one()

    critical_issues = (
        await session.execute(
            select(func.count())
            .select_from(SeoAuditIssue)
            .where(
                SeoAuditIssue.project_id == project_id,
                SeoAuditIssue.shopify_store_id == store_id,
                SeoAuditIssue.status == "open",
                SeoAuditIssue.severity == "critical",
            )
        )
    ).scalar_one()

    warnings = (
        await session.execute(
            select(func.count())
            .select_from(SeoAuditIssue)
            .where(
                SeoAuditIssue.project_id == project_id,
                SeoAuditIssue.shopify_store_id == store_id,
                SeoAuditIssue.status == "open",
                SeoAuditIssue.severity == "warning",
            )
        )
    ).scalar_one()

    content_opportunities_count = (
        await session.execute(
            select(func.count())
            .select_from(ContentOpportunity)
            .where(
                ContentOpportunity.project_id == project_id,
                ContentOpportunity.shopify_store_id == store_id,
                ContentOpportunity.status == "new",
            )
        )
    ).scalar_one()

    products_without_meta = (
        await session.execute(
            select(func.count())
            .select_from(SeoAuditIssue)
            .where(
                SeoAuditIssue.project_id == project_id,
                SeoAuditIssue.shopify_store_id == store_id,
                SeoAuditIssue.status == "open",
                SeoAuditIssue.entity_type == "product",
                SeoAuditIssue.issue_type.in_(
                    ["missing_meta_title", "missing_meta_description"]
                ),
            )
        )
    ).scalar_one()

    collections_weak = (
        await session.execute(
            select(func.count())
            .select_from(SeoAuditIssue)
            .where(
                SeoAuditIssue.project_id == project_id,
                SeoAuditIssue.shopify_store_id == store_id,
                SeoAuditIssue.status == "open",
                SeoAuditIssue.entity_type == "collection",
            )
        )
    ).scalar_one()

    articles_weak = (
        await session.execute(
            select(func.count())
            .select_from(SeoAuditIssue)
            .where(
                SeoAuditIssue.project_id == project_id,
                SeoAuditIssue.shopify_store_id == store_id,
                SeoAuditIssue.status == "open",
                SeoAuditIssue.entity_type == "article",
            )
        )
    ).scalar_one()

    top_product_opportunities = [
        _opportunity_to_dict(o)
        for o in opportunities
        if o.opportunity_type in ("blog_topic", "product_improvement")
    ][:list_limit]

    top_collection_opportunities = [
        _opportunity_to_dict(o)
        for o in opportunities
        if o.opportunity_type in ("collection_improvement", "blog_topic")
        and o.target_entity_type == "collection"
    ][:list_limit]

    internal_linking_opportunities = [
        _opportunity_to_dict(o)
        for o in opportunities
        if o.opportunity_type == "internal_linking"
    ][:list_limit]

    content_entities = 0
    for model in (ShopifyCollection, ShopifyPage, ShopifyBlog, ShopifyArticle):
        content_entities += (
            await session.execute(
                select(func.count()).select_from(model).where(
                    model.shopify_store_id == store_id
                )
            )
        ).scalar_one()

    return {
        "summary": {
            "total_issues": total_issues,
            "critical_issues": critical_issues,
            "warnings": warnings,
            "opportunities": content_opportunities_count,
            "content_opportunities": content_opportunities_count,
            "products_without_meta": products_without_meta,
            "collections_weak": collections_weak,
            "articles_weak": articles_weak,
            "has_synced_content": content_entities > 0,
            "content_entities_count": content_entities,
        },
        "issues": [_issue_to_dict(i) for i in issues],
        "opportunities": [_opportunity_to_dict(o) for o in opportunities],
        "top_product_opportunities": top_product_opportunities,
        "top_collection_opportunities": top_collection_opportunities,
        "internal_linking_opportunities": internal_linking_opportunities,
    }


async def build_content_seo_dashboard(
    store: ShopifyStore,
    session: AsyncSession,
    *,
    list_limit: int = 50,
) -> dict[str, Any]:
    try:
        return await _build_content_seo_dashboard_inner(store, session, list_limit=list_limit)
    except (ProgrammingError, OperationalError) as exc:
        logger.warning(
            "Content SEO dashboard fallback empty for store %s: %s",
            store.shop_domain,
            str(exc).split("\n")[0],
        )
        await session.rollback()
        return build_empty_content_seo_dashboard()
