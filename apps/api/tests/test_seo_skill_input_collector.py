"""Tests for SEO Skill input collector."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import httpx
import pytest

from app.services.seo_skills.exceptions import (
    SkillInputCollectionError,
    UnsupportedSkillTargetError,
)
from app.services.seo_skills.input_collector import (
    MAX_TEXT_CHARS,
    collect_skill_input,
    extract_page_metadata,
    extract_text_from_html,
    is_private_or_blocked_host,
    truncate_value,
    validate_public_http_url,
)


# --- SSRF validation ---


def test_validate_public_http_url_rejects_file_scheme() -> None:
    with pytest.raises(SkillInputCollectionError, match="URL host is not allowed"):
        validate_public_http_url("file:///etc/passwd")


def test_validate_public_http_url_rejects_localhost() -> None:
    with pytest.raises(SkillInputCollectionError, match="URL host is not allowed"):
        validate_public_http_url("http://localhost/page")


def test_validate_public_http_url_rejects_127_0_0_1() -> None:
    with pytest.raises(SkillInputCollectionError, match="URL host is not allowed"):
        validate_public_http_url("http://127.0.0.1/page")


def test_validate_public_http_url_rejects_private_ip() -> None:
    assert is_private_or_blocked_host("10.0.0.1") is True
    with pytest.raises(SkillInputCollectionError, match="URL host is not allowed"):
        validate_public_http_url("http://10.0.0.1/page")


def test_validate_public_http_url_accepts_https_example_com() -> None:
    assert validate_public_http_url("https://example.com") == "https://example.com"


# --- HTML extraction ---


def test_extract_text_from_html_removes_script_and_style() -> None:
    html = """
    <html>
      <head><style>body { color: red; }</style></head>
      <body>
        <script>alert('x')</script>
        <p>Hello   world</p>
      </body>
    </html>
    """
    text = extract_text_from_html(html)
    assert "alert" not in text
    assert "color: red" not in text
    assert "Hello world" in text


def test_extract_page_metadata_extracts_title_meta_h1_canonical() -> None:
    html = """
    <html>
      <head>
        <title>Page Title</title>
        <meta name="description" content="Meta desc here" />
        <link rel="canonical" href="https://example.com/canonical" />
      </head>
      <body>
        <h1>Main Heading</h1>
        <h1>Second H1</h1>
      </body>
    </html>
    """
    meta = extract_page_metadata(html)
    assert meta["title"] == "Page Title"
    assert meta["metaDescription"] == "Meta desc here"
    assert meta["canonical"] == "https://example.com/canonical"
    assert meta["h1"] == ["Main Heading", "Second H1"]


def test_truncate_value_truncates_long_text() -> None:
    long_text = "a" * (MAX_TEXT_CHARS + 10)
    truncated = truncate_value(long_text, MAX_TEXT_CHARS)
    assert len(truncated) == MAX_TEXT_CHARS
    assert truncated.endswith("...")


# --- domain target ---


def test_collect_domain_returns_full_crawl_warning() -> None:
    async def run() -> None:
        session = AsyncMock()
        project_id = uuid4()

        with patch(
            "app.services.seo_skills.input_collector.BrandIntelligenceContextBuilder.get_prompt_context",
            new=AsyncMock(return_value=None),
        ):
            result = await collect_skill_input(
                session,
                project_id,
                "domain",
                url="example.com",
            )

        assert result["targetType"] == "domain"
        assert result["url"] == "https://example.com"
        assert result["metadata"]["domain"] == "example.com"
        assert any(
            "Full domain crawl is not implemented yet" in warning
            for warning in result["warnings"]
        )

    asyncio.run(run())


# --- shopify_product ---


def test_collect_shopify_product_requires_target_id() -> None:
    async def run() -> None:
        session = AsyncMock()
        with pytest.raises(
            SkillInputCollectionError,
            match="target_id is required for shopify_product",
        ):
            await collect_skill_input(session, uuid4(), "shopify_product")

    asyncio.run(run())


def test_collect_shopify_product_collects_product_data() -> None:
    async def run() -> None:
        session = AsyncMock()
        project_id = uuid4()
        product_id = uuid4()
        store_id = uuid4()

        store = MagicMock()
        store.id = store_id
        store.shop_domain = "demo.myshopify.com"

        product = MagicMock()
        product.id = product_id
        product.shopify_gid = "gid://shopify/Product/1"
        product.title = "Test Product"
        product.handle = "test-product"
        product.vendor = "Acme"
        product.product_type = "Shoes"
        product.tags = ["sale"]
        product.status = "ACTIVE"
        product.seo_title = "SEO Title"
        product.seo_description = "SEO Description"
        product.description_html = "<p>Product <strong>description</strong></p>"
        product.description_text = "Product description"
        product.media_images = [{"url": "https://cdn.example.com/img.jpg"}]
        product.min_price = Decimal("19.99")
        product.max_price = Decimal("29.99")
        product.created_at_shopify = datetime(2024, 1, 1, tzinfo=UTC)
        product.updated_at_shopify = datetime(2024, 6, 1, tzinfo=UTC)

        product_result = MagicMock()
        product_result.scalar_one_or_none.return_value = product

        analysis_result = MagicMock()
        analysis_result.scalar_one_or_none.return_value = None

        proposal_result = MagicMock()
        proposal_result.scalar_one_or_none.return_value = None

        session.execute = AsyncMock(
            side_effect=[product_result, analysis_result, proposal_result]
        )

        with (
            patch(
                "app.services.seo_skills.input_collector.get_shopify_store_for_project",
                new=AsyncMock(return_value=store),
            ),
            patch(
                "app.services.seo_skills.input_collector.BrandIntelligenceContextBuilder.get_prompt_context",
                new=AsyncMock(return_value="Brand voice: friendly"),
            ),
        ):
            result = await collect_skill_input(
                session,
                project_id,
                "shopify_product",
                target_id=product_id,
            )

        assert result["targetType"] == "shopify_product"
        assert result["targetId"] == str(product_id)
        assert result["title"] == "Test Product"
        assert result["url"] == "https://demo.myshopify.com/products/test-product"
        assert result["shopify"]["product"]["handle"] == "test-product"
        assert result["shopify"]["product"]["priceRange"]["minPrice"] == 19.99
        assert result["brandContext"] == "Brand voice: friendly"

    asyncio.run(run())


# --- shopify_collection ---


def test_collect_shopify_collection_requires_target_id() -> None:
    async def run() -> None:
        session = AsyncMock()
        with pytest.raises(
            SkillInputCollectionError,
            match="target_id is required for shopify_collection",
        ):
            await collect_skill_input(session, uuid4(), "shopify_collection")

    asyncio.run(run())


def test_collect_shopify_collection_collects_collection_data() -> None:
    async def run() -> None:
        session = AsyncMock()
        project_id = uuid4()
        collection_id = uuid4()
        store_id = uuid4()

        store = MagicMock()
        store.id = store_id
        store.shop_domain = "demo.myshopify.com"

        collection = MagicMock()
        collection.id = collection_id
        collection.shopify_gid = "gid://shopify/Collection/1"
        collection.title = "Summer"
        collection.handle = "summer"
        collection.seo_title = "Summer SEO"
        collection.seo_description = "Summer collection"
        collection.description_html = "<p>Summer picks</p>"
        collection.description_text = "Summer picks"
        collection.image_url = "https://cdn.example.com/summer.jpg"
        collection.image_alt = "Summer banner"
        collection.products_count = 12
        collection.created_at = datetime(2024, 1, 1, tzinfo=UTC)
        collection.updated_at = datetime(2024, 6, 1, tzinfo=UTC)

        collection_result = MagicMock()
        collection_result.scalar_one_or_none.return_value = collection

        analysis_result = MagicMock()
        analysis_result.scalar_one_or_none.return_value = None

        proposal_result = MagicMock()
        proposal_result.scalar_one_or_none.return_value = None

        session.execute = AsyncMock(
            side_effect=[collection_result, analysis_result, proposal_result]
        )

        with (
            patch(
                "app.services.seo_skills.input_collector.get_shopify_store_for_project",
                new=AsyncMock(return_value=store),
            ),
            patch(
                "app.services.seo_skills.input_collector.BrandIntelligenceContextBuilder.get_prompt_context",
                new=AsyncMock(return_value=None),
            ),
        ):
            result = await collect_skill_input(
                session,
                project_id,
                "shopify_collection",
                target_id=collection_id,
            )

        assert result["targetType"] == "shopify_collection"
        assert result["url"] == "https://demo.myshopify.com/collections/summer"
        assert result["shopify"]["collection"]["productsCount"] == 12
        assert "Brand context not available for this project." in result["warnings"]

    asyncio.run(run())


# --- brand context ---


def test_collect_skill_input_brand_context_unavailable_adds_warning() -> None:
    async def run() -> None:
        session = AsyncMock()
        project_id = uuid4()

        with patch(
            "app.services.seo_skills.input_collector.BrandIntelligenceContextBuilder.get_prompt_context",
            new=AsyncMock(return_value=None),
        ):
            result = await collect_skill_input(
                session,
                project_id,
                "domain",
                url="example.org",
            )

        assert result["brandContext"] == ""
        assert "Brand context not available for this project." in result["warnings"]

    asyncio.run(run())


# --- unsupported target ---


def test_collect_skill_input_unsupported_target_type() -> None:
    async def run() -> None:
        session = AsyncMock()
        with pytest.raises(
            UnsupportedSkillTargetError,
            match="Unsupported target_type: unknown",
        ):
            await collect_skill_input(session, uuid4(), "unknown")

    asyncio.run(run())


# --- url target fetch ---


def test_collect_url_fetches_and_populates_metadata() -> None:
    async def run() -> None:
        session = AsyncMock()
        project_id = uuid4()
        html = """
        <html>
          <head>
            <title>Fetched</title>
            <meta name="description" content="Fetched desc" />
          </head>
          <body><h1>Heading</h1><p>Body text</p></body>
        </html>
        """

        mock_response = MagicMock()
        mock_response.text = html
        mock_response.status_code = 200
        mock_response.url = "https://example.com/final"

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with (
            patch(
                "app.services.seo_skills.input_collector.httpx.AsyncClient",
                return_value=mock_client,
            ),
            patch(
                "app.services.seo_skills.input_collector.BrandIntelligenceContextBuilder.get_prompt_context",
                new=AsyncMock(return_value=None),
            ),
        ):
            result = await collect_skill_input(
                session,
                project_id,
                "url",
                url="https://example.com",
            )

        assert result["targetType"] == "url"
        assert result["title"] == "Fetched"
        assert result["metadata"]["httpStatus"] == 200
        assert result["metadata"]["finalUrl"] == "https://example.com/final"
        assert result["metadata"]["metaDescription"] == "Fetched desc"
        assert result["metadata"]["h1"] == ["Heading"]
        mock_client.get.assert_awaited_once()

    asyncio.run(run())


def test_collect_url_requires_url() -> None:
    async def run() -> None:
        session = AsyncMock()
        with pytest.raises(
            SkillInputCollectionError,
            match="url is required for target_type=url",
        ):
            await collect_skill_input(session, uuid4(), "url")

    asyncio.run(run())


def test_collect_url_fetch_failure_raises_readable_error() -> None:
    async def run() -> None:
        session = AsyncMock()
        mock_client = MagicMock()
        mock_client.get = AsyncMock(side_effect=httpx.ConnectError("connection refused"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "app.services.seo_skills.input_collector.httpx.AsyncClient",
            return_value=mock_client,
        ):
            with pytest.raises(SkillInputCollectionError, match="Failed to fetch URL"):
                await collect_skill_input(
                    session,
                    uuid4(),
                    "url",
                    url="https://example.com",
                )

    asyncio.run(run())
