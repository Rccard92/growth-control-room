"""Brand Intelligence API route registration tests."""

from app.api.routes import brand_intelligence


def test_brand_intelligence_router_prefix() -> None:
    assert brand_intelligence.router.prefix == "/projects"


def test_brand_intelligence_routes_registered() -> None:
    paths = {route.path for route in brand_intelligence.router.routes}
    assert "/projects/{project_id}/brand-intelligence" in paths
    assert "/projects/{project_id}/brand-intelligence/score" in paths
    assert "/projects/{project_id}/brand-intelligence/context" in paths
    assert "/projects/{project_id}/brand-intelligence/profile" in paths
    assert "/projects/{project_id}/brand-intelligence/voice" in paths
    assert "/projects/{project_id}/brand-intelligence/products" in paths
    assert "/projects/{project_id}/brand-intelligence/audience" in paths
    assert "/projects/{project_id}/brand-intelligence/claims" in paths
    assert "/projects/{project_id}/brand-intelligence/seo-strategy" in paths
    assert "/projects/{project_id}/brand-intelligence/content-pillars" in paths
    assert "/projects/{project_id}/brand-intelligence/guardrails" in paths
    assert "/projects/{project_id}/brand-intelligence/assets" in paths
