"""Brief API route registration tests."""

from app.api.routes import brand_intelligence


def test_brief_routes_registered() -> None:
    paths = {route.path for route in brand_intelligence.router.routes}
    base = "/projects/{project_id}/brand-intelligence"
    assert f"{base}/import-batches/{{batch_id}}/generate-brief" in paths
    assert f"{base}/briefs" in paths
    assert f"{base}/briefs/{{brief_id}}" in paths
    assert f"{base}/briefs/{{brief_id}}/approve" in paths
    assert f"{base}/briefs/{{brief_id}}/archive" in paths


def test_generate_brief_response_schema() -> None:
    from app.schemas.brand_brief import GenerateBriefResponse

    resp = GenerateBriefResponse.model_validate(
        {
            "brief_id": "00000000-0000-0000-0000-000000000001",
            "status": "draft",
            "confidence": 0.82,
            "message": "ok",
        }
    )
    assert resp.status == "draft"
    assert resp.confidence == 0.82


def test_overview_has_brief_fields() -> None:
    from app.schemas.brand_intelligence import BrandIntelligenceOverviewResponse

    fields = BrandIntelligenceOverviewResponse.model_fields
    assert "has_approved_brief" in fields
    assert "approved_brief_id" in fields
    assert "pending_brief_count" in fields
