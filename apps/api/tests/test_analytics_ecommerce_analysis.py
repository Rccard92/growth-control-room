"""Tests for Growth Audit GA4 ecommerce funnel analysis."""

from __future__ import annotations

import asyncio
import os
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

from app.api.routes.growth_audit import analyze_growth_audit_analytics_ecommerce_endpoint
from app.models.growth_audit import GrowthAuditPage, GrowthAuditRun
from app.schemas.growth_audit import GrowthAuditGa4EcommerceAnalysisRequest
from app.services.growth_audit.analytics_ecommerce_analysis import (
    _build_page_ga4_ecommerce_metadata,
    _build_ga4_ecommerce_findings,
    _compute_run_ga4_ecommerce_summary,
    analyze_growth_audit_analytics_ecommerce,
)
from app.services.growth_audit.exceptions import GrowthAuditValidationError
from app.services.growth_audit.ga4_item_product_matching import (
    build_product_match_profiles,
    match_ga4_rows_to_pages,
)
from app.services.google.exceptions import GoogleApiRequestError
from app.services.google.analytics_client import (
    ITEM_ECOMMERCE_FALLBACK_METRICS,
    fetch_ga4_item_ecommerce_report,
)


def _build_run(project_id, run_id=None) -> GrowthAuditRun:
    run_id = run_id or uuid4()
    now = datetime.now(UTC)
    return GrowthAuditRun(
        id=run_id,
        project_id=project_id,
        root_url="https://example.com",
        normalized_domain="example.com",
        status="completed",
        phase="completed",
        audit_mode="full_site_mvp",
        provider="openai",
        progress_percent=100,
        pages_discovered=1,
        pages_classified=1,
        pages_analyzed=1,
        pages_failed=0,
        site_score=70,
        summary={},
        config={},
        created_at=now,
        updated_at=now,
    )


def _build_product_page(
    *,
    project_id,
    run_id,
    page_id=None,
    product_gid: str = "gid://shopify/Product/123",
    title: str = "Polline biologico",
) -> GrowthAuditPage:
    page_id = page_id or uuid4()
    now = datetime.now(UTC)
    return GrowthAuditPage(
        id=page_id,
        run_id=run_id,
        project_id=project_id,
        url="https://example.com/products/polline",
        normalized_url="https://example.com/products/polline",
        path="/products/polline",
        page_type="product",
        source="shopify_product",
        status="analyzed",
        priority="normal",
        title=title,
        score=82,
        http_status=200,
        source_entity_type="shopify_product",
        source_entity_gid=product_gid,
        source_entity_title=title,
        source_entity_handle="polline",
        created_at=now,
        updated_at=now,
    )


def test_match_by_product_legacy_id() -> None:
    page = _build_product_page(project_id=uuid4(), run_id=uuid4())
    profiles = build_product_match_profiles([page])
    aggregates, unmatched = match_ga4_rows_to_pages(
        profiles,
        [
            {
                "itemId": "123",
                "itemName": "Polline biologico",
                "itemVariant": "",
                "itemsViewed": 80,
                "itemViewEvents": 60,
                "itemsAddedToCart": 10,
                "itemsCheckedOut": 5,
                "itemsPurchased": 2,
                "itemRevenue": 48.5,
            }
        ],
    )
    assert unmatched == 0
    assert page.id in aggregates
    assert aggregates[page.id]["itemViews"] == 80
    assert aggregates[page.id]["matchedBy"] == "item_id"


def test_match_by_variant_id() -> None:
    page = _build_product_page(project_id=uuid4(), run_id=uuid4())
    profiles = build_product_match_profiles(
        [page],
        variant_data_by_gid={
            "gid://shopify/Product/123": {
                "variantLegacyIds": ["456"],
                "skus": ["SKU-456"],
            }
        },
    )
    aggregates, unmatched = match_ga4_rows_to_pages(
        profiles,
        [
            {
                "itemId": "456",
                "itemName": "Variant",
                "itemVariant": "500g",
                "itemsViewed": 20,
                "itemsAddedToCart": 4,
                "itemsPurchased": 1,
                "itemRevenue": 12.0,
            }
        ],
    )
    assert unmatched == 0
    assert aggregates[page.id]["matchedBy"] == "variant_id"


def test_match_by_normalized_item_name() -> None:
    page = _build_product_page(project_id=uuid4(), run_id=uuid4(), title="Miele Bio")
    profiles = build_product_match_profiles([page])
    aggregates, unmatched = match_ga4_rows_to_pages(
        profiles,
        [
            {
                "itemId": "(not set)",
                "itemName": "miele bio",
                "itemVariant": "",
                "itemsViewed": 30,
                "itemsAddedToCart": 2,
                "itemsPurchased": 0,
                "itemRevenue": 0,
            }
        ],
    )
    assert unmatched == 0
    assert aggregates[page.id]["matchedBy"] == "item_name"


def test_ambiguous_item_name_does_not_assign() -> None:
    project_id = uuid4()
    run_id = uuid4()
    pages = [
        _build_product_page(project_id=project_id, run_id=run_id, page_id=uuid4(), title="Miele Bio"),
        _build_product_page(
            project_id=project_id,
            run_id=run_id,
            page_id=uuid4(),
            product_gid="gid://shopify/Product/999",
            title="Miele Bio",
        ),
    ]
    profiles = build_product_match_profiles(pages)
    aggregates, unmatched = match_ga4_rows_to_pages(
        profiles,
        [
            {
                "itemId": "",
                "itemName": "Miele Bio",
                "itemVariant": "",
                "itemsViewed": 40,
                "itemsAddedToCart": 3,
                "itemsPurchased": 1,
                "itemRevenue": 20,
            }
        ],
    )
    assert aggregates == {}
    assert unmatched == 1


def test_build_page_metadata_zero_safe_rates() -> None:
    metadata = _build_page_ga4_ecommerce_metadata(
        period_days=30,
        aggregate=None,
        synced_at="2026-06-13T10:00:00Z",
    )
    assert metadata["itemViews"] == 0
    assert metadata["viewToCartRate"] == 0
    assert metadata["matchedBy"] == "none"


def test_compute_run_summary_aggregates() -> None:
    page = _build_product_page(project_id=uuid4(), run_id=uuid4())
    page.page_metadata = {
        "ga4Ecommerce": {
            "itemViews": 100,
            "itemsAddedToCart": 15,
            "itemsCheckedOut": 8,
            "itemsPurchased": 4,
            "itemRevenue": 120.0,
            "viewToCartRate": 0.15,
            "cartToPurchaseRate": 0.27,
            "matchedBy": "item_id",
        }
    }
    summary = _compute_run_ga4_ecommerce_summary(
        [page],
        period_days=30,
        synced_at="2026-06-13T10:00:00Z",
        unmatched_items=2,
    )
    assert summary["totalItemViews"] == 100
    assert summary["productsWithFunnelData"] == 1
    assert summary["unmatchedItems"] == 2


def test_build_ga4_ecommerce_findings_limited_to_ten() -> None:
    pages = [
        _build_product_page(project_id=uuid4(), run_id=uuid4(), page_id=uuid4())
        for _ in range(12)
    ]
    for page in pages:
        page.page_metadata = {
            "ga4Ecommerce": {
                "itemViews": 120,
                "itemsAddedToCart": 0,
                "itemsPurchased": 0,
                "matchedBy": "item_id",
            }
        }
    findings = _build_ga4_ecommerce_findings(pages, [])
    assert len(findings) <= 10


def test_analyze_requires_ga4_property() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        audit_run = _build_run(project_id, run_id)
        project = MagicMock()
        project.google_analytics_property_id = None
        session = AsyncMock()

        with (
            patch(
                "app.services.growth_audit.analytics_ecommerce_analysis.get_growth_audit_run",
                new=AsyncMock(return_value=audit_run),
            ),
            patch(
                "app.services.growth_audit.analytics_ecommerce_analysis.get_project_in_default_workspace",
                new=AsyncMock(return_value=project),
            ),
            pytest.raises(GrowthAuditValidationError, match="Seleziona prima"),
        ):
            await analyze_growth_audit_analytics_ecommerce(
                session,
                project_id=project_id,
                run_id=run_id,
            )

    asyncio.run(run())


def test_analyze_updates_page_metadata_and_summary() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        page = _build_product_page(project_id=project_id, run_id=run_id)
        audit_run = _build_run(project_id, run_id)
        project = MagicMock()
        project.google_analytics_property_id = "123456789"

        session = AsyncMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.flush = AsyncMock()
        findings_result = MagicMock()
        findings_result.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=findings_result)

        with (
            patch(
                "app.services.growth_audit.analytics_ecommerce_analysis.get_growth_audit_run",
                new=AsyncMock(return_value=audit_run),
            ),
            patch(
                "app.services.growth_audit.analytics_ecommerce_analysis.get_project_in_default_workspace",
                new=AsyncMock(return_value=project),
            ),
            patch(
                "app.services.growth_audit.analytics_ecommerce_analysis.get_valid_google_access_token",
                new=AsyncMock(return_value="access-token"),
            ),
            patch(
                "app.services.growth_audit.analytics_ecommerce_analysis.fetch_ga4_item_ecommerce_report",
                new=AsyncMock(
                    return_value={
                        "rows": [
                            {
                                "itemId": "123",
                                "itemName": "Polline biologico",
                                "itemVariant": "",
                                "itemsViewed": 90,
                                "itemViewEvents": 70,
                                "itemsAddedToCart": 12,
                                "itemsCheckedOut": 6,
                                "itemsPurchased": 3,
                                "itemRevenue": 72.5,
                            }
                        ]
                    }
                ),
            ),
            patch(
                "app.services.growth_audit.analytics_ecommerce_analysis.list_growth_audit_pages",
                new=AsyncMock(return_value=[page]),
            ),
            patch(
                "app.services.growth_audit.analytics_ecommerce_analysis.get_shopify_store_for_project",
                new=AsyncMock(return_value=None),
            ),
            patch(
                "app.services.growth_audit.analytics_ecommerce_analysis.create_growth_audit_event",
                new=AsyncMock(),
            ),
        ):
            result = await analyze_growth_audit_analytics_ecommerce(
                session,
                project_id=project_id,
                run_id=run_id,
                days=30,
            )

        assert result["pages_updated"] == 1
        assert page.page_metadata["ga4Ecommerce"]["itemViews"] == 90
        assert page.page_metadata["ga4Ecommerce"]["matchedBy"] == "item_id"
        assert audit_run.summary["ga4Ecommerce"]["totalItemViews"] == 90
        session.commit.assert_awaited_once()

    asyncio.run(run())


def test_fetch_ga4_item_ecommerce_report_fallback_metrics() -> None:
    async def run() -> None:
        incompatible = {"_metric_incompatible": True, "error": {}}
        fallback_payload = {
            "rows": [
                {
                    "dimensionValues": [
                        {"value": "123"},
                        {"value": "Prodotto"},
                        {"value": ""},
                    ],
                    "metricValues": [
                        {"value": "10"},
                        {"value": "2"},
                        {"value": "1"},
                        {"value": "15.5"},
                    ],
                }
            ]
        }

        with patch(
            "app.services.google.analytics_client._run_ga4_item_report",
            new=AsyncMock(side_effect=[incompatible, fallback_payload]),
        ):
            result = await fetch_ga4_item_ecommerce_report(
                "access-token",
                property_id="123456789",
                start_date=datetime.now(UTC).date(),
                end_date=datetime.now(UTC).date(),
            )

        assert result["metricsUsed"] == ITEM_ECOMMERCE_FALLBACK_METRICS
        assert result["rows"][0]["itemId"] == "123"
        assert result["rows"][0]["itemsPurchased"] == 1

    asyncio.run(run())


def test_fetch_ga4_item_ecommerce_report_raises_when_incompatible() -> None:
    async def run() -> None:
        incompatible = {"_metric_incompatible": True, "error": {}}
        with (
            patch(
                "app.services.google.analytics_client._run_ga4_item_report",
                new=AsyncMock(return_value=incompatible),
            ),
            pytest.raises(GoogleApiRequestError, match="non compatibile"),
        ):
            await fetch_ga4_item_ecommerce_report(
                "access-token",
                property_id="123456789",
                start_date=datetime.now(UTC).date(),
                end_date=datetime.now(UTC).date(),
            )

    asyncio.run(run())


def test_ga4_ecommerce_route_returns_422_without_property() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        session = AsyncMock()

        with (
            patch(
                "app.api.routes.growth_audit.get_project_in_default_workspace",
                new=AsyncMock(),
            ),
            patch(
                "app.api.routes.growth_audit.analyze_growth_audit_analytics_ecommerce",
                new=AsyncMock(
                    side_effect=GrowthAuditValidationError(
                        "Seleziona prima una proprietà GA4 per leggere eventi ecommerce prodotto."
                    )
                ),
            ),
            pytest.raises(HTTPException) as exc,
        ):
            await analyze_growth_audit_analytics_ecommerce_endpoint(
                project_id,
                run_id,
                GrowthAuditGa4EcommerceAnalysisRequest(days=30),
                session,
            )

        assert exc.value.status_code == 422

    asyncio.run(run())
