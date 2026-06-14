"""Tests for normalize_to_string_list and related helpers."""

from pydantic import BaseModel

from app.services.brand_intelligence.faq_objections_normalize import (
    dict_item_to_string,
    normalize_to_string_list,
)
from app.services.brand_intelligence.faq_objections_service import has_text


def test_normalize_none() -> None:
    assert normalize_to_string_list(None) == []


def test_normalize_string() -> None:
    assert normalize_to_string_list("  testo  ") == ["testo"]


def test_normalize_empty_string() -> None:
    assert normalize_to_string_list("   ") == []


def test_normalize_list_str() -> None:
    assert normalize_to_string_list(["uno", " due ", "uno"]) == ["uno", "due"]


def test_normalize_list_dict_question_answer() -> None:
    result = normalize_to_string_list(
        [{"question": "Spedite?", "answer": "Sì, in 48h"}]
    )
    assert result == ["Domanda: Spedite?\nRisposta: Sì, in 48h"]


def test_normalize_list_dict_objection_answer() -> None:
    result = normalize_to_string_list(
        [{"objection": "Costa troppo", "answer": "Valore artigianale"}]
    )
    assert result == ["Obiezione: Costa troppo\nRisposta consigliata: Valore artigianale"]


def test_normalize_list_dict_myth_correction() -> None:
    result = normalize_to_string_list(
        [{"myth": "Non è naturale", "correction": "È 100% artigianale"}]
    )
    assert result == ["Mito: Non è naturale\nCorrezione: È 100% artigianale"]


def test_normalize_dict_text() -> None:
    result = normalize_to_string_list({"text": "Solo testo"})
    assert result == ["Solo testo"]


def test_normalize_pydantic_like_object() -> None:
    class Entry(BaseModel):
        question: str = "FAQ?"
        answer: str = "Sì"

    result = normalize_to_string_list([Entry()])
    assert result == ["Domanda: FAQ?\nRisposta: Sì"]


def test_normalize_unsupported_item_adds_warning() -> None:
    warnings: list[str] = []
    result = normalize_to_string_list([123, "valida"], warnings)
    assert result == ["valida"]
    assert len(warnings) == 1


def test_dict_item_to_string_title_description() -> None:
    assert dict_item_to_string({"title": "Titolo", "description": "Descrizione"}) == (
        "Titolo — Descrizione"
    )


def test_dict_item_to_string_insight_only() -> None:
    assert dict_item_to_string({"insight": "Cliente scettico"}) == "Insight: Cliente scettico"


def test_normalize_mixed_list_string_and_dict() -> None:
    result = normalize_to_string_list(
        [
            "testo semplice",
            {"question": "FAQ?", "answer": "Sì"},
            None,
            "",
        ]
    )
    assert result == ["testo semplice", "Domanda: FAQ?\nRisposta: Sì"]


def test_normalize_list_with_null_and_empty_items() -> None:
    result = normalize_to_string_list([None, "  ", "valida", {}])
    assert result == ["valida"]


def test_has_text_on_none() -> None:
    assert has_text(None) is False


def test_has_text_on_string() -> None:
    assert has_text("  testo  ") is True
    assert has_text("   ") is False


def test_has_text_on_dict() -> None:
    assert has_text({"question": "Q?", "answer": "A"}) is True


def test_has_text_on_list() -> None:
    assert has_text([{"objection": "Costa troppo"}]) is True
    assert has_text([]) is False


def test_has_text_on_unsupported_type() -> None:
    assert has_text(123) is False
