"""Safe Claims API route registration tests."""

from app.api.routes import brand_intelligence


def test_safe_claims_routes_registered() -> None:
    paths = {route.path for route in brand_intelligence.router.routes}
    assert "/projects/{project_id}/brand-intelligence/safe-claims" in paths
    assert "/projects/{project_id}/brand-intelligence/safe-claims/import-file" in paths
    assert "/projects/{project_id}/brand-intelligence/safe-claims/apply-proposal" in paths
