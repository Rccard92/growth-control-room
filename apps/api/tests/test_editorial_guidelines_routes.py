"""Editorial guidelines route registration tests."""

from app.api.routes import brand_intelligence


def test_editorial_guidelines_routes_registered() -> None:
    paths = {route.path for route in brand_intelligence.router.routes}
    assert "/projects/{project_id}/brand-intelligence/editorial-guidelines" in paths
