"""Tests for Growth Audit Merchant Center analysis."""

from __future__ import annotations

import asyncio
import os
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

from app.models.growth_audit import GrowthAuditPage, GrowthAuditRun
from app.models.project import Project
from app.services.growth_audit.exceptions import GrowthAuditValidationError
from app.services.growth_audit.merchant_center_analysis import (
    _build_merchant_center_findings,
    _compute_run_merchant_center_summary,
)
from app.services.growth_audit.merchant_product_matching import match_merchant_products_to_pages


def _build_product_page(
    *,
    project_id,
    run_id,
    page_id=None,
    url: str = "https://example.com/products/miele",
    handle: str = "miele",
    product_gid: str = "gid://shopify/Product/42",
) -> GrowthAuditPage:
    page_id = page_id or uuid4()
    now = datetime.now(UTC)
    return GrowthAuditPage(
        id=page_id,
        run_id=run_id,
        project_id=project_id,
        url=url,
        normalized_url=url,
        path="/products/miele",
        page_type="product",
        source="shopify_product",
        status="analyzed",
        priority="normal",
        title="Miele",
        score=82,
        http_status=200,
        source_entity_type="shopify_product",
        source_entity_gid=product_gid,
        source_entity_handle=handle,
        page_metadata={},
        created_at=now,
        updated_at=now,
    )


def test_match_merchant_products_by_link() -> None:
    page = _build_product_page(project_id=uuid4(), run_id=uuid4())
    products = [
        {
            "offerId": "sku-1",
            "link": "https://example.com/products/miele",
            "title": "Miele",
            "status": "approved",
            "issues": [],
        }
    ]
    matches, unmatched = match_merchant_products_to_pages([page], products)
    assert len(matches) == 1
    first = next(iter(matches.values()))
    assert first.matched_by == "link"
    assert len(unmatched) == 0


def test_match_merchant_products_by_handle() -> None:
    page = _build_product_page(
        project_id=uuid4(),
        run_id=uuid4(),
        url="https://example.com/products/miele",
        handle="miele",
    )
    page.normalized_url = "https://example.com/products/other"
    page.url = "https://example.com/products/other"
    products = [
        {
            "offerId": "sku-2",
            "link": "https://example.com/products/miele?variant=1",
            "title": "Miele",
            "status": "approved",
            "issues": [],
        }
    ]
    matches, unmatched = match_merchant_products_to_pages([page], products)
    assert len(matches) == 1
    first = next(iter(matches.values()))
    assert first.matched_by == "handle"


def test_match_merchant_products_skips_ambiguous_gtin() -> None:
    page_a = _build_product_page(project_id=uuid4(), run_id=uuid4(), handle="a")
    page_b = _build_product_page(project_id=uuid4(), run_id=uuid4(), handle="b")
    page_a.page_metadata = {
        "ga4Ecommerce": {
            "variantBreakdown": [{"sku": "SKU-1", "variantLegacyId": "1"}],
        }
    }
    page_b.page_metadata = {
        "ga4Ecommerce": {
            "variantBreakdown": [{"sku": "SKU-1", "variantLegacyId": "2"}],
        }
    }
    products = [
        {
            "offerId": "x",
            "link": "https://other.com/products/x",
            "gtin": "SKU-1",
            "status": "approved",
            "issues": [],
        }
    ]
    matches, unmatched = match_merchant_products_to_pages([page_a, page_b], products)
    assert len(matches) == 0
    assert len(unmatched) == 1


def test_compute_run_merchant_center_summary_counts_statuses() -> None:
    page = _build_product_page(project_id=uuid4(), run_id=uuid4())
    page.page_metadata = {
        "merchantCenter": {
            "matchedBy": "link",
            "status": "disapproved",
            "issues": [{"code": "price", "severity": "ERROR"}],
            "issuesCount": 1,
            "criticalIssuesCount": 1,
        }
    }
    summary = _compute_run_merchant_center_summary([page], products_unmatched=2, synced_at="2026-01-01T00:00:00Z")
    assert summary["productsMatched"] == 1
    assert summary["productsUnmatched"] == 2
    assert summary["disapprovedProducts"] == 1
    assert summary["productsWithIssues"] == 1
    assert summary["criticalIssues"] == 1


def test_build_merchant_center_findings_prioritizes_disapproved_with_demand() -> None:
    page = _build_product_page(project_id=uuid4(), run_id=uuid4())
    page.page_metadata = {
        "merchantCenter": {
            "matchedBy": "link",
            "status": "disapproved",
            "issues": [],
            "issuesCount": 0,
            "criticalIssuesCount": 0,
        },
        "shopifyCommerce": {"sales": 120, "syncedAt": "2026-01-01T00:00:00Z"},
    }
    findings = _build_merchant_center_findings([page])
    assert len(findings) == 1
    assert findings[0]["severity"] == "high"
    assert "disapprovato" in findings[0]["title"].lower()


def test_analyze_merchant_center_requires_account() -> None:
    async def run() -> None:
        from app.services.growth_audit.merchant_center_analysis import analyze_growth_audit_merchant_center

        project_id = uuid4()
        run_id = uuid4()
        session = AsyncMock()
        run = GrowthAuditRun(
            id=run_id,
            project_id=project_id,
            root_url="https://example.com",
            normalized_domain="example.com",
            status="completed",
            phase="completed",
            audit_mode="full_site_mvp",
            provider="openai",
            progress_percent=100,
            pages_discovered=0,
            pages_classified=0,
            pages_analyzed=0,
            pages_failed=0,
            site_score=70,
            summary={},
            config={},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        project = Project(
            id=project_id,
            workspace_id=uuid4(),
            name="Example",
            slug="example",
            status="active",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            google_merchant_account_id=None,
        )
        project_result = MagicMock()
        project_result.scalar_one_or_none.return_value = project
        session.execute = AsyncMock(return_value=project_result)

        with patch(
            "app.services.growth_audit.merchant_center_analysis.get_growth_audit_run",
            new_callable=AsyncMock,
            return_value=run,
        ):
            with pytest.raises(GrowthAuditValidationError) as exc:
                await analyze_growth_audit_merchant_center(
                    session,
                    project_id=project_id,
                    run_id=run_id,
                )

        assert "Merchant Center" in str(exc.value)

    asyncio.run(run())
