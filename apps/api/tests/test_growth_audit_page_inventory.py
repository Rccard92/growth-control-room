"""Tests for Growth Audit page inventory merge."""

from __future__ import annotations

from app.services.growth_audit.page_inventory import merge_discovered_urls


def test_merge_discovered_urls_seed_first() -> None:
    items = merge_discovered_urls(
        seed_url="https://example.com",
        sitemap_urls=["https://example.com/products/a"],
        shopify_items=[],
        max_pages=10,
        root_domain="example.com",
    )
    assert items[0]["source"] == "seed"
    assert items[0]["pageType"] == "homepage"


def test_merge_deduplicates_normalized_url() -> None:
    items = merge_discovered_urls(
        seed_url="https://example.com",
        sitemap_urls=["https://example.com/products/shared"],
        shopify_items=[
            {
                "url": "https://example.com/products/shared",
                "source": "shopify_product",
                "pageType": "product",
                "title": "Shared Product",
                "metadata": {"handle": "shared"},
            }
        ],
        max_pages=10,
        root_domain="example.com",
    )
    product_items = [item for item in items if item["pageType"] == "product"]
    assert len(product_items) == 1
    assert product_items[0]["source"] == "shopify_product"
    assert product_items[0]["title"] == "Shared Product"


def test_merge_excludes_cart_and_static_assets() -> None:
    items = merge_discovered_urls(
        seed_url="https://example.com",
        sitemap_urls=[
            "https://example.com/cart",
            "https://example.com/assets/app.js",
            "https://example.com/products/ok",
        ],
        shopify_items=[],
        max_pages=10,
        root_domain="example.com",
    )
    urls = [item["normalizedUrl"] for item in items]
    assert all("/cart" not in url for url in urls)
    assert all(".js" not in url for url in urls)
    assert "https://example.com/products/ok" in urls


def test_merge_limits_max_pages() -> None:
    sitemap_urls = [f"https://example.com/pages/page-{index}" for index in range(20)]
    items = merge_discovered_urls(
        seed_url="https://example.com",
        sitemap_urls=sitemap_urls,
        shopify_items=[],
        max_pages=5,
        root_domain="example.com",
    )
    assert len(items) == 5


def test_merge_classifies_static_page_and_blog_article() -> None:
    items = merge_discovered_urls(
        seed_url="https://example.com",
        sitemap_urls=[
            "https://example.com/pages/about",
            "https://example.com/blogs/news/post-one",
        ],
        shopify_items=[],
        max_pages=10,
        root_domain="example.com",
    )
    page_types = {item["pageType"] for item in items}
    assert "static_page" in page_types
    assert "blog_article" in page_types
