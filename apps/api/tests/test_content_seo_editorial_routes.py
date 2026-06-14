"""Content SEO editorial API route registration tests."""

from app.api.routes import content_seo


def test_content_seo_router_prefix() -> None:
    assert content_seo.router.prefix == "/projects"


def test_content_seo_editorial_routes_registered() -> None:
    paths = {route.path for route in content_seo.router.routes}
    assert "/projects/{project_id}/content/seo/editorial-items" in paths
    assert "/projects/{project_id}/content/seo/editorial-items/{item_id}" in paths
    assert "/projects/{project_id}/content/seo/editorial-plan/generate-calendar" in paths
    assert (
        "/projects/{project_id}/content/seo/editorial-items/{item_id}/generate-brief" in paths
    )
    assert "/projects/{project_id}/content/seo/editorial-items/{item_id}/brief" in paths
    assert (
        "/projects/{project_id}/content/seo/editorial-items/{item_id}/reschedule" in paths
    )
