"""Tests for local SEO update after Shopify apply."""

import asyncio
import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

from app.schemas.seo_optimizer import SeoApplyResponse
from app.services.content.seo_apply_local_update import apply_proposed_values_to_product
from app.services.content.seo_scoring_engine import score_product


class _FakeResult:
    def __init__(self, entity):
        self._entity = entity

    def scalar_one_or_none(self):
        return self._entity


class _FakeSession:
    def __init__(self, entity):
        self.entity = entity
        self.flushed = False

    async def execute(self, _stmt):
        return _FakeResult(self.entity)

    async def flush(self):
        self.flushed = True


class _FakeProduct:
    title = "Miele"
    handle = "miele"
    seo_title = None
    seo_description = None
    description_html = None
    description_text = None
    tags = []
    media_images = []
    raw_payload = {}


def test_apply_proposed_meta_description_maps_to_seo_description() -> None:
    product = _FakeProduct()
    session = _FakeSession(product)

    asyncio.run(
        apply_proposed_values_to_product(
            session,
            product_id="00000000-0000-0000-0000-000000000001",  # type: ignore[arg-type]
            proposed={"meta_description": "Miele biologico di acacia"},
        )
    )

    assert product.seo_description == "Miele biologico di acacia"
    assert session.flushed is True


def test_score_improves_after_meta_description_update() -> None:
    before = score_product(
        title="Miele",
        seo_title=None,
        seo_description=None,
        description_text="Descrizione",
        handle="miele",
        media_images=[],
        featured_image_url=None,
        product_type=None,
        is_best_seller=False,
    )
    after = score_product(
        title="Miele",
        seo_title=None,
        seo_description="Miele biologico di acacia",
        description_text="Descrizione",
        handle="miele",
        media_images=[],
        featured_image_url=None,
        product_type=None,
        is_best_seller=False,
    )

    assert after["score_total"] >= before["score_total"]
    assert after["score_meta_description"] > before["score_meta_description"]


def test_seo_apply_response_serializes_updated_analysis() -> None:
    response = SeoApplyResponse.model_validate(
        {
            "applied": True,
            "local_update_failed": False,
            "entity_type": "product",
            "entity_id": "00000000-0000-0000-0000-000000000001",
            "updated_analysis": {
                "scoreTotal": 82,
                "severity": "good",
                "issues": [],
            },
            "message": "Modifiche applicate su Shopify e dati locali aggiornati.",
        }
    )
    dumped = response.model_dump(by_alias=True)
    assert dumped["applied"] is True
    assert dumped["localUpdateFailed"] is False
    assert dumped["updatedAnalysis"]["scoreTotal"] == 82
