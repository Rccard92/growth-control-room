"""FAQ & Objections API route registration tests."""

from app.api.routes import brand_intelligence


def test_faq_objections_routes_registered() -> None:
    paths = {route.path for route in brand_intelligence.router.routes}
    assert "/projects/{project_id}/brand-intelligence/faq-objections" in paths
    assert "/projects/{project_id}/brand-intelligence/faq-objections/import-file" in paths
    assert "/projects/{project_id}/brand-intelligence/faq-objections/apply-proposal" in paths
