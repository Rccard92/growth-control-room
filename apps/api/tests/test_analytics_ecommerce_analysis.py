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
    ITEM_ECOMMERCE_BASE_DIMENSIONS,
    ITEM_ECOMMERCE_BASE_METRICS,
    ITEM_ECOMMERCE_CHECKOUT_METRICS,
    ITEM_ECOMMERCE_ID_ONLY_DIMENSIONS,
    ITEM_ECOMMERCE_NAME_ONLY_DIMENSIONS,
    _parse_item_report_rows,
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
    aggregates, unmatched, ambiguous = match_ga4_rows_to_pages(
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
    assert ambiguous == 0
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
    aggregates, unmatched, ambiguous = match_ga4_rows_to_pages(
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
    aggregates, unmatched, ambiguous = match_ga4_rows_to_pages(
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
    aggregates, unmatched, ambiguous = match_ga4_rows_to_pages(
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
    assert ambiguous == 1


def test_build_page_match_debug_matched_status() -> None:
    from app.services.growth_audit.ga4_item_product_matching import build_page_match_debug

    page = _build_product_page(project_id=uuid4(), run_id=uuid4())
    profiles = build_product_match_profiles([page])
    aggregate = {
        "matchedBy": "item_id",
        "itemViews": 50,
        "itemsAddedToCart": 5,
        "itemsPurchased": 1,
        "itemRevenue": 20.0,
    }
    debug = build_page_match_debug(
        profiles[0],
        aggregate=aggregate,
        rows=[],
    )
    assert debug["matchStatus"] == "matched"
    assert debug["candidateItems"] == []
    assert debug["shopifyKeys"]["productLegacyId"] == "123"


def test_build_page_match_debug_no_reliable_match() -> None:
    from app.services.growth_audit.ga4_item_product_matching import build_page_match_debug

    page = _build_product_page(project_id=uuid4(), run_id=uuid4(), title="Polline biologico")
    profiles = build_product_match_profiles([page])
    rows = [
        {
            "itemId": "999",
            "itemName": "Polline biologico premium",
            "itemVariant": "",
            "itemsViewed": 80,
            "itemsAddedToCart": 4,
            "itemsPurchased": 1,
            "itemRevenue": 15.0,
        }
    ]
    debug = build_page_match_debug(
        profiles[0],
        aggregate=None,
        rows=rows,
    )
    assert debug["matchStatus"] == "no_reliable_match"
    assert debug["shopifyKeys"]["titleNormalized"] == "polline biologico"
    assert len(debug["candidateItems"]) > 0
    assert debug["candidateItems"][0]["itemsViewed"] == 80


def test_candidate_items_do_not_affect_page_metrics() -> None:
    from app.services.growth_audit.ga4_item_product_matching import (
        build_page_match_debug,
        find_potential_unmatched_candidates_for_profile,
    )

    page = _build_product_page(project_id=uuid4(), run_id=uuid4(), title="Polline biologico")
    profiles = build_product_match_profiles([page])
    rows = [
        {
            "itemId": "999",
            "itemName": "Polline biologico extra",
            "itemVariant": "",
            "itemsViewed": 120,
            "itemsAddedToCart": 8,
            "itemsPurchased": 2,
            "itemRevenue": 40.0,
        }
    ]
    candidates = find_potential_unmatched_candidates_for_profile(profiles[0], rows)
    metadata = _build_page_ga4_ecommerce_metadata(
        period_days=30,
        aggregate=None,
        synced_at="2026-06-13T10:00:00Z",
        match_debug=build_page_match_debug(profiles[0], aggregate=None, rows=rows),
    )
    assert len(candidates) > 0
    assert metadata["itemViews"] == 0
    assert metadata["itemsPurchased"] == 0
    assert metadata["itemRevenue"] == 0
    assert metadata["matchDebug"]["candidateItems"][0]["itemsViewed"] == 120


def test_summary_includes_matching_mode_strict() -> None:
    page = _build_product_page(project_id=uuid4(), run_id=uuid4())
    page.page_metadata = {
        "ga4Ecommerce": _build_page_ga4_ecommerce_metadata(
            period_days=30,
            aggregate={"matchedBy": "item_id", "itemViews": 10, "itemsAddedToCart": 1},
            synced_at="2026-06-13T10:00:00Z",
        )
    }
    summary = _compute_run_ga4_ecommerce_summary(
        [page],
        period_days=30,
        synced_at="2026-06-13T10:00:00Z",
        unmatched_items=2,
        ambiguous_items=1,
    )
    assert summary["matchingMode"] == "strict"
    assert summary["ambiguousItemsCount"] == 1
    assert summary["unmatchedItems"] == 2
    assert summary["matchedProducts"] == 1


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


def _base_report_payload(
    *,
    item_id: str = "123",
    item_name: str = "Prodotto",
    item_variant: str = "",
    items_viewed: str = "10",
    items_added: str = "2",
    items_purchased: str = "1",
    item_revenue: str = "15.5",
    dimensions: list[str] | None = None,
) -> dict:
    dims = dimensions or ITEM_ECOMMERCE_BASE_DIMENSIONS
    dimension_values = []
    if "itemId" in dims:
        dimension_values.append({"value": item_id})
    if "itemName" in dims:
        dimension_values.append({"value": item_name})
    if "itemVariant" in dims:
        dimension_values.append({"value": item_variant})
    return {
        "rows": [
            {
                "dimensionValues": dimension_values,
                "metricValues": [
                    {"value": items_viewed},
                    {"value": items_added},
                    {"value": items_purchased},
                    {"value": item_revenue},
                ],
            }
        ]
    }


def _checkout_report_payload(*, items_checked_out: str = "3") -> dict:
    return {
        "rows": [
            {
                "dimensionValues": [
                    {"value": "123"},
                    {"value": "Prodotto"},
                ],
                "metricValues": [{"value": items_checked_out}],
            }
        ]
    }


def test_base_metrics_do_not_include_item_view_events() -> None:
    assert "itemViewEvents" not in ITEM_ECOMMERCE_BASE_METRICS
    assert "itemViewEvents" not in ITEM_ECOMMERCE_CHECKOUT_METRICS


def test_fetch_ga4_item_ecommerce_report_base_success() -> None:
    async def run() -> None:
        base_payload = _base_report_payload()
        checkout_payload = _checkout_report_payload()

        with patch(
            "app.services.google.analytics_client._run_ga4_item_report",
            new=AsyncMock(
                side_effect=[
                    base_payload,
                    checkout_payload,
                    {"_metric_incompatible": True, "error": {}},
                ]
            ),
        ) as mock_report:
            result = await fetch_ga4_item_ecommerce_report(
                "access-token",
                property_id="123456789",
                start_date=datetime.now(UTC).date(),
                end_date=datetime.now(UTC).date(),
            )

        assert result["dimensionsUsed"] == ITEM_ECOMMERCE_BASE_DIMENSIONS
        assert ITEM_ECOMMERCE_BASE_METRICS[0] in result["metricsUsed"]
        assert "itemsCheckedOut" in result["metricsUsed"]
        assert result["rows"][0]["itemId"] == "123"
        assert result["rows"][0]["itemsViewed"] == 10
        assert result["rows"][0]["itemsCheckedOut"] == 3
        first_call = mock_report.await_args_list[0].kwargs
        assert first_call["dimensions"] == ITEM_ECOMMERCE_BASE_DIMENSIONS
        assert first_call["metrics"] == ITEM_ECOMMERCE_BASE_METRICS

    asyncio.run(run())


def test_fetch_ga4_item_ecommerce_report_checkout_failure_keeps_base_valid() -> None:
    async def run() -> None:
        base_payload = _base_report_payload()

        with patch(
            "app.services.google.analytics_client._run_ga4_item_report",
            new=AsyncMock(
                side_effect=[
                    base_payload,
                    {"_metric_incompatible": True, "error": {}},
                    {"_metric_incompatible": True, "error": {}},
                ]
            ),
        ):
            result = await fetch_ga4_item_ecommerce_report(
                "access-token",
                property_id="123456789",
                start_date=datetime.now(UTC).date(),
                end_date=datetime.now(UTC).date(),
            )

        assert result["rows"][0]["itemsViewed"] == 10
        assert result["rows"][0]["itemsCheckedOut"] == 0
        assert "itemsCheckedOut" in result["missingMetrics"]

    asyncio.run(run())


def test_fetch_ga4_item_ecommerce_report_variant_failure_keeps_base_valid() -> None:
    async def run() -> None:
        base_payload = _base_report_payload()
        checkout_payload = _checkout_report_payload()

        with patch(
            "app.services.google.analytics_client._run_ga4_item_report",
            new=AsyncMock(
                side_effect=[
                    base_payload,
                    checkout_payload,
                    {"_metric_incompatible": True, "error": {}},
                ]
            ),
        ):
            result = await fetch_ga4_item_ecommerce_report(
                "access-token",
                property_id="123456789",
                start_date=datetime.now(UTC).date(),
                end_date=datetime.now(UTC).date(),
            )

        assert result["rows"][0]["itemsPurchased"] == 1
        assert result["dimensionsUsed"] == ITEM_ECOMMERCE_BASE_DIMENSIONS

    asyncio.run(run())


def test_fetch_ga4_item_ecommerce_report_fallback_item_name() -> None:
    async def run() -> None:
        incompatible = {"_metric_incompatible": True, "error": {}}
        name_payload = _base_report_payload(
            item_id="",
            dimensions=ITEM_ECOMMERCE_NAME_ONLY_DIMENSIONS,
        )
        checkout_payload = _checkout_report_payload()

        with patch(
            "app.services.google.analytics_client._run_ga4_item_report",
            new=AsyncMock(
                side_effect=[
                    incompatible,
                    name_payload,
                    checkout_payload,
                    {"_metric_incompatible": True, "error": {}},
                ]
            ),
        ) as mock_report:
            result = await fetch_ga4_item_ecommerce_report(
                "access-token",
                property_id="123456789",
                start_date=datetime.now(UTC).date(),
                end_date=datetime.now(UTC).date(),
            )

        assert result["dimensionsUsed"] == ITEM_ECOMMERCE_NAME_ONLY_DIMENSIONS
        assert result["rows"][0]["itemName"] == "Prodotto"
        second_call = mock_report.await_args_list[1].kwargs
        assert second_call["dimensions"] == ITEM_ECOMMERCE_NAME_ONLY_DIMENSIONS

    asyncio.run(run())


def test_fetch_ga4_item_ecommerce_report_fallback_item_id() -> None:
    async def run() -> None:
        incompatible = {"_metric_incompatible": True, "error": {}}
        id_payload = _base_report_payload(
            item_name="",
            dimensions=ITEM_ECOMMERCE_ID_ONLY_DIMENSIONS,
        )
        checkout_payload = {
            "rows": [
                {
                    "dimensionValues": [{"value": "123"}],
                    "metricValues": [{"value": "2"}],
                }
            ]
        }

        with patch(
            "app.services.google.analytics_client._run_ga4_item_report",
            new=AsyncMock(
                side_effect=[
                    incompatible,
                    incompatible,
                    id_payload,
                    checkout_payload,
                    {"_metric_incompatible": True, "error": {}},
                ]
            ),
        ):
            result = await fetch_ga4_item_ecommerce_report(
                "access-token",
                property_id="123456789",
                start_date=datetime.now(UTC).date(),
                end_date=datetime.now(UTC).date(),
            )

        assert result["dimensionsUsed"] == ITEM_ECOMMERCE_ID_ONLY_DIMENSIONS
        assert result["rows"][0]["itemId"] == "123"

    asyncio.run(run())


def test_fetch_ga4_item_ecommerce_report_empty_rows_success() -> None:
    async def run() -> None:
        empty_payload = {"rows": []}
        checkout_payload = {"rows": []}

        with patch(
            "app.services.google.analytics_client._run_ga4_item_report",
            new=AsyncMock(side_effect=[empty_payload, checkout_payload, {"_metric_incompatible": True, "error": {}}]),
        ):
            result = await fetch_ga4_item_ecommerce_report(
                "access-token",
                property_id="123456789",
                start_date=datetime.now(UTC).date(),
                end_date=datetime.now(UTC).date(),
            )

        assert result["rows"] == []

    asyncio.run(run())


def test_fetch_ga4_item_ecommerce_report_raises_when_all_attempts_fail() -> None:
    async def run() -> None:
        incompatible = {"_metric_incompatible": True, "error": {}}
        with (
            patch(
                "app.services.google.analytics_client._run_ga4_item_report",
                new=AsyncMock(return_value=incompatible),
            ),
            pytest.raises(GoogleApiRequestError, match="metriche ecommerce item-level"),
        ):
            await fetch_ga4_item_ecommerce_report(
                "access-token",
                property_id="123456789",
                start_date=datetime.now(UTC).date(),
                end_date=datetime.now(UTC).date(),
            )

    asyncio.run(run())


def test_parse_item_report_rows_supports_variable_dimensions() -> None:
    one_dim_payload = _base_report_payload(dimensions=["itemId"], item_name="")
    two_dim_payload = _base_report_payload()
    three_dim_payload = {
        "rows": [
            {
                "dimensionValues": [
                    {"value": "123"},
                    {"value": "Prodotto"},
                    {"value": "500g"},
                ],
                "metricValues": [
                    {"value": "8"},
                    {"value": "1"},
                    {"value": "0"},
                    {"value": "9.5"},
                ],
            }
        ]
    }

    one_dim_rows = _parse_item_report_rows(
        one_dim_payload,
        dimensions=["itemId"],
        metrics=ITEM_ECOMMERCE_BASE_METRICS,
    )
    two_dim_rows = _parse_item_report_rows(
        two_dim_payload,
        dimensions=ITEM_ECOMMERCE_BASE_DIMENSIONS,
        metrics=ITEM_ECOMMERCE_BASE_METRICS,
    )
    three_dim_rows = _parse_item_report_rows(
        three_dim_payload,
        dimensions=["itemId", "itemName", "itemVariant"],
        metrics=ITEM_ECOMMERCE_BASE_METRICS,
    )

    assert one_dim_rows[0]["itemId"] == "123"
    assert one_dim_rows[0]["itemName"] == ""
    assert two_dim_rows[0]["itemName"] == "Prodotto"
    assert three_dim_rows[0]["itemVariant"] == "500g"


def test_analyze_updates_zero_metadata_when_rows_empty() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        page = _build_product_page(project_id=project_id, run_id=run_id)
        audit_run = _build_run(project_id, run_id)
        project = MagicMock()
        project.google_analytics_property_id = "properties/123456789"

        session = AsyncMock()
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
                new=AsyncMock(return_value={"rows": []}),
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
        assert result["findings_created"] == 0
        assert "Nessun dato item-level" in result["message"]
        assert page.page_metadata["ga4Ecommerce"]["itemViews"] == 0
        assert page.page_metadata["ga4Ecommerce"]["matchedBy"] == "none"
        assert audit_run.summary["ga4Ecommerce"]["productsWithoutFunnelData"] == 1

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
