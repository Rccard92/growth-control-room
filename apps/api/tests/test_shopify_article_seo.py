"""Tests for Shopify article SEO metafield helpers."""

import inspect

from app.services.shopify.client import (
    ARTICLE_FIELDS,
    ShopifyGraphQLClient,
    article_seo_metafields_match,
    parse_article_global_seo_metafields,
)


def test_parse_article_global_seo_metafields() -> None:
    node = {
        "metafields": {
            "edges": [
                {
                    "node": {
                        "namespace": "global",
                        "key": "title_tag",
                        "value": "SEO title",
                        "type": "single_line_text_field",
                    }
                },
                {
                    "node": {
                        "namespace": "global",
                        "key": "description_tag",
                        "value": "Meta desc",
                        "type": "multi_line_text_field",
                    }
                },
            ]
        }
    }
    parsed = parse_article_global_seo_metafields(node)
    assert parsed["title_tag"] == "SEO title"
    assert parsed["description_tag"] == "Meta desc"


def test_article_seo_metafields_match() -> None:
    parsed = {"title_tag": "SEO title", "description_tag": "Meta desc"}
    assert article_seo_metafields_match(
        parsed,
        expected_title="SEO title",
        expected_description="Meta desc",
    )


def test_article_fields_has_no_seo_selection() -> None:
    assert "seo {" not in ARTICLE_FIELDS
    assert "title_tag" in ARTICLE_FIELDS or "metafields" in ARTICLE_FIELDS


def test_paginate_blog_articles_query_has_no_article_seo() -> None:
    source = inspect.getsource(ShopifyGraphQLClient._paginate_blog_articles)
    assert "seo {" not in source
    assert "ARTICLE_FIELDS" in source
    assert "seo {" not in ARTICLE_FIELDS
    assert "metafields" in ARTICLE_FIELDS
