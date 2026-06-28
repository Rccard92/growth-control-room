"""Editorial structure limits by content type for brief and article generation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

StructureComplexity = Literal["snella", "media", "approfondita"]

_SIMPLE_QUESTION_MARKERS = ("?", "perché", "perche", "come", "cos'è", "cos'e", "cosa")


@dataclass(frozen=True)
class StructureProfile:
    word_min: int
    word_max: int
    max_h2: int
    max_h3: int
    max_faq: int
    structure_complexity: StructureComplexity


_DEFAULT_PROFILE = StructureProfile(
    word_min=700,
    word_max=950,
    max_h2=5,
    max_h3=3,
    max_faq=4,
    structure_complexity="snella",
)

_CONTENT_TYPE_PROFILES: dict[str, StructureProfile] = {
    "educational_article": StructureProfile(
        word_min=700,
        word_max=950,
        max_h2=5,
        max_h3=3,
        max_faq=4,
        structure_complexity="snella",
    ),
    "faq_objection_article": StructureProfile(
        word_min=700,
        word_max=950,
        max_h2=5,
        max_h3=3,
        max_faq=4,
        structure_complexity="snella",
    ),
    "recipe": StructureProfile(
        word_min=600,
        word_max=900,
        max_h2=4,
        max_h3=2,
        max_faq=2,
        structure_complexity="snella",
    ),
    "product_guide": StructureProfile(
        word_min=800,
        word_max=1100,
        max_h2=5,
        max_h3=4,
        max_faq=3,
        structure_complexity="media",
    ),
    "brand_storytelling": StructureProfile(
        word_min=700,
        word_max=1000,
        max_h2=4,
        max_h3=2,
        max_faq=2,
        structure_complexity="snella",
    ),
    "product_comparison": StructureProfile(
        word_min=1000,
        word_max=1300,
        max_h2=6,
        max_h3=5,
        max_faq=4,
        structure_complexity="approfondita",
    ),
    "seasonal_article": StructureProfile(
        word_min=1000,
        word_max=1300,
        max_h2=6,
        max_h3=5,
        max_faq=4,
        structure_complexity="approfondita",
    ),
}


def get_structure_profile(content_type: str) -> StructureProfile:
    return _CONTENT_TYPE_PROFILES.get(content_type, _DEFAULT_PROFILE)


def is_simple_customer_doubt(title: str) -> bool:
    """Short titles or question-style topics → lean structure."""
    text = (title or "").strip().lower()
    if not text:
        return False
    word_count = len(text.split())
    if word_count <= 10 and any(marker in text for marker in _SIMPLE_QUESTION_MARKERS):
        return True
    if word_count <= 6:
        return True
    return False


def resolve_structure_profile(content_type: str, title: str) -> StructureProfile:
    base = get_structure_profile(content_type)
    if not is_simple_customer_doubt(title):
        return base
    if base.structure_complexity == "approfondita":
        return StructureProfile(
            word_min=min(base.word_min, 700),
            word_max=min(base.word_max, 950),
            max_h2=min(base.max_h2, 5),
            max_h3=min(base.max_h3, 3),
            max_faq=min(base.max_faq, 4),
            structure_complexity="snella",
        )
    return base


def default_avoid_repetitions(content_type: str, primary_keyword: str) -> list[str]:
    keyword = (primary_keyword or "").strip().lower()
    phrases: list[str] = [
        "non indica un difetto",
        "prodotto agricolo vivo",
        "non è un problema",
        "è del tutto naturale",
    ]
    if "miele" in keyword or "cristall" in keyword:
        phrases.extend(
            [
                "la cristallizzazione è naturale",
                "cristallizzazione è un processo naturale",
                "il miele cristallizzato non è difettoso",
            ]
        )
    if content_type == "recipe":
        phrases.append("ricetta semplice e veloce")
    return list(dict.fromkeys(phrases))
