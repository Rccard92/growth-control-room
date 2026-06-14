"""Shared helpers for API request validation errors."""

from __future__ import annotations


def is_json_string_body_validation_error(errors: list[dict]) -> bool:
    """True when the request body was a JSON string instead of a JSON object."""
    for err in errors:
        loc = err.get("loc")
        if not isinstance(loc, (list, tuple)) or "body" not in loc:
            continue
        body_input = err.get("input")
        if isinstance(body_input, str) and body_input.strip().startswith("{"):
            return True
    return False
