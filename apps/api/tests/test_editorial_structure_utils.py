"""Tests for editorial structure helpers."""

from app.schemas.content_seo_editorial import BriefH2Section
from app.services.content.editorial_structure_profiles import (
    is_simple_customer_doubt,
    resolve_structure_profile,
)
from app.services.content.editorial_structure_utils import (
    coerce_h2_h3_structure,
    count_h2_h3,
    trim_structure,
)


def test_coerce_h2_h3_structure_legacy_strings() -> None:
    sections = coerce_h2_h3_structure(
        ["H2: Perché il miele cristallizza", "H3: Dettaglio", "H2: Come usarlo"]
    )
    assert len(sections) == 2
    assert sections[0].h2 == "Perché il miele cristallizza"
    assert sections[0].h3 == ["Dettaglio"]
    assert sections[1].h2 == "Come usarlo"


def test_coerce_h2_h3_structure_objects() -> None:
    sections = coerce_h2_h3_structure(
        [
            {"h2": "Perché il miele cristallizza", "h3": []},
            {"h2": "Il miele cristallizzato è difettoso?", "h3": []},
        ]
    )
    assert len(sections) == 2
    assert sections[0].h3 == []


def test_trim_structure_limits_h2_and_h3() -> None:
    sections = [
        BriefH2Section(h2=f"Sezione {i}", h3=[f"Sotto {i}a", f"Sotto {i}b"])
        for i in range(6)
    ]
    trimmed, was_trimmed = trim_structure(sections, max_h2=5, max_h3=3)
    assert was_trimmed is True
    h2_count, h3_count = count_h2_h3(trimmed)
    assert h2_count == 5
    assert h3_count <= 3


def test_trim_structure_drops_duplicate_h3() -> None:
    sections = [BriefH2Section(h2="Perché il miele cristallizza", h3=["Perché il miele cristallizza"])]
    trimmed, was_trimmed = trim_structure(sections, max_h2=5, max_h3=3)
    assert was_trimmed is True
    assert trimmed[0].h3 == []


def test_is_simple_customer_doubt() -> None:
    assert is_simple_customer_doubt("Perché il miele cristallizza?") is True
    assert is_simple_customer_doubt("Guida completa al mondo del miele artigianale e biologico") is False


def test_resolve_structure_profile_simple_title() -> None:
    profile = resolve_structure_profile("product_comparison", "Perché il miele cristallizza?")
    assert profile.structure_complexity == "snella"
    assert profile.max_h2 <= 5
