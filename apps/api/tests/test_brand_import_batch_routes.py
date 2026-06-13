"""Import batch API route registration tests."""

from app.api.routes import brand_intelligence


def test_import_batch_routes_registered() -> None:
    paths = {route.path for route in brand_intelligence.router.routes}
    base = "/projects/{project_id}/brand-intelligence"
    assert f"{base}/import-batches" in paths
    assert f"{base}/import-batches/{{batch_id}}/start" in paths
    assert f"{base}/import-batches/{{batch_id}}/status" in paths


def test_upload_response_includes_batch() -> None:
    from app.schemas.brand_intelligence import BrandSourceDocumentsUploadResponse

    fields = BrandSourceDocumentsUploadResponse.model_fields
    assert "batch_id" in fields
    assert "status" in fields


def test_apply_facts_accepts_batch_id() -> None:
    from app.schemas.brand_intelligence import BrandApplyFactsRequest

    req = BrandApplyFactsRequest.model_validate({"factIds": [], "batchId": None})
    assert req.batch_id is None
