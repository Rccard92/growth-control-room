"""Tests for Shopify article SEO metafield helpers."""

from app.services.shopify.client import (
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
