from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_seo import ContentOpportunity, SeoAuditIssue, ShopifyArticle, ShopifyBlog, ShopifyCollection, ShopifyPage
from app.models.shopify import ShopifyProduct, ShopifyStore


def _issue_to_dict(issue: SeoAuditIssue) -> dict[str, Any]:
    return {
        "id": str(issue.id),
        "entityType": issue.entity_type,
        "entityId": str(issue.entity_id),
        "issueType": issue.issue_type,
        "severity": issue.severity,
        "title": issue.title,
        "description": issue.description,
        "recommendation": issue.recommendation,
        "status": issue.status,
        "createdAt": issue.created_at.isoformat() if issue.created_at else None,
    }


def _opportunity_to_dict(opp: ContentOpportunity) -> dict[str, Any]:
    return {
        "id": str(opp.id),
        "opportunityType": opp.opportunity_type,
        "priority": opp.priority,
        "title": opp.title,
        "description": opp.description,
        "targetEntityType": opp.target_entity_type,
        "targetEntityId": str(opp.target_entity_id) if opp.target_entity_id else None,
        "suggestedKeyword": opp.suggested_keyword,
        "searchIntent": opp.search_intent,
        "suggestedProducts": opp.suggested_products,
        "suggestedCollections": opp.suggested_collections,
        "reason": opp.reason,
        "status": opp.status,
        "createdAt": opp.created_at.isoformat() if opp.created_at else None,
    }


async def build_content_seo_dashboard(
    store: ShopifyStore,
    session: AsyncSession,
    *,
    list_limit: int = 50,
) -> dict[str, Any]:
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
            "totalIssues": total_issues,
            "criticalIssues": critical_issues,
            "warnings": warnings,
            "opportunities": content_opportunities_count,
            "contentOpportunities": content_opportunities_count,
            "productsWithoutMeta": products_without_meta,
            "collectionsWeak": collections_weak,
            "articlesWeak": articles_weak,
            "hasSyncedContent": content_entities > 0,
            "contentEntitiesCount": content_entities,
        },
        "issues": [_issue_to_dict(i) for i in issues],
        "opportunities": [_opportunity_to_dict(o) for o in opportunities],
        "topProductOpportunities": top_product_opportunities,
        "topCollectionOpportunities": top_collection_opportunities,
        "internalLinkingOpportunities": internal_linking_opportunities,
    }
