"""Normalized JSON output schema for Claude SEO Skill Library."""

from __future__ import annotations

from typing import Any

ALLOWED_SEVERITIES = frozenset({"critical", "high", "medium", "low", "info"})
ALLOWED_PRIORITIES = frozenset({"high", "medium", "low"})
ALLOWED_OWNER_TYPES = frozenset({"content", "dev", "seo", "design", "ads"})
ALLOWED_EFFORTS = frozenset({"low", "medium", "high"})

DEFAULT_SEVERITY = "info"
DEFAULT_PRIORITY = "medium"
DEFAULT_OWNER_TYPE = "seo"
DEFAULT_EFFORT = "medium"

SEO_SKILL_OUTPUT_SCHEMA_DESCRIPTION = """
Rispondi con un singolo oggetto JSON valido con questa struttura:

{
  "skillKey": "<skill_key>",
  "summary": "<sintesi esecutiva stringa>",
  "score": <numero intero 0-100 o null se non valutabile>,
  "findings": [
    {
      "severity": "critical|high|medium|low|info",
      "area": "<area SEO>",
      "title": "<titolo finding>",
      "description": "<descrizione>",
      "evidence": "<evidenza dall'input>",
      "recommendation": "<raccomandazione>",
      "howToValidate": "<come verificare>",
      "priority": "high|medium|low"
    }
  ],
  "recommendations": [
    {
      "title": "<titolo>",
      "description": "<descrizione>",
      "priority": "high|medium|low",
      "impact": "high|medium|low",
      "effort": "low|medium|high"
    }
  ],
  "tasks": [
    {
      "title": "<titolo task>",
      "description": "<descrizione task>",
      "priority": "high|medium|low",
      "ownerType": "content|dev|seo|design|ads",
      "estimatedEffort": "low|medium|high"
    }
  ],
  "artifacts": {
    "jsonLd": [<oggetti JSON-LD suggeriti>],
    "markdownReport": "<report markdown opzionale>",
    "shopifySidekickPrompts": [<prompt operativi>],
    "implementationNotes": [<note implementative>]
  },
  "warnings": [<stringhe su dati mancanti o limiti>]
}

Regole:
- Restituisci SOLO JSON valido, senza markdown o testo extra.
- Non inventare dati non supportati dall'input: se mancano, usa warnings.
- Usa severity e priority coerenti con l'impatto reale.
""".strip()


def get_output_schema_instruction(skill_key: str) -> str:
    return f"Skill key: {skill_key}\n\n{SEO_SKILL_OUTPUT_SCHEMA_DESCRIPTION}"


def _empty_artifacts() -> dict[str, Any]:
    return {
        "jsonLd": [],
        "markdownReport": "",
        "shopifySidekickPrompts": [],
        "implementationNotes": [],
    }


def get_minimal_empty_skill_output(skill_key: str) -> dict[str, Any]:
    return {
        "skillKey": skill_key,
        "summary": "",
        "score": None,
        "findings": [],
        "recommendations": [],
        "tasks": [],
        "artifacts": _empty_artifacts(),
        "warnings": [],
    }


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _as_string(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _normalize_enum(value: Any, allowed: frozenset[str], default: str) -> str:
    normalized = _as_string(value).strip().lower()
    if normalized in allowed:
        return normalized
    return default


def _normalize_score(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        score = int(float(value))
    except (TypeError, ValueError):
        return None
    if score < 0:
        return 0
    if score > 100:
        return 100
    return score


def _normalize_finding(item: Any) -> dict[str, Any]:
    data = _as_dict(item)
    return {
        "severity": _normalize_enum(
            data.get("severity"), ALLOWED_SEVERITIES, DEFAULT_SEVERITY
        ),
        "area": _as_string(data.get("area")),
        "title": _as_string(data.get("title")),
        "description": _as_string(data.get("description")),
        "evidence": _as_string(data.get("evidence")),
        "recommendation": _as_string(data.get("recommendation")),
        "howToValidate": _as_string(data.get("howToValidate")),
        "priority": _normalize_enum(
            data.get("priority"), ALLOWED_PRIORITIES, DEFAULT_PRIORITY
        ),
    }


def _normalize_recommendation(item: Any) -> dict[str, Any]:
    data = _as_dict(item)
    return {
        "title": _as_string(data.get("title")),
        "description": _as_string(data.get("description")),
        "priority": _normalize_enum(
            data.get("priority"), ALLOWED_PRIORITIES, DEFAULT_PRIORITY
        ),
        "impact": _normalize_enum(
            data.get("impact"), ALLOWED_PRIORITIES, DEFAULT_PRIORITY
        ),
        "effort": _normalize_enum(data.get("effort"), ALLOWED_EFFORTS, DEFAULT_EFFORT),
    }


def _normalize_task(item: Any) -> dict[str, Any]:
    data = _as_dict(item)
    return {
        "title": _as_string(data.get("title")),
        "description": _as_string(data.get("description")),
        "priority": _normalize_enum(
            data.get("priority"), ALLOWED_PRIORITIES, DEFAULT_PRIORITY
        ),
        "ownerType": _normalize_enum(
            data.get("ownerType"),
            ALLOWED_OWNER_TYPES,
            DEFAULT_OWNER_TYPE,
        ),
        "estimatedEffort": _normalize_enum(
            data.get("estimatedEffort"),
            ALLOWED_EFFORTS,
            DEFAULT_EFFORT,
        ),
    }


def _normalize_artifacts(value: Any) -> dict[str, Any]:
    data = _as_dict(value)
    json_ld = data.get("jsonLd")
    sidekick = data.get("shopifySidekickPrompts")
    notes = data.get("implementationNotes")
    return {
        "jsonLd": json_ld if isinstance(json_ld, list) else [],
        "markdownReport": _as_string(data.get("markdownReport")),
        "shopifySidekickPrompts": sidekick if isinstance(sidekick, list) else [],
        "implementationNotes": notes if isinstance(notes, list) else [],
    }


def normalize_skill_output(
    skill_key: str,
    raw_output: dict[str, Any] | None,
) -> dict[str, Any]:
    base = get_minimal_empty_skill_output(skill_key)
    if not raw_output:
        return base

    normalized = dict(base)
    normalized["skillKey"] = _as_string(raw_output.get("skillKey")) or skill_key
    normalized["summary"] = _as_string(raw_output.get("summary"))
    normalized["score"] = _normalize_score(raw_output.get("score"))
    normalized["findings"] = [
        _normalize_finding(item) for item in _as_list(raw_output.get("findings"))
    ]
    normalized["recommendations"] = [
        _normalize_recommendation(item)
        for item in _as_list(raw_output.get("recommendations"))
    ]
    normalized["tasks"] = [
        _normalize_task(item) for item in _as_list(raw_output.get("tasks"))
    ]
    normalized["artifacts"] = _normalize_artifacts(raw_output.get("artifacts"))
    warnings = raw_output.get("warnings")
    normalized["warnings"] = [
        _as_string(item) for item in _as_list(warnings) if _as_string(item)
    ]
    return normalized
