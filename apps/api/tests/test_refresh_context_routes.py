"""Refresh context and PUT sources route registration tests."""

from app.api.routes import brand_intelligence


def test_refresh_context_routes_registered() -> None:
    paths = {route.path for route in brand_intelligence.router.routes}
    base = "/projects/{project_id}/brand-intelligence"
    assert f"{base}/import-batches/{{batch_id}}/sources" in paths
    assert f"{base}/import-batches/{{batch_id}}/refresh-context" in paths


def test_sources_update_schema_fields() -> None:
    from app.schemas.brand_intelligence import (
        BrandImportBatchRefreshContextRequest,
        BrandImportBatchSourcesUpdateRequest,
        BrandImportBatchSourcesUpdateResponse,
    )

    req = BrandImportBatchSourcesUpdateRequest.model_validate(
        {"brandName": "Acme", "websiteUrl": "https://acme.com", "sources": []}
    )
    assert req.brand_name == "Acme"

    resp = BrandImportBatchSourcesUpdateResponse.model_validate(
        {
            "batch_id": "00000000-0000-0000-0000-000000000001",
            "sources_saved": 2,
            "message": "ok",
        }
    )
    assert resp.sources_saved == 2

    refresh = BrandImportBatchRefreshContextRequest.model_validate({})
    assert refresh.refetch_external_sources is True
    assert refresh.archive_previous_drafts is True
