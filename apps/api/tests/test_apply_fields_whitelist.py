import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

from app.services.content.seo_field_keys import (
    filter_proposed_by_whitelist,
    normalize_api_fields_to_snake,
    whitelist_changed_fields,
)
from app.services.content.seo_proposal_diff import compute_changed_proposed


def test_whitelist_ignores_extra_fields_in_body() -> None:
    current = {"meta_description": "Vecchia", "product_title": "Titolo originale"}
    fields = {
        "metaDescription": "Nuova meta",
        "title": "Titolo che non deve passare",
    }
    proposed_snake = normalize_api_fields_to_snake("product", fields)
    whitelist = whitelist_changed_fields("product", ["metaDescription"])
    filtered = filter_proposed_by_whitelist(proposed_snake, whitelist)
    delta, fields_changed = compute_changed_proposed(current, filtered)
    assert "meta_description" in delta
    assert "product_title" not in delta
    assert fields_changed == ["meta_description"]


def test_whitelist_snake_case_from_manual_save() -> None:
    whitelist = whitelist_changed_fields("product", ["meta_description", "seo_title"])
    assert whitelist == {"meta_description", "seo_title"}
