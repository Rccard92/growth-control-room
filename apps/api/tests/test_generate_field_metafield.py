import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

from app.services.shopify.metafield_utils import rules_metafield_fallback


def test_rules_metafield_improves_nonempty_value() -> None:
    value, reasoning, risk = rules_metafield_fallback(
        value="Breve testo",
        namespace="custom",
        key="subtitle",
        type_name="single_line_text_field",
        definition_name="Sottotitolo",
        product_title="Miele biologico",
    )
    assert "Breve testo" in value
    assert "ottimizzato" in value.lower() or "SEO" in value
    assert reasoning
    assert risk == "low"


def test_rules_metafield_empty_uses_title() -> None:
    value, reasoning, risk = rules_metafield_fallback(
        value="",
        namespace="custom",
        key="subtitle",
        type_name="single_line_text_field",
        definition_name=None,
        product_title="Olio extravergine",
    )
    assert value == "Olio extravergine"
    assert reasoning
    assert risk == "low"
