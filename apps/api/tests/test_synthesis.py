"""Synthesis helper unit tests."""

from app.schemas.section_drafts import FACT_SECTION_TO_DRAFT, SECTION_DRAFT_LABELS
from app.services.brand_intelligence.synthesis import SECTION_SYNTHESIS_ORDER, _facts_for_section


class _FakeFact:
    def __init__(self, target_section: str, fact_id: str = "a") -> None:
        self.id = fact_id
        self.target_section = target_section


def test_facts_for_products_categories() -> None:
    facts = [
        _FakeFact("product_knowledge", "1"),
        _FakeFact("category_knowledge", "2"),
        _FakeFact("audience", "3"),
    ]
    result = _facts_for_section(facts, "products_categories")  # type: ignore[arg-type]
    assert len(result) == 2


def test_synthesis_order_has_nine_sections() -> None:
    assert len(SECTION_SYNTHESIS_ORDER) == 9
    assert SECTION_SYNTHESIS_ORDER[0] == "brand_profile"


def test_fact_section_mapping() -> None:
    assert FACT_SECTION_TO_DRAFT["product_knowledge"] == "products_categories"
    assert SECTION_DRAFT_LABELS["claims_compliance"] == "Claims & Compliance"
