import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

from app.services.content.seo_field_keys import (
    filter_proposed_by_whitelist,
    normalize_api_fields_to_snake,
    whitelist_changed_fields,
)
from app.services.content.seo_proposal_diff import compute_changed_proposed


def test_server_diff_ignores_unchanged_value() -> None:
    current = {"meta_description": "Già uguale", "product_title": "Miele"}
    fields = {"metaDescription": "Già uguale", "title": "Nuovo titolo"}
    proposed_snake = normalize_api_fields_to_snake("product", fields)
    whitelist = whitelist_changed_fields("product", ["metaDescription", "title"])
    filtered = filter_proposed_by_whitelist(proposed_snake, whitelist)
    delta, changed = compute_changed_proposed(current, filtered)
    assert "meta_description" not in delta
    assert delta.get("product_title") == "Nuovo titolo"
    assert "meta_description" not in changed
