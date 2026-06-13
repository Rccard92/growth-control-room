"""Regression tests for SEO product/collection detail responses."""

import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

from app.schemas.seo_optimizer import (
    SeoCollectionDetailResponse,
    SeoProductDetailResponse,
)
from app.services.content.seo_skill_loader import skill_meta_for_detail_response


def test_skill_meta_for_detail_response_product() -> None:
    meta = skill_meta_for_detail_response("product")
    assert meta.score_rule_categories
    assert "title" in meta.score_rule_categories
    assert "image_alt" in meta.score_rule_categories
    assert len(meta.external_skills) >= 1


def test_skill_meta_for_detail_response_collection() -> None:
    meta = skill_meta_for_detail_response("collection")
    assert meta.score_rule_categories
    assert "tags" not in meta.score_rule_categories
    assert "image_alt" in meta.score_rule_categories


def test_build_product_detail_no_validation_error() -> None:
    response = SeoProductDetailResponse(
        product={
            "id": "00000000-0000-0000-0000-000000000001",
            "title": "Test Product",
            "handle": "test-product",
        },
        analysis=None,
        score_breakdown=None,
        skill_meta=skill_meta_for_detail_response("product"),
        current_values={
            "title": "Test Product",
            "handle": "test-product",
            "seoTitle": None,
            "metaDescription": None,
            "descriptionHtml": "<p>Test</p>",
            "descriptionText": "Test",
            "tags": [],
            "productType": None,
            "vendor": None,
            "images": [],
        },
        images=[],
        quantity_sold=0,
        revenue=0.0,
        stock=10,
        latest_proposal=None,
        proposal_history=[],
        change_logs=[],
    )
    assert response.skill_meta is not None
    assert response.skill_meta.score_rule_categories
    dumped = response.model_dump(by_alias=True)
    assert dumped["skillMeta"]["scoreRuleCategories"]
    assert dumped["currentValues"]["title"] == "Test Product"


def test_build_collection_detail_no_validation_error() -> None:
    response = SeoCollectionDetailResponse(
        collection={
            "id": "00000000-0000-0000-0000-000000000002",
            "title": "Test Collection",
            "handle": "test-collection",
        },
        analysis=None,
        score_breakdown=None,
        skill_meta=skill_meta_for_detail_response("collection"),
        current_values={
            "title": "Test Collection",
            "handle": "test-collection",
            "seoTitle": None,
            "metaDescription": None,
            "descriptionHtml": None,
            "descriptionText": None,
            "imageAlt": None,
        },
        image=None,
        latest_proposal=None,
        proposal_history=[],
        change_logs=[],
    )
    assert response.skill_meta is not None
    assert response.skill_meta.score_rule_categories
    dumped = response.model_dump(by_alias=True)
    assert dumped["skillMeta"]["scoreRuleCategories"]
