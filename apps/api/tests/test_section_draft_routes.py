"""Section draft route registration tests."""

from app.api.routes import brand_intelligence


def test_section_draft_routes_registered() -> None:
    paths = {route.path for route in brand_intelligence.router.routes}
    base = "/projects/{project_id}/brand-intelligence"
    assert f"{base}/import-batches/{{batch_id}}/synthesize" in paths
    assert f"{base}/section-drafts" in paths
    assert f"{base}/section-drafts/{{draft_id}}" in paths
    assert f"{base}/section-drafts/{{draft_id}}/apply" in paths
    assert f"{base}/section-drafts/apply-batch" in paths
    assert f"{base}/section-drafts/{{draft_id}}/regenerate" in paths


def test_section_draft_keys() -> None:
    from app.schemas.section_drafts import SECTION_DRAFT_KEYS, validate_draft_payload

    assert "brand_profile" in SECTION_DRAFT_KEYS
    payload = validate_draft_payload("brand_profile", {"brand_name": "Test"})
    assert payload["brand_name"] == "Test"
