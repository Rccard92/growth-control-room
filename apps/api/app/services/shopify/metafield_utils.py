"""Helpers for Shopify product metafield editability and AI generation."""

from __future__ import annotations

import json
from typing import Any

EDITABLE_METAFIELD_TYPES = {
    "single_line_text_field",
    "multi_line_text_field",
    "rich_text_field",
}

AI_GENERATABLE_METAFIELD_TYPES = EDITABLE_METAFIELD_TYPES | {"json"}


def _json_round_trip_ok(value: str) -> bool:
    if not value or not value.strip():
        return True
    try:
        parsed = json.loads(value)
        return json.dumps(parsed, ensure_ascii=False, separators=(",", ":")) == value.strip()
    except (json.JSONDecodeError, TypeError):
        return False


def is_editable_metafield_type(type_name: str, value: str = "") -> bool:
    normalized = (type_name or "").strip().lower()
    if normalized in EDITABLE_METAFIELD_TYPES:
        return True
    if normalized == "json":
        return _json_round_trip_ok(value)
    return False


def is_ai_generatable_metafield_type(type_name: str, value: str = "") -> bool:
    normalized = (type_name or "").strip().lower()
    if normalized in AI_GENERATABLE_METAFIELD_TYPES:
        if normalized == "json":
            return _json_round_trip_ok(value)
        return True
    return False


def metafield_snapshot_item(
    *,
    id: str,
    namespace: str,
    key: str,
    type_name: str,
    value: str | None,
    definition_name: str | None = None,
    definition_description: str | None = None,
    updated_at: Any = None,
) -> dict[str, Any]:
    val = value or ""
    return {
        "id": id,
        "namespace": namespace,
        "key": key,
        "type": type_name,
        "value": val,
        "definition_name": definition_name,
        "definition_description": definition_description,
        "editable": is_editable_metafield_type(type_name, val),
        "ai_generatable": is_ai_generatable_metafield_type(type_name, val),
        "updated_at": updated_at,
    }


def metafields_current_snapshot(rows: list[Any]) -> list[dict[str, Any]]:
    return [
        {
            "id": str(row.id),
            "namespace": row.namespace,
            "key": row.key,
            "type": row.type,
            "value": row.value or "",
        }
        for row in rows
    ]


def rules_metafield_fallback(
    *,
    value: str | None,
    namespace: str,
    key: str,
    type_name: str,
    definition_name: str | None,
    product_title: str | None,
) -> tuple[str, str, str]:
    current_val = (value or "").strip()
    label = definition_name or f"{namespace}.{key}"
    if current_val:
        improved = f"{current_val} — ottimizzato per SEO"
        if len(improved) > 500:
            improved = improved[:500]
        return improved, f"Miglioramento rule-based per {label}", "low"
    base = product_title or label
    if type_name == "multi_line_text_field":
        return (
            f"{base}\n\nDescrizione dettagliata del prodotto.",
            f"Testo generato per {label}",
            "low",
        )
    return base[:255], f"Valore iniziale generato per {label}", "low"
