"""Tests for product SEO scoring without tags component."""

import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

from app.services.content.seo_scoring_constants import PRODUCT_WEIGHTS
from app.services.content.seo_scoring_engine import score_product


def test_product_score_breakdown_excludes_tags() -> None:
    result = score_product(
        title="Miele Acacia 500g",
        seo_title="Miele Acacia | Apicoltura",
        seo_description="Miele biologico di acacia coltivato in Italia con metodi sostenibili.",
        description_text="Descrizione lunga " * 20,
        handle="miele-acacia",
        media_images=[{"id": "1", "altText": "Barattolo di miele"}],
        featured_image_url=None,
        product_type="Miele",
        is_best_seller=False,
    )
    breakdown = result["score_breakdown"]
    assert "tags" not in breakdown
    assert "imageAlt" in breakdown
    assert sum(item["max"] for item in breakdown.values()) == sum(PRODUCT_WEIGHTS.values())


def test_product_score_total_max_is_100_weights() -> None:
    assert sum(PRODUCT_WEIGHTS.values()) == 100
