"""Tests for Growth Audit page AI output JSON schema."""

from app.services.growth_audit.page_ai_output_schema import (
    get_growth_audit_page_ai_output_json_schema,
    normalize_growth_audit_page_ai_output,
)

ARTIFACT_KEYS = frozenset(
    {"shopifyEditHints", "croChecklist", "geoChecklist", "adsReadinessNotes"}
)

ROOT_REQUIRED_KEYS = frozenset(
    {
        "score",
        "seoScore",
        "geoScore",
        "croScore",
        "adsReadinessScore",
        "summary",
        "pageType",
        "findings",
        "tasks",
        "recommendations",
        "artifacts",
    }
)


def _assert_strict_object_schema(schema: dict) -> None:
    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == set(schema["properties"].keys())


def test_schema_artifacts_required_keys() -> None:
    schema = get_growth_audit_page_ai_output_json_schema()
    artifacts = schema["properties"]["artifacts"]

    assert set(artifacts["required"]) == ARTIFACT_KEYS


def test_schema_artifacts_strict() -> None:
    schema = get_growth_audit_page_ai_output_json_schema()
    artifacts = schema["properties"]["artifacts"]

    _assert_strict_object_schema(artifacts)


def test_schema_root_required_fields() -> None:
    schema = get_growth_audit_page_ai_output_json_schema()

    _assert_strict_object_schema(schema)
    assert set(schema["required"]) == ROOT_REQUIRED_KEYS


def test_normalize_fills_missing_artifacts() -> None:
    normalized = normalize_growth_audit_page_ai_output({}, page_type="product")

    assert normalized["artifacts"] == {
        "shopifyEditHints": [],
        "croChecklist": [],
        "geoChecklist": [],
        "adsReadinessNotes": [],
    }


def test_normalize_fills_partial_artifacts() -> None:
    normalized = normalize_growth_audit_page_ai_output(
        {
            "summary": "Test",
            "artifacts": {"shopifyEditHints": ["Aggiorna meta title"]},
        },
        page_type="product",
    )

    assert normalized["artifacts"]["shopifyEditHints"] == ["Aggiorna meta title"]
    assert normalized["artifacts"]["croChecklist"] == []
    assert normalized["artifacts"]["geoChecklist"] == []
    assert normalized["artifacts"]["adsReadinessNotes"] == []
