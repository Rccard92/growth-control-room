"""Growth Audit context for DataForSEO site cost estimates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.growth_audit import GrowthAuditPage, GrowthAuditRun


def _is_product_page(page: GrowthAuditPage) -> bool:
    return page.page_type == "product" or page.source_entity_type == "shopify_product"


def _get_gsc_top_queries(page: GrowthAuditPage) -> list[Any]:
    metadata = page.page_metadata or {}
    search_console = metadata.get("searchConsole")
    if not isinstance(search_console, dict):
        return []
    top_queries = search_console.get("topQueries")
    return top_queries if isinstance(top_queries, list) else []


def _get_shopify_sales(page: GrowthAuditPage) -> float:
    metadata = page.page_metadata or {}
    commerce = metadata.get("shopifyCommerce")
    if not isinstance(commerce, dict):
        return 0.0
    sales = commerce.get("sales")
    try:
        return float(sales or 0)
    except (TypeError, ValueError):
        return 0.0


def _get_gsc_impressions(page: GrowthAuditPage) -> float:
    metadata = page.page_metadata or {}
    search_console = metadata.get("searchConsole")
    if not isinstance(search_console, dict):
        return 0.0
    impressions = search_console.get("impressions")
    try:
        return float(impressions or 0)
    except (TypeError, ValueError):
        return 0.0


def _economic_priority_score(page: GrowthAuditPage) -> float:
    return _get_gsc_impressions(page) + _get_shopify_sales(page) * 100.0


@dataclass
class GrowthAuditProductContext:
    product_pages_count: int
    pages_with_gsc_queries: int
    avg_queries_per_page: float
    top_product_pages_count: int


async def load_run_product_context(
    session: AsyncSession,
    *,
    run_id: UUID,
    project_id: UUID,
    top_n: int | None = None,
) -> GrowthAuditProductContext:
    run_result = await session.execute(
        select(GrowthAuditRun).where(
            GrowthAuditRun.id == run_id,
            GrowthAuditRun.project_id == project_id,
        )
    )
    run = run_result.scalar_one_or_none()
    if run is None:
        raise ValueError("Growth Audit run non trovato per questo progetto.")

    pages_result = await session.execute(
        select(GrowthAuditPage).where(
            GrowthAuditPage.run_id == run_id,
            GrowthAuditPage.project_id == project_id,
        )
    )
    pages = list(pages_result.scalars().all())
    product_pages = [page for page in pages if _is_product_page(page)]

    if top_n is not None and top_n > 0:
        product_pages = sorted(
            product_pages,
            key=_economic_priority_score,
            reverse=True,
        )[:top_n]

    query_counts: list[int] = []
    pages_with_gsc = 0
    for page in product_pages:
        top_queries = _get_gsc_top_queries(page)
        if top_queries:
            pages_with_gsc += 1
            query_counts.append(len(top_queries))

    avg_queries = (
        sum(query_counts) / len(query_counts) if query_counts else 0.0
    )

    return GrowthAuditProductContext(
        product_pages_count=len(product_pages),
        pages_with_gsc_queries=pages_with_gsc,
        avg_queries_per_page=avg_queries,
        top_product_pages_count=len(product_pages),
    )
