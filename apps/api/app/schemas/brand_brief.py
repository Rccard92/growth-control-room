"""Flexible Brand Intelligence Brief payload schemas and sanitization."""

from __future__ import annotations

import copy
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

BriefPayload = dict[str, Any]

DEFAULT_BRIEF_PAYLOAD: BriefPayload = {
    "brand_identity": {
        "brand_name": "",
        "short_description": "",
        "story": "",
        "mission": "",
        "values": [],
        "differentiators": [],
    },
    "voice_and_tone": {
        "tone": "",
        "style_notes": "",
        "words_to_use": [],
        "words_to_avoid": [],
        "examples": [],
    },
    "products_and_categories": [],
    "audience": [],
    "questions_objections_feedback": {
        "common_questions": [],
        "common_objections": [],
        "customer_feedback": [],
        "social_comments_insights": [],
    },
    "claims_compliance": {
        "allowed_claims": [],
        "forbidden_claims": [],
        "caution_claims": [],
        "disclaimers": [],
    },
    "seo_guidelines": {
        "primary_keywords": [],
        "secondary_keywords": [],
        "content_clusters": [],
        "priority_pages": [],
        "internal_linking_notes": "",
        "meta_guidelines": "",
    },
    "content_pillars": [],
    "ads_social_guidelines": {
        "hooks": [],
        "angles": [],
        "pain_points": [],
        "creative_rules": [],
        "cta_examples": [],
    },
    "ai_guardrails": {
        "must_follow": [],
        "must_not": [],
        "needs_review": [],
    },
    "missing_information": [],
    "source_warnings": [],
}


def _as_list(value: Any, warnings: list[str], label: str) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, (str, int, float, bool)):
        warnings.append(f"{label}: valore scalare convertito in lista")
        return [value]
    if isinstance(value, dict):
        warnings.append(f"{label}: oggetto convertito in lista con un elemento")
        return [value]
    warnings.append(f"{label}: tipo non riconosciuto, ignorato")
    return []


def _as_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, dict):
        for key in ("label", "name", "title", "text", "value"):
            if key in value and value[key]:
                return str(value[key])
        return str(value)
    if isinstance(value, list):
        return ", ".join(_as_str(v) for v in value[:5])
    return str(value)


def _merge_dict(default: dict[str, Any], raw: Any, warnings: list[str], path: str) -> dict[str, Any]:
    out = copy.deepcopy(default)
    if not isinstance(raw, dict):
        if raw is not None:
            warnings.append(f"{path}: atteso oggetto, ricevuto {type(raw).__name__}")
        return out
    for key, default_val in default.items():
        if key not in raw:
            continue
        val = raw[key]
        if isinstance(default_val, list):
            out[key] = _as_list(val, warnings, f"{path}.{key}")
        elif isinstance(default_val, dict):
            out[key] = _merge_dict(default_val, val, warnings, f"{path}.{key}")
        else:
            out[key] = _as_str(val, default_val if isinstance(default_val, str) else "")
    for extra_key, extra_val in raw.items():
        if extra_key not in out:
            warnings.append(f"{path}: campo extra '{extra_key}' conservato")
            out[extra_key] = extra_val
    return out


def _normalize_list_items(
    items: list[Any],
    warnings: list[str],
    path: str,
    string_keys: tuple[str, ...] = ("name", "title", "label", "text"),
) -> list[Any]:
    normalized: list[Any] = []
    for i, item in enumerate(items):
        if isinstance(item, str):
            normalized.append(item)
            continue
        if isinstance(item, dict):
            normalized.append(item)
            continue
        warnings.append(f"{path}[{i}]: elemento convertito in stringa")
        normalized.append(_as_str(item))
    return normalized


def _normalize_priority_pages(items: list[Any], warnings: list[str]) -> list[Any]:
    result: list[Any] = []
    for i, item in enumerate(items):
        if isinstance(item, str):
            result.append(item)
        elif isinstance(item, dict):
            result.append(item)
        else:
            warnings.append(f"seo_guidelines.priority_pages[{i}]: oggetto convertito in stringa")
            result.append(_as_str(item))
    return result


def sanitize_brief_payload(raw: dict[str, Any] | None) -> tuple[BriefPayload, list[str]]:
    """Merge AI/user payload with defaults. Never raises."""
    warnings: list[str] = []
    if not raw or not isinstance(raw, dict):
        if raw is not None:
            warnings.append("Payload non è un oggetto: usato skeleton default")
        return copy.deepcopy(DEFAULT_BRIEF_PAYLOAD), warnings

    payload = copy.deepcopy(DEFAULT_BRIEF_PAYLOAD)

    payload["brand_identity"] = _merge_dict(
        DEFAULT_BRIEF_PAYLOAD["brand_identity"],
        raw.get("brand_identity"),
        warnings,
        "brand_identity",
    )
    for list_key in ("values", "differentiators"):
        payload["brand_identity"][list_key] = _normalize_list_items(
            _as_list(payload["brand_identity"].get(list_key), warnings, f"brand_identity.{list_key}"),
            warnings,
            f"brand_identity.{list_key}",
        )

    payload["voice_and_tone"] = _merge_dict(
        DEFAULT_BRIEF_PAYLOAD["voice_and_tone"],
        raw.get("voice_and_tone"),
        warnings,
        "voice_and_tone",
    )
    for list_key in ("words_to_use", "words_to_avoid", "examples"):
        payload["voice_and_tone"][list_key] = _normalize_list_items(
            _as_list(payload["voice_and_tone"].get(list_key), warnings, f"voice_and_tone.{list_key}"),
            warnings,
            f"voice_and_tone.{list_key}",
        )

    payload["products_and_categories"] = _as_list(
        raw.get("products_and_categories"),
        warnings,
        "products_and_categories",
    )
    payload["audience"] = _as_list(raw.get("audience"), warnings, "audience")

    payload["questions_objections_feedback"] = _merge_dict(
        DEFAULT_BRIEF_PAYLOAD["questions_objections_feedback"],
        raw.get("questions_objections_feedback"),
        warnings,
        "questions_objections_feedback",
    )
    for list_key in (
        "common_questions",
        "common_objections",
        "customer_feedback",
        "social_comments_insights",
    ):
        payload["questions_objections_feedback"][list_key] = _normalize_list_items(
            _as_list(
                payload["questions_objections_feedback"].get(list_key),
                warnings,
                f"questions_objections_feedback.{list_key}",
            ),
            warnings,
            f"questions_objections_feedback.{list_key}",
        )

    payload["claims_compliance"] = _merge_dict(
        DEFAULT_BRIEF_PAYLOAD["claims_compliance"],
        raw.get("claims_compliance"),
        warnings,
        "claims_compliance",
    )
    for list_key in ("allowed_claims", "forbidden_claims", "caution_claims", "disclaimers"):
        payload["claims_compliance"][list_key] = _normalize_list_items(
            _as_list(
                payload["claims_compliance"].get(list_key),
                warnings,
                f"claims_compliance.{list_key}",
            ),
            warnings,
            f"claims_compliance.{list_key}",
        )

    payload["seo_guidelines"] = _merge_dict(
        DEFAULT_BRIEF_PAYLOAD["seo_guidelines"],
        raw.get("seo_guidelines"),
        warnings,
        "seo_guidelines",
    )
    for list_key in ("primary_keywords", "secondary_keywords", "content_clusters"):
        payload["seo_guidelines"][list_key] = _normalize_list_items(
            _as_list(
                payload["seo_guidelines"].get(list_key),
                warnings,
                f"seo_guidelines.{list_key}",
            ),
            warnings,
            f"seo_guidelines.{list_key}",
        )
    payload["seo_guidelines"]["priority_pages"] = _normalize_priority_pages(
        _as_list(
            payload["seo_guidelines"].get("priority_pages"),
            warnings,
            "seo_guidelines.priority_pages",
        ),
        warnings,
    )

    payload["content_pillars"] = _as_list(raw.get("content_pillars"), warnings, "content_pillars")

    payload["ads_social_guidelines"] = _merge_dict(
        DEFAULT_BRIEF_PAYLOAD["ads_social_guidelines"],
        raw.get("ads_social_guidelines"),
        warnings,
        "ads_social_guidelines",
    )
    for list_key in ("hooks", "angles", "pain_points", "creative_rules", "cta_examples"):
        payload["ads_social_guidelines"][list_key] = _normalize_list_items(
            _as_list(
                payload["ads_social_guidelines"].get(list_key),
                warnings,
                f"ads_social_guidelines.{list_key}",
            ),
            warnings,
            f"ads_social_guidelines.{list_key}",
        )

    payload["ai_guardrails"] = _merge_dict(
        DEFAULT_BRIEF_PAYLOAD["ai_guardrails"],
        raw.get("ai_guardrails"),
        warnings,
        "ai_guardrails",
    )
    for list_key in ("must_follow", "must_not", "needs_review"):
        payload["ai_guardrails"][list_key] = _normalize_list_items(
            _as_list(payload["ai_guardrails"].get(list_key), warnings, f"ai_guardrails.{list_key}"),
            warnings,
            f"ai_guardrails.{list_key}",
        )

    payload["missing_information"] = _normalize_list_items(
        _as_list(raw.get("missing_information"), warnings, "missing_information"),
        warnings,
        "missing_information",
    )
    payload["source_warnings"] = _normalize_list_items(
        _as_list(raw.get("source_warnings"), warnings, "source_warnings"),
        warnings,
        "source_warnings",
    )

    for top_key, top_val in raw.items():
        if top_key not in DEFAULT_BRIEF_PAYLOAD:
            warnings.append(f"Sezione top-level extra '{top_key}' aggiunta a source_warnings")
            payload["source_warnings"].append(f"Extra section: {top_key}")

    return payload, warnings


def build_markdown_summary(payload: BriefPayload) -> str:
    """Template-based markdown summary from brief payload."""
    identity = payload.get("brand_identity") or {}
    voice = payload.get("voice_and_tone") or {}
    parts: list[str] = []

    brand_name = identity.get("brand_name") or "Brand"
    parts.append(f"# {brand_name} — Brand Intelligence Brief")
    if identity.get("short_description"):
        parts.append(f"\n{identity['short_description']}")
    if identity.get("mission"):
        parts.append(f"\n**Mission:** {identity['mission']}")
    if voice.get("tone"):
        parts.append(f"\n**Tone:** {voice['tone']}")

    products = payload.get("products_and_categories") or []
    if products:
        names = []
        for p in products[:5]:
            if isinstance(p, dict):
                names.append(p.get("name") or p.get("title") or str(p))
            else:
                names.append(str(p))
        parts.append(f"\n**Products:** {', '.join(names)}")

    missing = payload.get("missing_information") or []
    if missing:
        parts.append("\n**Missing information:**")
        for m in missing[:10]:
            parts.append(f"- {m}")

    return "\n".join(parts).strip()


class BrandIntelligenceBriefListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    version: int
    status: str
    title: str
    confidence: float | None = None
    source_batch_id: UUID | None = Field(default=None, serialization_alias="sourceBatchId")
    created_at: datetime = Field(serialization_alias="createdAt")
    approved_at: datetime | None = Field(default=None, serialization_alias="approvedAt")


class BrandIntelligenceBriefRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    project_id: UUID = Field(serialization_alias="projectId")
    source_batch_id: UUID | None = Field(default=None, serialization_alias="sourceBatchId")
    version: int
    status: str
    title: str
    brief_payload: Any = Field(serialization_alias="briefPayload")
    markdown_summary: str | None = Field(default=None, serialization_alias="markdownSummary")
    confidence: float | None = None
    warnings: Any | None = None
    source_document_ids: list[str] = Field(
        default_factory=list, serialization_alias="sourceDocumentIds"
    )
    source_external_ids: list[str] = Field(
        default_factory=list, serialization_alias="sourceExternalIds"
    )
    source_fact_ids: list[str] = Field(default_factory=list, serialization_alias="sourceFactIds")
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")
    approved_at: datetime | None = Field(default=None, serialization_alias="approvedAt")
    archived_at: datetime | None = Field(default=None, serialization_alias="archivedAt")


class BrandIntelligenceBriefUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: str | None = None
    brief_payload: Any | None = Field(default=None, validation_alias="briefPayload")
    markdown_summary: str | None = Field(default=None, validation_alias="markdownSummary")
    warnings: Any | None = None
    status: str | None = None


class GenerateBriefResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    brief_id: UUID = Field(serialization_alias="briefId")
    status: str
    confidence: float | None = None
    message: str
