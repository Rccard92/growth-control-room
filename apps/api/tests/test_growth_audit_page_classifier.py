"""Tests for Growth Audit page classifier."""

from __future__ import annotations

from app.services.growth_audit.page_classifier import (
    classify_page_type,
    get_default_skill_bundle_for_page_type,
)


def test_classify_homepage() -> None:
    assert classify_page_type("https://example.com/") == "homepage"


def test_classify_product() -> None:
    assert classify_page_type("https://example.com/products/foo-bar") == "product"


def test_classify_collection() -> None:
    assert classify_page_type("https://example.com/collections/summer") == "collection"


def test_classify_blog() -> None:
    assert classify_page_type("https://example.com/blogs/news") == "blog"


def test_classify_blog_article() -> None:
    assert classify_page_type("https://example.com/blogs/news/my-post") == "blog_article"


def test_classify_static_page() -> None:
    assert classify_page_type("https://example.com/pages/about") == "static_page"


def test_classify_policy() -> None:
    assert classify_page_type("https://example.com/privacy-policy") == "policy"


def test_classify_cart() -> None:
    assert classify_page_type("https://example.com/cart") == "cart"


def test_skill_bundle_homepage() -> None:
    bundle = get_default_skill_bundle_for_page_type("homepage")
    assert "seo-audit" in bundle
