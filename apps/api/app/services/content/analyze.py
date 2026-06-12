from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_seo import (
    ContentOpportunity,
    SeoAuditIssue,
    ShopifyArticle,
    ShopifyCollection,
    ShopifyPage,
)
from app.models.shopify import ShopifyProduct, ShopifyStore
from app.services.content.opportunity_engine import generate_content_opportunities
from app.services.content.seo_audit import generate_seo_audit_issues


@dataclass
class AnalyzeResult:
    issues_created: int = 0
    opportunities_created: int = 0
    critical_issues: int = 0
    high_priority_opportunities: int = 0


async def _load_content_entities(
    session: AsyncSession,
    store_id: UUID,
) -> tuple[list[ShopifyProduct], list[ShopifyCollection], list[ShopifyPage], list[ShopifyArticle]]:
    products = (
        await session.execute(select(ShopifyProduct).where(ShopifyProduct.shopify_store_id == store_id))
    ).scalars().all()
    collections = (
        await session.execute(
            select(ShopifyCollection).where(ShopifyCollection.shopify_store_id == store_id)
        )
    ).scalars().all()
    pages = (
        await session.execute(select(ShopifyPage).where(ShopifyPage.shopify_store_id == store_id))
    ).scalars().all()
    articles = (
        await session.execute(select(ShopifyArticle).where(ShopifyArticle.shopify_store_id == store_id))
    ).scalars().all()
    return list(products), list(collections), list(pages), list(articles)


async def run_content_seo_analyze(
    store: ShopifyStore,
    session: AsyncSession,
) -> AnalyzeResult:
    products, collections, pages, articles = await _load_content_entities(session, store.id)

    issue_drafts = await generate_seo_audit_issues(
        session,
        store.id,
        products,
        collections,
        pages,
        articles,
    )
    opportunity_drafts = await generate_content_opportunities(
        session,
        store.id,
        products,
        collections,
        articles,
        issue_drafts,
    )

    await session.execute(
        delete(SeoAuditIssue).where(
            SeoAuditIssue.project_id == store.project_id,
            SeoAuditIssue.shopify_store_id == store.id,
            SeoAuditIssue.status == "open",
        )
    )
    await session.execute(
        delete(ContentOpportunity).where(
            ContentOpportunity.project_id == store.project_id,
            ContentOpportunity.shopify_store_id == store.id,
            ContentOpportunity.status == "new",
        )
    )

    result = AnalyzeResult()
    seen_issues: set[tuple[Any, ...]] = set()

    for draft in issue_drafts:
        key = (
            draft["entity_type"],
            draft["entity_id"],
            draft["issue_type"],
        )
        if key in seen_issues:
            continue
        seen_issues.add(key)

        issue = SeoAuditIssue(
            project_id=store.project_id,
            shopify_store_id=store.id,
            entity_type=draft["entity_type"],
            entity_id=draft["entity_id"],
            issue_type=draft["issue_type"],
            severity=draft["severity"],
            title=draft["title"],
            description=draft["description"],
            recommendation=draft["recommendation"],
            status="open",
        )
        session.add(issue)
        result.issues_created += 1
        if draft["severity"] == "critical":
            result.critical_issues += 1

    seen_opps: set[tuple[Any, ...]] = set()
    for draft in opportunity_drafts:
        key = (
            draft["opportunity_type"],
            draft["title"],
            draft.get("target_entity_id"),
        )
        if key in seen_opps:
            continue
        seen_opps.add(key)

        opp = ContentOpportunity(
            project_id=store.project_id,
            shopify_store_id=store.id,
            opportunity_type=draft["opportunity_type"],
            priority=draft["priority"],
            title=draft["title"],
            description=draft["description"],
            target_entity_type=draft.get("target_entity_type"),
            target_entity_id=draft.get("target_entity_id"),
            suggested_keyword=draft.get("suggested_keyword"),
            search_intent=draft.get("search_intent"),
            suggested_products=draft.get("suggested_products"),
            suggested_collections=draft.get("suggested_collections"),
            reason=draft["reason"],
            status="new",
        )
        session.add(opp)
        result.opportunities_created += 1
        if draft["priority"] == "high":
            result.high_priority_opportunities += 1

    await session.commit()
    return result
