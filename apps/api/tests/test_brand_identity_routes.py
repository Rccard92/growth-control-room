"""Brand Identity API route registration tests."""

from app.api.routes import brand_intelligence


def test_brand_identity_routes_registered() -> None:
    paths = {route.path for route in brand_intelligence.router.routes}
    assert "/projects/{project_id}/brand-intelligence/identity" in paths
    assert "/projects/{project_id}/brand-intelligence/identity/import-file" in paths
    assert "/projects/{project_id}/brand-intelligence/identity/apply-proposal" in paths
    assert "/projects/{project_id}/brand-intelligence/visual-identity" in paths
    assert (
        "/projects/{project_id}/brand-intelligence/visual-identity/extract-from-website" in paths
    )
    assert (
        "/projects/{project_id}/brand-intelligence/visual-identity/apply-proposal" in paths
    )
