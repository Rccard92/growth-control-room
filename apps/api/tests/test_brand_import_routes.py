"""Brand import API route registration tests."""

from app.api.routes import brand_intelligence


def test_import_routes_registered() -> None:
    paths = {route.path for route in brand_intelligence.router.routes}
    base = "/projects/{project_id}/brand-intelligence"
    assert f"{base}/sources/upload" in paths
    assert f"{base}/sources" in paths
    assert f"{base}/sources/{{document_id}}/extract" in paths
    assert f"{base}/sources/extract-batch" in paths
    assert f"{base}/extracted-facts" in paths
    assert f"{base}/extracted-facts/{{fact_id}}" in paths
    assert f"{base}/extracted-facts/apply" in paths
    assert f"{base}/import-batches" in paths
    assert f"{base}/import-batches/{{batch_id}}/start" in paths
    assert f"{base}/import-batches/{{batch_id}}/status" in paths


def test_upload_limits_constants() -> None:
    from app.services.brand_intelligence.text_extraction import MAX_BATCH_FILES, MAX_FILE_BYTES

    assert MAX_BATCH_FILES == 10
    assert MAX_FILE_BYTES == 15 * 1024 * 1024
