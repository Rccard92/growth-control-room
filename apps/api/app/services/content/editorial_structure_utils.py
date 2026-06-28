"""Helpers for compact H2/H3 brief structure normalization and trimming."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.schemas.content_seo_editorial import BriefH2Section

_H2_PREFIX = re.compile(r"^h2\s*:\s*", re.IGNORECASE)
_H3_PREFIX = re.compile(r"^h3\s*:\s*", re.IGNORECASE)


def _strip_heading_prefix(text: str) -> str:
    cleaned = _H2_PREFIX.sub("", text.strip())
    cleaned = _H3_PREFIX.sub("", cleaned)
    return cleaned.strip()


def _normalize_h3_list(items: object) -> list[str]:
    if not isinstance(items, list):
        return []
    out: list[str] = []
    for item in items:
        if item is None:
            continue
        text = _strip_heading_prefix(str(item))
        if text:
            out.append(text)
    return out


def coerce_h2_h3_structure(raw: object) -> list["BriefH2Section"]:
    """Accept legacy string[] or structured object[]; return canonical sections."""
    from app.schemas.content_seo_editorial import BriefH2Section

    if raw is None:
        return []
    if isinstance(raw, str):
        raw = [line.strip() for line in raw.splitlines() if line.strip()]
    if not isinstance(raw, list):
        return []

    if raw and all(isinstance(item, dict) for item in raw):
        sections: list[BriefH2Section] = []
        for item in raw:
            assert isinstance(item, dict)
            h2 = _strip_heading_prefix(str(item.get("h2") or ""))
            h3 = _normalize_h3_list(item.get("h3"))
            if h2:
                sections.append(BriefH2Section(h2=h2, h3=h3))
        return sections

    sections: list[BriefH2Section] = []
    current: BriefH2Section | None = None
    for item in raw:
        if item is None:
            continue
        text = str(item).strip()
        if not text:
            continue
        if _H3_PREFIX.match(text):
            h3_title = _strip_heading_prefix(text)
            if h3_title:
                if current is None:
                    current = BriefH2Section(h2="", h3=[h3_title])
                else:
                    current.h3.append(h3_title)
            continue
        if _H2_PREFIX.match(text) or current is None or current.h2:
            if current is not None and current.h2:
                sections.append(current)
            current = BriefH2Section(h2=_strip_heading_prefix(text), h3=[])
        else:
            current.h2 = _strip_heading_prefix(text)
    if current is not None and current.h2:
        sections.append(current)
    return sections


def count_h2_h3(sections: list["BriefH2Section"]) -> tuple[int, int]:
    h2_count = len(sections)
    h3_count = sum(len(section.h3) for section in sections)
    return h2_count, h3_count


def _normalize_for_compare(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _h3_duplicates_h2(h2: str, h3: str) -> bool:
    h2_norm = _normalize_for_compare(h2)
    h3_norm = _normalize_for_compare(h3)
    if not h2_norm or not h3_norm:
        return False
    return h2_norm == h3_norm or h3_norm in h2_norm or h2_norm in h3_norm


def trim_structure(
    sections: list["BriefH2Section"],
    *,
    max_h2: int,
    max_h3: int,
) -> tuple[list["BriefH2Section"], bool]:
    """Trim excess H2/H3; drop H3 that duplicate their H2 title."""
    from app.schemas.content_seo_editorial import BriefH2Section

    trimmed = False
    cleaned: list[BriefH2Section] = []
    total_h3 = 0
    for section in sections:
        if len(cleaned) >= max_h2:
            trimmed = True
            break
        filtered_h3 = [
            h3 for h3 in section.h3 if not _h3_duplicates_h2(section.h2, h3)
        ]
        if len(filtered_h3) < len(section.h3):
            trimmed = True
        remaining_h3_slots = max(0, max_h3 - total_h3)
        if len(filtered_h3) > remaining_h3_slots:
            filtered_h3 = filtered_h3[:remaining_h3_slots]
            trimmed = True
        total_h3 += len(filtered_h3)
        cleaned.append(BriefH2Section(h2=section.h2, h3=filtered_h3))
    if len(sections) > max_h2:
        trimmed = True
    return cleaned, trimmed


def format_h2_h3_for_prompt(sections: list["BriefH2Section"]) -> str:
    if not sections:
        return "—"
    lines: list[str] = []
    for section in sections:
        lines.append(f"- H2: {section.h2}")
        for h3 in section.h3:
            lines.append(f"  - H3: {h3}")
    return "\n".join(lines)


def sections_to_json(sections: list["BriefH2Section"]) -> list[dict[str, Any]]:
    return [{"h2": s.h2, "h3": list(s.h3)} for s in sections]
