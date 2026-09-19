"""Sanity limits on SEO values before they reach Shopify.

These are hard caps, not the scoring targets (30-60 for the SEO title, 120-160
for the meta description) which stay advisory. The point is to stop obviously
broken values -- an empty title, a 2.000-character meta, an invalid handle --
from being written to a live store and coming back as a cryptic Shopify error.
"""

from __future__ import annotations

import re
from typing import Any

MAX_TITLE = 255
MAX_SEO_TITLE = 200
MAX_META_DESCRIPTION = 500
MAX_HANDLE = 255
MAX_IMAGE_ALT = 512

_HANDLE_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

_LENGTH_LIMITS: dict[str, tuple[int, str]] = {
    "product_title": (MAX_TITLE, "Titolo prodotto"),
    "collection_title": (MAX_TITLE, "Titolo collection"),
    "seo_title": (MAX_SEO_TITLE, "SEO title"),
    "meta_description": (MAX_META_DESCRIPTION, "Meta description"),
    "handle": (MAX_HANDLE, "Handle"),
    "image_alt": (MAX_IMAGE_ALT, "Alt immagine"),
}

_NON_EMPTY_FIELDS = ("product_title", "collection_title")


class SeoFieldValidationError(ValueError):
    """A proposed value cannot be written to Shopify."""


def validate_seo_values(values: dict[str, Any]) -> None:
    errors: list[str] = []

    for field, (limit, label) in _LENGTH_LIMITS.items():
        raw = values.get(field)
        if raw is None:
            continue
        text = str(raw).strip()
        if len(text) > limit:
            errors.append(f"{label}: {len(text)} caratteri, il massimo è {limit}.")

    for field in _NON_EMPTY_FIELDS:
        if field in values and not str(values.get(field) or "").strip():
            errors.append(f"{_LENGTH_LIMITS[field][1]}: non può essere vuoto.")

    handle = values.get("handle")
    if handle is not None:
        normalized = str(handle).strip()
        if not normalized:
            errors.append("Handle: non può essere vuoto.")
        elif not _HANDLE_PATTERN.match(normalized):
            errors.append(
                "Handle: usa solo lettere minuscole, numeri e trattini singoli "
                f"(valore ricevuto: '{normalized}')."
            )

    for entry in values.get("image_alts") or []:
        if not isinstance(entry, dict):
            continue
        alt = str(entry.get("proposed_alt") or entry.get("alt") or "").strip()
        if len(alt) > MAX_IMAGE_ALT:
            errors.append(f"Alt immagine: {len(alt)} caratteri, il massimo è {MAX_IMAGE_ALT}.")

    if errors:
        raise SeoFieldValidationError(" ".join(errors))
