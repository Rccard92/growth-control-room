"""Brief payload sanitization tests."""

from app.schemas.brand_brief import DEFAULT_BRIEF_PAYLOAD, sanitize_brief_payload


def test_sanitize_partial_payload_no_raise() -> None:
    raw = {
        "brand_identity": {"brand_name": "Acme"},
        "seo_guidelines": {
            "priority_pages": [{"url": "/shop", "label": "Shop"}, "About us"],
        },
        "claims_compliance": {
            "forbidden_claims": [{"text": "cura malattie", "title": "medical"}],
        },
    }
    payload, warnings = sanitize_brief_payload(raw)
    assert payload["brand_identity"]["brand_name"] == "Acme"
    assert len(payload["seo_guidelines"]["priority_pages"]) == 2
    assert "voice_and_tone" in payload
    assert isinstance(warnings, list)


def test_sanitize_empty_returns_defaults() -> None:
    payload, warnings = sanitize_brief_payload(None)
    assert payload == DEFAULT_BRIEF_PAYLOAD
    assert warnings == []


def test_sanitize_coerces_scalar_to_list() -> None:
    raw = {"missing_information": "solo un gap"}
    payload, warnings = sanitize_brief_payload(raw)
    assert payload["missing_information"] == ["solo un gap"]
    assert any("missing_information" in w for w in warnings)
