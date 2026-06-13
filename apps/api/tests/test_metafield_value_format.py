import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

from app.services.shopify.metafield_value_format import (
    display_to_rich_text,
    parse_metafield_display_value,
    rich_text_to_display,
    serialize_metafield_value,
)


def test_rich_text_to_display_paragraphs() -> None:
    raw = (
        '{"type":"root","children":[{"type":"paragraph","children":'
        '[{"type":"text","value":"Primo paragrafo"}]},'
        '{"type":"paragraph","children":[{"type":"text","value":"Secondo"}]}]}'
    )
    assert rich_text_to_display(raw) == "Primo paragrafo\n\nSecondo"


def test_display_to_rich_text_from_plain() -> None:
    result = display_to_rich_text("Riga uno\n\nRiga due")
    assert '"type": "root"' in result
    assert "Riga uno" in result
    assert "Riga due" in result


def test_parse_and_serialize_rich_text_roundtrip() -> None:
    raw = display_to_rich_text("Testo semplice")
    display = parse_metafield_display_value("rich_text_field", raw)
    assert display == "Testo semplice"
    serialized = serialize_metafield_value("rich_text_field", display)
    assert '"type": "root"' in serialized


def test_single_line_strips_newlines_on_serialize() -> None:
    assert serialize_metafield_value("single_line_text_field", "a\nb") == "a b"


def test_plain_text_passthrough() -> None:
    assert parse_metafield_display_value("single_line_text_field", "Ciao") == "Ciao"
