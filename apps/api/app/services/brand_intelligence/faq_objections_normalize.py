"""Shared normalization helpers for FAQ & Objections list[str] fields."""

from __future__ import annotations

import json
from typing import Protocol, runtime_checkable

_MAX_STRING_LEN = 2000


@runtime_checkable
class _HasModelDump(Protocol):
    def model_dump(self) -> dict[str, object]: ...


def _soft_cap(value: str, max_len: int = _MAX_STRING_LEN) -> str:
    if len(value) <= max_len:
        return value
    return value[:max_len] + "…"


def _get_str_field(data: dict[str, object], *keys: str) -> str:
    for key in keys:
        value = data.get(key)
        if isinstance(value, str):
            trimmed = value.strip()
            if trimmed:
                return trimmed
    return ""


def format_faq_block(question: str, answer: str) -> str:
    q = question.strip()
    a = answer.strip()
    if not q:
        return ""
    if a:
        return f"Domanda: {q}\nRisposta: {a}"
    return f"Domanda: {q}"


def format_myth_block(myth: str, correction: str) -> str:
    m = myth.strip()
    c = correction.strip()
    if not m:
        return ""
    if c:
        return f"Mito: {m}\nCorrezione: {c}"
    return f"Mito: {m}"


def format_objection_answer_block(objection: str, answer: str) -> str:
    o = objection.strip()
    a = answer.strip()
    if not o:
        return ""
    if a:
        return f"Obiezione: {o}\nRisposta consigliata: {a}"
    return f"Obiezione: {o}"


def format_social_block(insight: str, doubt: str, reply: str) -> str:
    parts: list[str] = []
    if insight.strip():
        parts.append(f"Insight: {insight.strip()}")
    if doubt.strip():
        parts.append(f"Dubbio: {doubt.strip()}")
    if reply.strip():
        parts.append(f"Risposta: {reply.strip()}")
    return " | ".join(parts)


def serialize_unknown_object(item: dict[str, object]) -> str:
    try:
        return json.dumps(item, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return str(item)


def dict_item_to_string(item: dict[str, object]) -> str | None:
    question = _get_str_field(item, "question", "domanda")
    answer = _get_str_field(item, "answer", "risposta", "response")
    objection = _get_str_field(item, "objection", "obiezione")
    myth = _get_str_field(item, "myth", "mito", "misconception")
    correction = _get_str_field(item, "correction", "correzione", "clarification")
    insight = _get_str_field(item, "insight")
    doubt = _get_str_field(item, "doubt", "dubbio", "concern")
    suggested_reply = _get_str_field(
        item, "suggestedReply", "suggested_reply", "reply", "rispostaConsigliata"
    )
    title = _get_str_field(item, "title", "titolo")
    description = _get_str_field(item, "description", "descrizione")
    text = _get_str_field(item, "text", "testo", "content")
    value = _get_str_field(item, "value", "valore")

    has_objection_key = any(
        key in item for key in ("objection", "obiezione")
    )
    has_question_key = any(
        key in item for key in ("question", "domanda")
    )

    if has_objection_key or (objection and not has_question_key):
        block = format_objection_answer_block(objection, answer)
        return block or None

    if has_question_key or question:
        block = format_faq_block(question, answer)
        return block or None

    if myth or correction:
        block = format_myth_block(myth, correction)
        return block or None

    if insight or doubt or suggested_reply:
        block = format_social_block(insight, doubt, suggested_reply)
        return block or None

    if title and description:
        return f"{title} — {description}"

    if title:
        return title

    if text:
        return text

    if value:
        return value

    if insight:
        return insight

    if answer:
        return answer

    if item:
        return serialize_unknown_object(item)

    return None


def item_to_string(item: object, warnings: list[str] | None = None) -> str | None:
    if item is None:
        return None

    if isinstance(item, str):
        trimmed = item.strip()
        return trimmed or None

    if isinstance(item, dict):
        return dict_item_to_string(item)

    if isinstance(item, _HasModelDump):
        dumped = item.model_dump()
        if isinstance(dumped, dict):
            return dict_item_to_string(dumped)
        if warnings is not None:
            warnings.append(
                f"Elemento ignorato (model_dump non è dict): {type(item).__name__}"
            )
        return None

    if warnings is not None:
        warnings.append(f"Elemento ignorato (tipo non supportato): {type(item).__name__}")
    return None


def dedupe_strings(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        trimmed = item.strip()
        if not trimmed or trimmed in seen:
            continue
        seen.add(trimmed)
        out.append(_soft_cap(trimmed))
    return out


def normalize_to_string_list(
    value: object | None,
    warnings: list[str] | None = None,
) -> list[str]:
    if value is None:
        return []

    if isinstance(value, str):
        trimmed = value.strip()
        return [_soft_cap(trimmed)] if trimmed else []

    if isinstance(value, dict):
        text = dict_item_to_string(value)
        return [_soft_cap(text)] if text else []

    if isinstance(value, _HasModelDump) and not isinstance(value, dict):
        dumped = value.model_dump()
        return normalize_to_string_list(dumped, warnings)

    if not isinstance(value, list):
        if warnings is not None:
            warnings.append(f"Valore ignorato (tipo non supportato): {type(value).__name__}")
        return []

    collected: list[str] = []
    for item in value:
        text = item_to_string(item, warnings)
        if text:
            collected.append(text)

    return dedupe_strings(collected)


__all__ = [
    "dict_item_to_string",
    "item_to_string",
    "normalize_to_string_list",
    "format_faq_block",
    "format_myth_block",
    "format_objection_answer_block",
    "format_social_block",
    "dedupe_strings",
    "serialize_unknown_object",
]
