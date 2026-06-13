"""Human-friendly parse/serialize for Shopify metafield values."""

from __future__ import annotations

import json
import re
from typing import Any

RICH_TEXT_ROOT = "root"


def _strip_rich_text_node(node: dict[str, Any], parts: list[str]) -> None:
    node_type = str(node.get("type") or "")
    if node_type == "text":
        text = str(node.get("value") or "")
        if text:
            parts.append(text)
        return
    if node_type in ("paragraph", "heading", "list-item"):
        block_parts: list[str] = []
        for child in node.get("children") or []:
            if isinstance(child, dict):
                _strip_rich_text_node(child, block_parts)
        if block_parts:
            parts.append("".join(block_parts))
        return
    for child in node.get("children") or []:
        if isinstance(child, dict):
            _strip_rich_text_node(child, parts)


def rich_text_to_display(raw_value: str) -> str:
    if not raw_value or not raw_value.strip():
        return ""
    stripped = raw_value.strip()
    if not stripped.startswith("{"):
        return stripped
    try:
        data = json.loads(stripped)
    except json.JSONDecodeError:
        return stripped
    if not isinstance(data, dict) or data.get("type") != RICH_TEXT_ROOT:
        return stripped
    parts: list[str] = []
    for child in data.get("children") or []:
        if isinstance(child, dict):
            _strip_rich_text_node(child, parts)
    return "\n\n".join(p.strip() for p in parts if p.strip())


def display_to_rich_text(display_value: str) -> str:
    text = (display_value or "").strip()
    if not text:
        return json.dumps({"type": RICH_TEXT_ROOT, "children": []}, ensure_ascii=False)
    if text.startswith("{"):
        try:
            data = json.loads(text)
            if isinstance(data, dict) and data.get("type") == RICH_TEXT_ROOT:
                return json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        except json.JSONDecodeError:
            pass
    paragraphs = re.split(r"\n\s*\n", text)
    children: list[dict[str, Any]] = []
    for para in paragraphs:
        line = para.strip()
        if not line:
            continue
        children.append(
            {
                "type": "paragraph",
                "children": [{"type": "text", "value": line}],
            }
        )
    if not children:
        children.append(
            {
                "type": "paragraph",
                "children": [{"type": "text", "value": text}],
            }
        )
    return json.dumps({"type": RICH_TEXT_ROOT, "children": children}, ensure_ascii=False)


def parse_metafield_display_value(type_name: str, raw_value: str | None) -> str:
    normalized = (type_name or "").strip().lower()
    val = raw_value or ""
    if normalized == "rich_text_field":
        return rich_text_to_display(val)
    if normalized == "boolean":
        low = val.strip().lower()
        if low in ("true", "1", "yes"):
            return "Sì"
        if low in ("false", "0", "no"):
            return "No"
        return val
    return val


def serialize_metafield_value(type_name: str, display_value: str) -> str:
    normalized = (type_name or "").strip().lower()
    text = display_value or ""
    if normalized == "rich_text_field":
        try:
            return display_to_rich_text(text)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Impossibile convertire il testo in formato rich text Shopify valido."
            ) from exc
    if normalized == "single_line_text_field":
        return text.replace("\n", " ").strip()
    return text
