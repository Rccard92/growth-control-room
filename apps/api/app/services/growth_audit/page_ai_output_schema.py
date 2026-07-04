"""JSON output schema for Growth Audit page-level AI/GEO/CRO analysis."""

from __future__ import annotations

from typing import Any

ALLOWED_CATEGORIES = frozenset({"seo", "content", "geo", "cro", "ads"})
ALLOWED_SEVERITIES = frozenset({"critical", "high", "medium", "low", "info"})
ALLOWED_PRIORITIES = frozenset({"high", "medium", "low"})
ALLOWED_IMPACTS = frozenset({"high", "medium", "low"})
ALLOWED_EFFORTS = frozenset({"low", "medium", "high"})
ALLOWED_OWNER_TYPES = frozenset({"seo", "content", "dev", "design", "ads"})

MAX_FINDINGS = 8
MAX_TASKS = 8
MAX_RECOMMENDATIONS = 6
MAX_SUMMARY_LEN = 900


def _strict_object_schema(
    *,
    properties: dict[str, Any],
    required: list[str] | None = None,
) -> dict[str, Any]:
    keys = required if required is not None else list(properties.keys())
    return {
        "type": "object",
        "properties": properties,
        "required": keys,
        "additionalProperties": False,
    }


def _enum_schema(values: frozenset[str]) -> dict[str, Any]:
    return {"type": "string", "enum": sorted(values)}


def _string_schema(max_length: int) -> dict[str, Any]:
    return {"type": "string", "maxLength": max_length}


def _score_schema() -> dict[str, Any]:
    return {
        "anyOf": [
            {"type": "integer", "minimum": 0, "maximum": 100},
            {"type": "null"},
        ],
    }


def get_growth_audit_page_ai_output_json_schema() -> dict[str, Any]:
    finding_schema = _strict_object_schema(
        properties={
            "category": _enum_schema(ALLOWED_CATEGORIES),
            "severity": _enum_schema(ALLOWED_SEVERITIES),
            "priority": _enum_schema(ALLOWED_PRIORITIES),
            "title": _string_schema(160),
            "description": _string_schema(700),
            "evidence": _string_schema(500),
            "recommendation": _string_schema(700),
            "howToValidate": _string_schema(500),
            "impact": _enum_schema(ALLOWED_IMPACTS),
            "effort": _enum_schema(ALLOWED_EFFORTS),
        },
    )
    task_schema = _strict_object_schema(
        properties={
            "title": _string_schema(160),
            "description": _string_schema(600),
            "ownerType": _enum_schema(ALLOWED_OWNER_TYPES),
            "priority": _enum_schema(ALLOWED_PRIORITIES),
            "estimatedEffort": _enum_schema(ALLOWED_EFFORTS),
        },
    )
    recommendation_schema = _strict_object_schema(
        properties={
            "title": _string_schema(160),
            "description": _string_schema(700),
            "priority": _enum_schema(ALLOWED_PRIORITIES),
        },
    )
    artifacts_schema = {
        "type": "object",
        "properties": {
            "shopifyEditHints": {
                "type": "array",
                "maxItems": 6,
                "items": _string_schema(400),
            },
            "croChecklist": {
                "type": "array",
                "maxItems": 8,
                "items": _string_schema(300),
            },
            "geoChecklist": {
                "type": "array",
                "maxItems": 8,
                "items": _string_schema(300),
            },
            "adsReadinessNotes": {
                "type": "array",
                "maxItems": 6,
                "items": _string_schema(400),
            },
        },
        "additionalProperties": False,
    }
    return _strict_object_schema(
        properties={
            "score": _score_schema(),
            "seoScore": _score_schema(),
            "geoScore": _score_schema(),
            "croScore": _score_schema(),
            "adsReadinessScore": _score_schema(),
            "summary": _string_schema(MAX_SUMMARY_LEN),
            "pageType": _string_schema(50),
            "findings": {
                "type": "array",
                "maxItems": MAX_FINDINGS,
                "items": finding_schema,
            },
            "tasks": {
                "type": "array",
                "maxItems": MAX_TASKS,
                "items": task_schema,
            },
            "recommendations": {
                "type": "array",
                "maxItems": MAX_RECOMMENDATIONS,
                "items": recommendation_schema,
            },
            "artifacts": artifacts_schema,
        },
    )


GROWTH_AUDIT_PAGE_AI_SCHEMA_INSTRUCTION = """
Rispondi con un singolo oggetto JSON valido. Nessun markdown fuori dal JSON.
Limiti: max 8 findings, max 8 tasks, max 6 recommendations, summary max 900 caratteri.
CRO e neuromarketing: analisi euristica basata su segnali pagina, NON dati comportamentali reali.
""".strip()


def get_output_schema_instruction() -> str:
    return GROWTH_AUDIT_PAGE_AI_SCHEMA_INSTRUCTION


def _clamp_score(value: Any) -> int | None:
    if value is None:
        return None
    try:
        score = int(value)
    except (TypeError, ValueError):
        return None
    return max(0, min(100, score))


def _pick_enum(value: Any, allowed: frozenset[str], default: str) -> str:
    if isinstance(value, str) and value in allowed:
        return value
    return default


def _truncate(value: Any, max_len: int) -> str:
    text = str(value or "").strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def normalize_growth_audit_page_ai_output(
    raw: dict[str, Any] | None,
    *,
    page_type: str,
) -> dict[str, Any]:
    data = raw if isinstance(raw, dict) else {}
    findings_in = data.get("findings") if isinstance(data.get("findings"), list) else []
    tasks_in = data.get("tasks") if isinstance(data.get("tasks"), list) else []
    recs_in = (
        data.get("recommendations") if isinstance(data.get("recommendations"), list) else []
    )
    artifacts_in = data.get("artifacts") if isinstance(data.get("artifacts"), dict) else {}

    findings: list[dict[str, Any]] = []
    for item in findings_in[:MAX_FINDINGS]:
        if not isinstance(item, dict):
            continue
        title = _truncate(item.get("title"), 160)
        if not title:
            continue
        findings.append(
            {
                "category": _pick_enum(item.get("category"), ALLOWED_CATEGORIES, "seo"),
                "severity": _pick_enum(item.get("severity"), ALLOWED_SEVERITIES, "medium"),
                "priority": _pick_enum(item.get("priority"), ALLOWED_PRIORITIES, "medium"),
                "title": title,
                "description": _truncate(item.get("description"), 700),
                "evidence": _truncate(item.get("evidence"), 500),
                "recommendation": _truncate(item.get("recommendation"), 700),
                "howToValidate": _truncate(item.get("howToValidate"), 500),
                "impact": _pick_enum(item.get("impact"), ALLOWED_IMPACTS, "medium"),
                "effort": _pick_enum(item.get("effort"), ALLOWED_EFFORTS, "medium"),
            }
        )

    tasks: list[dict[str, Any]] = []
    for item in tasks_in[:MAX_TASKS]:
        if not isinstance(item, dict):
            continue
        title = _truncate(item.get("title"), 160)
        if not title:
            continue
        tasks.append(
            {
                "title": title,
                "description": _truncate(item.get("description"), 600),
                "ownerType": _pick_enum(item.get("ownerType"), ALLOWED_OWNER_TYPES, "seo"),
                "priority": _pick_enum(item.get("priority"), ALLOWED_PRIORITIES, "medium"),
                "estimatedEffort": _pick_enum(
                    item.get("estimatedEffort"),
                    ALLOWED_EFFORTS,
                    "medium",
                ),
            }
        )

    recommendations: list[dict[str, Any]] = []
    for item in recs_in[:MAX_RECOMMENDATIONS]:
        if not isinstance(item, dict):
            continue
        title = _truncate(item.get("title"), 160)
        if not title:
            continue
        recommendations.append(
            {
                "title": title,
                "description": _truncate(item.get("description"), 700),
                "priority": _pick_enum(item.get("priority"), ALLOWED_PRIORITIES, "medium"),
            }
        )

    def _artifact_list(key: str, max_items: int) -> list[str]:
        raw_list = artifacts_in.get(key)
        if not isinstance(raw_list, list):
            return []
        return [_truncate(v, 400) for v in raw_list[:max_items] if str(v or "").strip()]

    return {
        "score": _clamp_score(data.get("score")),
        "seoScore": _clamp_score(data.get("seoScore")),
        "geoScore": _clamp_score(data.get("geoScore")),
        "croScore": _clamp_score(data.get("croScore")),
        "adsReadinessScore": _clamp_score(data.get("adsReadinessScore")),
        "summary": _truncate(data.get("summary"), MAX_SUMMARY_LEN),
        "pageType": _truncate(data.get("pageType") or page_type, 50),
        "findings": findings,
        "tasks": tasks,
        "recommendations": recommendations,
        "artifacts": {
            "shopifyEditHints": _artifact_list("shopifyEditHints", 6),
            "croChecklist": _artifact_list("croChecklist", 8),
            "geoChecklist": _artifact_list("geoChecklist", 8),
            "adsReadinessNotes": _artifact_list("adsReadinessNotes", 6),
        },
    }
