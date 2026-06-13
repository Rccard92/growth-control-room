import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

from app.services.shopify.metafield_utils import (
    is_ai_generatable_metafield_type,
    is_editable_metafield_type,
)


def test_editable_text_types() -> None:
    assert is_editable_metafield_type("single_line_text_field")
    assert is_editable_metafield_type("multi_line_text_field")
    assert is_editable_metafield_type("rich_text_field")


def test_not_editable_number_type() -> None:
    assert not is_editable_metafield_type("number_integer")


def test_json_editable_when_round_trip_ok() -> None:
    value = '{"a":1,"b":"c"}'
    assert is_editable_metafield_type("json", value)


def test_json_not_editable_invalid() -> None:
    assert not is_editable_metafield_type("json", "{bad json")


def test_ai_generatable_includes_text_and_json() -> None:
    assert is_ai_generatable_metafield_type("single_line_text_field")
    assert is_ai_generatable_metafield_type("json", '{"x":1}')
