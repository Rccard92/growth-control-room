import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

from app.services.content.seo_proposal_diff import compute_changed_proposed


def test_diff_unchanged_title_excluded() -> None:
    current = {"product_title": "Miele", "seo_title": "Old"}
    proposed = {"product_title": "Miele", "seo_title": "New SEO"}
    delta, fields = compute_changed_proposed(current, proposed)
    assert "product_title" not in delta
    assert delta["seo_title"] == "New SEO"
    assert fields == ["seo_title"]


def test_diff_meta_description_changed() -> None:
    current = {"meta_description": ""}
    proposed = {"meta_description": "Scopri il miele italiano"}
    delta, fields = compute_changed_proposed(current, proposed)
    assert delta["meta_description"] == "Scopri il miele italiano"
    assert fields == ["meta_description"]


def test_diff_image_alts_partial() -> None:
    current = {
        "media_images": [
            {"id": "gid://shopify/MediaImage/1", "altText": ""},
            {"id": "gid://shopify/MediaImage/2", "altText": "unchanged"},
        ],
    }
    proposed = {
        "image_alts": [
            {
                "image_id": "gid://shopify/MediaImage/1",
                "proposed_alt": "Miele biologico in barattolo",
            }
        ],
        "media_images": [
            {"id": "gid://shopify/MediaImage/1", "altText": "Miele biologico in barattolo"}
        ],
    }
    delta, fields = compute_changed_proposed(current, proposed)
    assert "image_alts" in fields
    assert "media_images" in fields
    assert len(delta["image_alts"]) == 1
    assert len(delta["media_images"]) == 2
    assert delta["media_images"][0]["altText"] == "Miele biologico in barattolo"
    assert delta["media_images"][1]["altText"] == "unchanged"


def test_diff_empty_when_no_changes() -> None:
    current = {"handle": "miele", "seo_title": "Titolo"}
    proposed = {"handle": "miele", "seo_title": "Titolo"}
    delta, fields = compute_changed_proposed(current, proposed)
    assert delta == {}
    assert fields == []
