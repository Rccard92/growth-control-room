"""Tests for Growth Audit Shopify commerce analysis."""

from __future__ import annotations

import asyncio
import os
from datetime import UTC, date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

from app.api.routes.growth_audit import analyze_growth_audit_shopify_commerce_endpoint
from app.models.growth_audit import GrowthAuditFinding, GrowthAuditPage, GrowthAuditRun
from app.schemas.growth_audit import GrowthAuditShopifyCommerceAnalysisRequest
from app.services.growth_audit.exceptions import GrowthAuditValidationError
from app.services.growth_audit.shopify_commerce_analysis import (
    _build_page_commerce_metadata,
    _build_shopify_commerce_findings,
    _compute_run_commerce_summary,
    analyze_growth_audit_shopify_commerce,
)
from app.services.shopify.exceptions import (
    ShopifyIntegrationNotConnectedError,
    ShopifyIntegrationPermissionError,
)
from app.services.shopify.shopify_commerce_client import _aggregate_line_items


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
    product_gid: str = "gid://shopify/Product/1",
) -> GrowthAuditPage:
    page_id = page_id or uuid4()
    now = datetime.now(UTC)
    return GrowthAuditPage(
        id=page_id,
        run_id=run_id,
        project_id=project_id,
        url="https://example.com/products/a",
        normalized_url="https://example.com/products/a",
        path="/products/a",
        page_type="product",
        source="shopify_product",
        status="analyzed",
        priority="normal",
        title="Prodotto A",
        score=82,
        http_status=200,
        source_entity_type="shopify_product",
        source_entity_gid=product_gid,
        source_entity_title="Prodotto A",
        created_at=now,
        updated_at=now,
    )


def _sample_order(
    *,
    order_id: str,
    created_at: str,
    product_gid: str,
    quantity: int,
    amount: str,
    cancelled: bool = False,
) -> dict:
    return {
        "id": order_id,
        "createdAt": created_at,
        "cancelledAt": "2026-06-01T10:00:00Z" if cancelled else None,
        "lineItems": {
            "nodes": [
                {
                    "quantity": quantity,
                    "product": {"id": product_gid},
                    "discountedTotalSet": {
                        "shopMoney": {"amount": amount, "currencyCode": "EUR"},
                    },
                    "originalTotalSet": {
                        "shopMoney": {"amount": amount, "currencyCode": "EUR"},
                    },
                }
            ]
        },
    }


def test_aggregate_line_items_groups_by_product_gid() -> None:
    today = date.today()
    created_at = datetime.combine(today, datetime.min.time()).isoformat() + "Z"
    orders = [
        _sample_order(
            order_id="order-1",
            created_at=created_at,
            product_gid="gid://shopify/Product/1",
            quantity=2,
            amount="50.00",
        ),
        _sample_order(
            order_id="order-2",
            created_at=created_at,
            product_gid="gid://shopify/Product/1",
            quantity=1,
            amount="25.00",
        ),
        _sample_order(
            order_id="order-3",
            created_at=created_at,
            product_gid="gid://shopify/Product/2",
            quantity=4,
            amount="80.00",
        ),
    ]

    aggregates, currency = _aggregate_line_items(orders)

    assert currency == "EUR"
    assert aggregates["gid://shopify/Product/1"]["quantitySold"] == 3
    assert aggregates["gid://shopify/Product/1"]["ordersCount"] == 2
    assert aggregates["gid://shopify/Product/1"]["sales"] == 75.0
    assert aggregates["gid://shopify/Product/2"]["quantitySold"] == 4


def test_fetch_orders_filters_cancelled_orders() -> None:
    async def run() -> None:
        from app.services.shopify.shopify_commerce_client import (
            fetch_shopify_orders_for_product_performance,
        )

        today = date.today()
        created_at = datetime.combine(today, datetime.min.time()).isoformat() + "Z"
        product_gid = "gid://shopify/Product/1"
        cancelled_order = _sample_order(
            order_id="order-cancelled",
            created_at=created_at,
            product_gid=product_gid,
            quantity=5,
            amount="100.00",
            cancelled=True,
        )

        with patch(
            "app.services.shopify.shopify_commerce_client._fetch_orders_page",
            new=AsyncMock(return_value=([cancelled_order], False, None)),
        ):
            result = await fetch_shopify_orders_for_product_performance(
                shop_domain="shop.myshopify.com",
                access_token="token",
                start_date=today - timedelta(days=29),
                end_date=today,
            )

        assert result["orders_count"] == 0
        assert result["aggregates_by_product_gid"] == {}

    asyncio.run(run())


def test_build_page_commerce_metadata_zeros_for_no_sales() -> None:
    metadata = _build_page_commerce_metadata(
        period_days=30,
        product_gid="gid://shopify/Product/99",
        aggregates={},
        snapshot={"stock": 12, "availableForSale": True, "status": "ACTIVE"},
        currency="EUR",
        synced_at="2026-06-13T10:00:00Z",
    )

    assert metadata["quantitySold"] == 0
    assert metadata["ordersCount"] == 0
    assert metadata["sales"] == 0
    assert metadata["stock"] == 12


def test_compute_run_commerce_summary_aggregates_totals() -> None:
    page = _build_product_page(project_id=uuid4(), run_id=uuid4())
    page.page_metadata = {
        "shopifyCommerce": {
            "sales": 120.5,
            "quantitySold": 8,
            "ordersCount": 5,
            "stock": 0,
            "availableForSale": False,
        }
    }
    page_no_sales = _build_product_page(
        project_id=page.project_id,
        run_id=page.run_id,
        page_id=uuid4(),
        product_gid="gid://shopify/Product/2",
    )
    page_no_sales.page_metadata = {
        "shopifyCommerce": {
            "sales": 0,
            "quantitySold": 0,
            "ordersCount": 0,
            "stock": 5,
            "availableForSale": True,
        }
    }

    summary = _compute_run_commerce_summary(
        [page, page_no_sales],
        period_days=30,
        synced_at="2026-06-13T10:00:00Z",
        currency="EUR",
    )

    assert summary["totalSales"] == 120.5
    assert summary["totalQuantitySold"] == 8
    assert summary["productsWithSales"] == 1
    assert summary["productsWithoutSales"] == 1
    assert summary["productsOutOfStock"] == 1


def test_build_shopify_commerce_findings_limited_to_ten() -> None:
    project_id = uuid4()
    run_id = uuid4()
    pages = [
        _build_product_page(
            project_id=project_id,
            run_id=run_id,
            page_id=uuid4(),
            product_gid=f"gid://shopify/Product/{index}",
        )
        for index in range(12)
    ]
    for page in pages:
        page.page_metadata = {
            "searchConsole": {"impressions": 500},
            "analytics": {"sessions": 80},
            "shopifyCommerce": {"sales": 0, "quantitySold": 0, "stock": 0, "availableForSale": False},
        }

    findings = _build_shopify_commerce_findings(pages, [])
    assert len(findings) <= 10


def test_analyze_shopify_commerce_requires_connected_store() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        audit_run = _build_run(project_id, run_id)
        session = AsyncMock()

        with (
            patch(
                "app.services.growth_audit.shopify_commerce_analysis.get_growth_audit_run",
                new=AsyncMock(return_value=audit_run),
            ),
            patch(
                "app.services.growth_audit.shopify_commerce_analysis.get_shopify_store_for_project",
                new=AsyncMock(return_value=None),
            ),
            pytest.raises(ShopifyIntegrationNotConnectedError, match="Collega Shopify"),
        ):
            await analyze_growth_audit_shopify_commerce(
                session,
                project_id=project_id,
                run_id=run_id,
            )

    asyncio.run(run())


def test_analyze_shopify_commerce_requires_commerce_scopes() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        audit_run = _build_run(project_id, run_id)
        store = MagicMock()
        store.connection_status = "connected"
        client = MagicMock()
        client.shop_domain = "shop.myshopify.com"
        client.access_token = "token"
        session = AsyncMock()

        with (
            patch(
                "app.services.growth_audit.shopify_commerce_analysis.get_growth_audit_run",
                new=AsyncMock(return_value=audit_run),
            ),
            patch(
                "app.services.growth_audit.shopify_commerce_analysis.get_shopify_store_for_project",
                new=AsyncMock(return_value=store),
            ),
            patch(
                "app.services.growth_audit.shopify_commerce_analysis.get_shopify_client_for_store",
                new=AsyncMock(return_value=client),
            ),
            patch(
                "app.services.growth_audit.shopify_commerce_analysis.assert_commerce_scopes_granted",
                new=AsyncMock(
                    side_effect=ShopifyIntegrationPermissionError(
                        "Permessi Shopify insufficienti per leggere vendite e revenue.",
                        missing_scopes=["read_orders"],
                    )
                ),
            ),
            pytest.raises(ShopifyIntegrationPermissionError),
        ):
            await analyze_growth_audit_shopify_commerce(
                session,
                project_id=project_id,
                run_id=run_id,
            )

    asyncio.run(run())


def test_analyze_shopify_commerce_requires_product_pages() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        audit_run = _build_run(project_id, run_id)
        store = MagicMock()
        store.connection_status = "connected"
        client = MagicMock()
        session = AsyncMock()

        with (
            patch(
                "app.services.growth_audit.shopify_commerce_analysis.get_growth_audit_run",
                new=AsyncMock(return_value=audit_run),
            ),
            patch(
                "app.services.growth_audit.shopify_commerce_analysis.get_shopify_store_for_project",
                new=AsyncMock(return_value=store),
            ),
            patch(
                "app.services.growth_audit.shopify_commerce_analysis.get_shopify_client_for_store",
                new=AsyncMock(return_value=client),
            ),
            patch(
                "app.services.growth_audit.shopify_commerce_analysis.assert_commerce_scopes_granted",
                new=AsyncMock(return_value=["read_orders", "read_products"]),
            ),
            patch(
                "app.services.growth_audit.shopify_commerce_analysis.list_growth_audit_pages",
                new=AsyncMock(return_value=[]),
            ),
            pytest.raises(GrowthAuditValidationError, match="Nessuna pagina prodotto"),
        ):
            await analyze_growth_audit_shopify_commerce(
                session,
                project_id=project_id,
                run_id=run_id,
            )

    asyncio.run(run())


def test_analyze_shopify_commerce_updates_page_metadata_and_summary() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        product_gid = "gid://shopify/Product/1"
        page = _build_product_page(project_id=project_id, run_id=run_id, product_gid=product_gid)
        audit_run = _build_run(project_id, run_id)
        store = MagicMock()
        store.connection_status = "connected"
        client = MagicMock()
        client.shop_domain = "shop.myshopify.com"
        client.access_token = "token"

        session = AsyncMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.flush = AsyncMock()
        findings_result = MagicMock()
        findings_result.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=findings_result)

        today = date.today()
        created_at = datetime.combine(today, datetime.min.time()).isoformat() + "Z"

        with (
            patch(
                "app.services.growth_audit.shopify_commerce_analysis.get_growth_audit_run",
                new=AsyncMock(return_value=audit_run),
            ),
            patch(
                "app.services.growth_audit.shopify_commerce_analysis.get_shopify_store_for_project",
                new=AsyncMock(return_value=store),
            ),
            patch(
                "app.services.growth_audit.shopify_commerce_analysis.get_shopify_client_for_store",
                new=AsyncMock(return_value=client),
            ),
            patch(
                "app.services.growth_audit.shopify_commerce_analysis.assert_commerce_scopes_granted",
                new=AsyncMock(return_value=["read_orders", "read_products"]),
            ),
            patch(
                "app.services.growth_audit.shopify_commerce_analysis.list_growth_audit_pages",
                new=AsyncMock(return_value=[page]),
            ),
            patch(
                "app.services.growth_audit.shopify_commerce_analysis.fetch_shopify_orders_for_product_performance",
                new=AsyncMock(
                    return_value={
                        "aggregates_by_product_gid": {
                            product_gid: {
                                "quantitySold": 3,
                                "ordersCount": 2,
                                "sales": 75.0,
                            }
                        },
                        "currency": "EUR",
                    }
                ),
            ),
            patch(
                "app.services.growth_audit.shopify_commerce_analysis.fetch_shopify_products_inventory_snapshot",
                new=AsyncMock(
                    return_value={
                        "products_by_gid": {
                            product_gid: {
                                "stock": 10,
                                "availableForSale": True,
                                "status": "ACTIVE",
                                "priceMin": 12.9,
                                "priceMax": 24.9,
                            }
                        }
                    }
                ),
            ),
            patch(
                "app.services.growth_audit.shopify_commerce_analysis.create_growth_audit_event",
                new=AsyncMock(),
            ),
        ):
            result = await analyze_growth_audit_shopify_commerce(
                session,
                project_id=project_id,
                run_id=run_id,
                days=30,
            )

        assert result["pages_updated"] == 1
        assert page.page_metadata["shopifyCommerce"]["sales"] == 75.0
        assert page.page_metadata["shopifyCommerce"]["quantitySold"] == 3
        assert page.page_metadata["shopifyCommerce"]["stock"] == 10
        assert audit_run.summary["shopifyCommerce"]["totalSales"] == 75.0
        assert audit_run.summary["shopifyCommerce"]["productsWithSales"] == 1
        session.commit.assert_awaited_once()

    asyncio.run(run())


def test_fetch_orders_pagination_mock() -> None:
    async def run() -> None:
        from app.services.shopify.shopify_commerce_client import (
            fetch_shopify_orders_for_product_performance,
        )

        today = date.today()
        recent = datetime.combine(today, datetime.min.time()).isoformat() + "Z"
        older = datetime.combine(today - timedelta(days=60), datetime.min.time()).isoformat() + "Z"
        product_gid = "gid://shopify/Product/1"

        page_one = [
            _sample_order(
                order_id="order-1",
                created_at=recent,
                product_gid=product_gid,
                quantity=2,
                amount="40.00",
            )
        ]
        page_two = [
            _sample_order(
                order_id="order-old",
                created_at=older,
                product_gid=product_gid,
                quantity=99,
                amount="999.00",
            )
        ]

        with patch(
            "app.services.shopify.shopify_commerce_client._fetch_orders_page",
            new=AsyncMock(
                side_effect=[
                    (page_one, True, "cursor-1"),
                    (page_two, False, None),
                ]
            ),
        ):
            result = await fetch_shopify_orders_for_product_performance(
                shop_domain="shop.myshopify.com",
                access_token="token",
                start_date=today - timedelta(days=29),
                end_date=today,
            )

        assert result["orders_count"] == 1
        assert result["aggregates_by_product_gid"][product_gid]["quantitySold"] == 2
        assert result["aggregates_by_product_gid"][product_gid]["sales"] == 40.0

    asyncio.run(run())


def test_shopify_commerce_route_returns_503_when_not_connected() -> None:
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
                "app.api.routes.growth_audit.analyze_growth_audit_shopify_commerce",
                new=AsyncMock(
                    side_effect=ShopifyIntegrationNotConnectedError(
                        "Collega Shopify per importare vendite e revenue prodotto."
                    )
                ),
            ),
            pytest.raises(HTTPException) as exc,
        ):
            await analyze_growth_audit_shopify_commerce_endpoint(
                project_id,
                run_id,
                GrowthAuditShopifyCommerceAnalysisRequest(days=30),
                session,
            )

        assert exc.value.status_code == 503

    asyncio.run(run())


def test_shopify_commerce_route_returns_403_when_scopes_missing() -> None:
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
                "app.api.routes.growth_audit.analyze_growth_audit_shopify_commerce",
                new=AsyncMock(
                    side_effect=ShopifyIntegrationPermissionError(
                        "Permessi Shopify insufficienti per leggere vendite e revenue.",
                        missing_scopes=["read_orders"],
                    )
                ),
            ),
            pytest.raises(HTTPException) as exc,
        ):
            await analyze_growth_audit_shopify_commerce_endpoint(
                project_id,
                run_id,
                GrowthAuditShopifyCommerceAnalysisRequest(days=30),
                session,
            )

        assert exc.value.status_code == 403

    asyncio.run(run())


def test_shopify_commerce_route_returns_200_with_mock() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        audit_run = _build_run(project_id, run_id)
        session = AsyncMock()

        with (
            patch(
                "app.api.routes.growth_audit.get_project_in_default_workspace",
                new=AsyncMock(),
            ),
            patch(
                "app.api.routes.growth_audit.analyze_growth_audit_shopify_commerce",
                new=AsyncMock(
                    return_value={
                        "run": audit_run,
                        "summary": {
                            "totalSales": 250.0,
                            "totalQuantitySold": 12,
                            "productsWithSales": 2,
                        },
                        "pages_updated": 2,
                        "findings_created": 1,
                        "message": "Dati ecommerce Shopify aggiornati",
                    }
                ),
            ),
        ):
            response = await analyze_growth_audit_shopify_commerce_endpoint(
                project_id,
                run_id,
                GrowthAuditShopifyCommerceAnalysisRequest(),
                session,
            )

        assert response.summary["totalSales"] == 250.0
        assert "aggiornati" in response.message.lower()

    asyncio.run(run())
