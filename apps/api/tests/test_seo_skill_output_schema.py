"""Tests for SEO skill output schema normalization."""

from app.services.seo_skills.output_schema import (
    ALLOWED_EFFORTS,
    ALLOWED_OWNER_TYPES,
    ALLOWED_PRIORITIES,
    ALLOWED_SEVERITIES,
    get_minimal_empty_skill_output,
    get_seo_skill_output_json_schema,
    normalize_skill_output,
)


def test_get_minimal_empty_skill_output_returns_complete_structure() -> None:
    output = get_minimal_empty_skill_output("seo_geo")

    assert output["skillKey"] == "seo_geo"
    assert output["summary"] == ""
    assert output["score"] is None
    assert output["findings"] == []
    assert output["recommendations"] == []
    assert output["tasks"] == []
    assert output["artifacts"] == {
        "jsonLd": [],
        "markdownReport": "",
        "shopifySidekickPrompts": [],
        "implementationNotes": [],
    }
    assert output["warnings"] == []


def test_normalize_skill_output_fills_missing_fields() -> None:
    normalized = normalize_skill_output(
        "seo_page",
        {
            "summary": "Pagina migliorabile",
            "findings": [{"title": "Title debole", "severity": "high"}],
        },
    )

    assert normalized["skillKey"] == "seo_page"
    assert normalized["summary"] == "Pagina migliorabile"
    assert normalized["score"] is None
    assert normalized["findings"][0]["severity"] == "high"
    assert normalized["findings"][0]["priority"] == "medium"
    assert normalized["recommendations"] == []
    assert normalized["tasks"] == []
    assert normalized["artifacts"]["jsonLd"] == []


def test_normalize_skill_output_normalizes_invalid_severity_to_info() -> None:
    normalized = normalize_skill_output(
        "seo_page",
        {"findings": [{"severity": "urgent", "title": "Issue"}]},
    )
    assert normalized["findings"][0]["severity"] == "info"


def test_normalize_skill_output_normalizes_invalid_priority_to_medium() -> None:
    normalized = normalize_skill_output(
        "seo_page",
        {
            "recommendations": [{"title": "Fix", "priority": "urgent"}],
            "tasks": [{"title": "Task", "priority": "urgent", "ownerType": "ops"}],
        },
    )
    assert normalized["recommendations"][0]["priority"] == "medium"
    assert normalized["tasks"][0]["priority"] == "medium"
    assert normalized["tasks"][0]["ownerType"] == "seo"


def test_normalize_skill_output_clamps_score_to_0_100() -> None:
    low = normalize_skill_output("seo_page", {"score": -15})
    high = normalize_skill_output("seo_page", {"score": 150})
    invalid = normalize_skill_output("seo_page", {"score": "not-a-number"})

    assert low["score"] == 0
    assert high["score"] == 100
    assert invalid["score"] is None


def test_normalize_skill_output_does_not_crash_on_empty_dict() -> None:
    normalized = normalize_skill_output("seo_audit", {})
    assert normalized["skillKey"] == "seo_audit"
    assert normalized["findings"] == []


def test_normalize_skill_output_does_not_crash_on_none() -> None:
    normalized = normalize_skill_output("seo_audit", None)
    assert normalized["skillKey"] == "seo_audit"
    assert normalized["warnings"] == []


def _assert_strict_object_schema(schema: dict) -> None:
    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == set(schema["properties"].keys())


def test_get_seo_skill_output_json_schema_has_required_top_level_fields() -> None:
    schema = get_seo_skill_output_json_schema()
    _assert_strict_object_schema(schema)
    assert set(schema["required"]) == {
        "skillKey",
        "summary",
        "score",
        "findings",
        "recommendations",
        "tasks",
        "artifacts",
        "warnings",
    }


def test_get_seo_skill_output_json_schema_nested_objects_are_strict() -> None:
    schema = get_seo_skill_output_json_schema()
    findings = schema["properties"]["findings"]["items"]
    recommendations = schema["properties"]["recommendations"]["items"]
    tasks = schema["properties"]["tasks"]["items"]
    artifacts = schema["properties"]["artifacts"]

    _assert_strict_object_schema(findings)
    _assert_strict_object_schema(recommendations)
    _assert_strict_object_schema(tasks)
    _assert_strict_object_schema(artifacts)

    assert set(findings["properties"]["severity"]["enum"]) == set(ALLOWED_SEVERITIES)
    assert set(findings["properties"]["priority"]["enum"]) == set(ALLOWED_PRIORITIES)
    assert set(recommendations["properties"]["impact"]["enum"]) == set(ALLOWED_PRIORITIES)
    assert set(recommendations["properties"]["effort"]["enum"]) == set(ALLOWED_EFFORTS)
    assert set(tasks["properties"]["ownerType"]["enum"]) == set(ALLOWED_OWNER_TYPES)
    assert set(tasks["properties"]["estimatedEffort"]["enum"]) == set(ALLOWED_EFFORTS)
    assert "jsonLd" in artifacts["properties"]
    assert "markdownReport" in artifacts["properties"]
    assert "shopifySidekickPrompts" in artifacts["properties"]
    assert "implementationNotes" in artifacts["properties"]


def test_get_seo_skill_output_json_schema_has_max_items_limits() -> None:
    schema = get_seo_skill_output_json_schema()
    assert schema["properties"]["findings"]["maxItems"] == 6
    assert schema["properties"]["recommendations"]["maxItems"] == 6
    assert schema["properties"]["tasks"]["maxItems"] == 8
    assert schema["properties"]["artifacts"]["properties"]["jsonLd"]["maxItems"] == 2


def test_get_seo_skill_output_json_schema_has_max_length_limits() -> None:
    schema = get_seo_skill_output_json_schema()
    assert schema["properties"]["summary"]["maxLength"] == 900
    assert (
        schema["properties"]["artifacts"]["properties"]["markdownReport"]["maxLength"]
        == 1200
    )
