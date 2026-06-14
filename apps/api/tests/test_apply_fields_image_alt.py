"""Tests for apply-fields local persistence of image ALT."""

import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

from app.services.content.seo_apply_local_update import apply_proposed_values_to_product
from app.services.content.seo_image_utils import merge_media_image_alts
from app.services.content.seo_proposal_diff import compute_changed_proposed


def test_diff_media_images_returns_full_array() -> None:
    current = {
        "media_images": [
            {"id": "gid://shopify/MediaImage/1", "altText": "", "url": "u1"},
            {"id": "gid://shopify/MediaImage/2", "altText": "keep", "url": "u2"},
        ],
    }
    proposed = {
        "image_alts": [
            {
                "image_id": "gid://shopify/MediaImage/1",
                "proposed_alt": "new alt one",
            }
        ],
        "media_images": [
            {"id": "gid://shopify/MediaImage/1", "altText": "new alt one", "url": "u1"},
        ],
    }
    delta, fields = compute_changed_proposed(current, proposed)
    assert "image_alts" in fields
    assert "media_images" in fields
    assert len(delta["media_images"]) == 2
    assert delta["media_images"][0]["altText"] == "new alt one"
    assert delta["media_images"][1]["altText"] == "keep"


def test_merge_media_from_shopify_response() -> None:
    existing = [
        {"id": "gid://shopify/MediaImage/1", "altText": "old", "url": "u1"},
        {"id": "gid://shopify/MediaImage/2", "altText": "b", "url": "u2"},
    ]
    shopify_media = [{"id": "gid://shopify/MediaImage/1", "alt": "from shopify"}]
    merged = merge_media_image_alts(existing, shopify_media=shopify_media)
    assert merged[0]["altText"] == "from shopify"
    assert merged[1]["altText"] == "b"


def test_apply_proposed_values_merges_media_not_subset() -> None:
    from types import SimpleNamespace
    from uuid import uuid4

    product_id = uuid4()
    existing_media = [
        {"id": "gid://shopify/MediaImage/1", "altText": "old1", "url": "u1"},
        {"id": "gid://shopify/MediaImage/2", "altText": "old2", "url": "u2"},
    ]
    product = SimpleNamespace(
        id=product_id,
        title="T",
        handle="h",
        seo_title="s",
        seo_description="m",
        description_html="<p>x</p>",
        description_text="x",
        media_images=existing_media,
        raw_payload={},
    )

    class FakeResult:
        def scalar_one_or_none(self):
            return product

    class FakeSession:
        async def execute(self, _query):
            return FakeResult()

        async def flush(self):
            return None

    proposed = {
        "image_alts": [
            {"image_id": "gid://shopify/MediaImage/1", "proposed_alt": "applied alt"},
        ],
        "media_images": [
            {"id": "gid://shopify/MediaImage/1", "altText": "applied alt", "url": "u1"},
        ],
    }
    shopify_response = {
        "productUpdateMedia": {
            "media": [{"id": "gid://shopify/MediaImage/1", "alt": "applied alt"}],
        },
    }

    import asyncio

    asyncio.run(
        apply_proposed_values_to_product(
            FakeSession(),  # type: ignore[arg-type]
            product_id,
            proposed,
            shopify_node=None,
            shopify_response=shopify_response,
        )
    )
    assert len(product.media_images) == 2
    assert product.media_images[0]["altText"] == "applied alt"
    assert product.media_images[1]["altText"] == "old2"
