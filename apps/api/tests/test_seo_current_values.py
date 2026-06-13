"""Tests for SEO current values normalization."""

import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

from app.services.content.seo_current_values import (
    collection_api_current_values,
    normalize_proposal_values,
    product_api_current_values,
)


class _FakeProduct:
    title = "Miele Acacia"
    handle = "miele-acacia"
    seo_title = "Miele Acacia 500g | Brand"
    seo_description = "Miele biologico di acacia"
    description_html = "<p>Descrizione</p>"
    description_text = "Descrizione"
    tags = ["miele", "bio"]
    product_type = "Miele"
    vendor = "Apicoltura Test"
    media_images = [{"url": "https://x/img.jpg", "altText": "Barattolo"}]
    featured_image_url = None
    raw_payload = {}


class _FakeProductRawDescription:
    title = "Miele"
    handle = "miele"
    seo_title = None
    seo_description = None
    description_html = None
    description_text = None
    tags = []
    product_type = None
    vendor = None
    media_images = []
    featured_image_url = None
    raw_payload = {"descriptionHtml": "<p>Da raw payload</p>"}


class _FakeCollection:
    title = "Mieli"
    handle = "mieli"
    seo_title = "Mieli artigianali"
    seo_description = "Tutti i mieli"
    description_html = "<p>Collezione</p>"
    description_text = "Collezione"
    image_alt = "Mieli vari"


def test_product_api_current_values_camel_case() -> None:
    data = product_api_current_values(_FakeProduct())
    assert data["title"] == "Miele Acacia"
    assert data["seoTitle"] == "Miele Acacia 500g | Brand"
    assert data["metaDescription"] == "Miele biologico di acacia"
    assert data["productType"] == "Miele"
    assert data["vendor"] == "Apicoltura Test"
    assert len(data["images"]) == 1


def test_product_description_fallback_from_raw_payload() -> None:
    data = product_api_current_values(_FakeProductRawDescription())
    assert data["descriptionHtml"] == "<p>Da raw payload</p>"
    assert data["descriptionText"] == "Da raw payload"


def test_collection_api_current_values_camel_case() -> None:
    data = collection_api_current_values(_FakeCollection())
    assert data["title"] == "Mieli"
    assert data["seoTitle"] == "Mieli artigianali"
    assert data["imageAlt"] == "Mieli vari"


def test_normalize_proposal_values_from_camel() -> None:
    result = normalize_proposal_values(
        "product",
        {
            "title": "New Title",
            "seoTitle": "SEO",
            "metaDescription": "Meta",
            "tags": ["a"],
        },
    )
    assert result["product_title"] == "New Title"
    assert result["seo_title"] == "SEO"
    assert result["meta_description"] == "Meta"
