"""Helpers for Shopify product metafield editability and AI generation."""

from __future__ import annotations

import json
from typing import Any

from app.services.shopify.metafield_value_format import parse_metafield_display_value

EDITABLE_METAFIELD_TYPES = {
    "single_line_text_field",
    "multi_line_text_field",
    "rich_text_field",
}

AI_GENERATABLE_METAFIELD_TYPES = EDITABLE_METAFIELD_TYPES

READONLY_METAFIELD_TYPES = {
    "json",
    "metaobject_reference",
    "list.metaobject_reference",
    "file_reference",
    "product_reference",
    "number",
    "boolean",
    "date",
    "date_time",
    "url",
    "color",
    "rating",
    "dimension",
    "volume",
    "weight",
    "money",
}


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
    definition_id: str | None = None,
    metafield_id: str | None = None,
    raw_value: str | None = None,
    display_value: str | None = None,
    exists_on_product: bool = True,
    is_empty: bool | None = None,
) -> dict[str, Any]:
    raw = raw_value if raw_value is not None else (value or "")
    display = display_value if display_value is not None else parse_metafield_display_value(
        type_name, raw
    )
    empty = is_empty if is_empty is not None else not str(display).strip()
    def_id = definition_id or id
    mf_id = metafield_id
    ui_id = mf_id or def_id
    return {
        "id": ui_id,
        "definition_id": def_id,
        "metafield_id": mf_id,
        "namespace": namespace,
        "key": key,
        "type": type_name,
        "value": display,
        "raw_value": raw,
        "display_value": display,
        "definition_name": definition_name,
        "definition_description": definition_description,
        "editable": is_editable_metafield_type(type_name, raw),
        "ai_generatable": is_ai_generatable_metafield_type(type_name, raw),
        "exists_on_product": exists_on_product,
        "is_empty": empty,
        "updated_at": updated_at,
    }


def merged_metafield_item(
    *,
    definition: Any | None,
    value_row: Any | None,
) -> dict[str, Any]:
    if definition is not None:
        type_name = definition.type_name
        namespace = definition.namespace
        key = definition.key
        def_name = definition.name
        def_desc = definition.description
        definition_id = str(definition.id)
        if value_row is not None:
            raw = value_row.value or ""
            return metafield_snapshot_item(
                id=str(value_row.id),
                definition_id=definition_id,
                metafield_id=str(value_row.id),
                namespace=namespace,
                key=key,
                type_name=type_name,
                value=raw,
                raw_value=raw,
                definition_name=def_name or value_row.definition_name,
                definition_description=def_desc or value_row.definition_description,
                updated_at=value_row.updated_at,
                exists_on_product=True,
            )
        return metafield_snapshot_item(
            id=definition_id,
            definition_id=definition_id,
            metafield_id=None,
            namespace=namespace,
            key=key,
            type_name=type_name,
            value="",
            raw_value="",
            definition_name=def_name,
            definition_description=def_desc,
            exists_on_product=False,
            is_empty=True,
        )

    assert value_row is not None
    raw = value_row.value or ""
    row_id = str(value_row.id)
    return metafield_snapshot_item(
        id=row_id,
        definition_id=row_id,
        metafield_id=row_id,
        namespace=value_row.namespace,
        key=value_row.key,
        type_name=value_row.type,
        value=raw,
        raw_value=raw,
        definition_name=value_row.definition_name,
        definition_description=value_row.definition_description,
        updated_at=value_row.updated_at,
        exists_on_product=True,
    )


def metafields_current_snapshot(rows: list[Any]) -> list[dict[str, Any]]:
    return [
        {
            "id": str(row.id),
            "metafield_id": str(row.id),
            "namespace": row.namespace,
            "key": row.key,
            "type": row.type,
            "value": row.value or "",
            "raw_value": row.value or "",
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
