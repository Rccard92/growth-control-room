"""External source route registration tests."""

from app.api.routes import brand_intelligence


def test_external_source_routes_registered() -> None:
    paths = {route.path for route in brand_intelligence.router.routes}
    base = "/projects/{project_id}/brand-intelligence"
    assert f"{base}/import-batches" in paths
    assert f"{base}/import-batches/{{batch_id}}/external-sources" in paths
    assert f"{base}/import-batches/{{batch_id}}/fetch-sources" in paths
