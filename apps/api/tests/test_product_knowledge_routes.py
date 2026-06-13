"""Product Knowledge API route registration tests."""

from app.api.routes import brand_intelligence


def test_product_knowledge_routes_registered() -> None:
    paths = {route.path for route in brand_intelligence.router.routes}
    assert "/projects/{project_id}/brand-intelligence/product-knowledge/general" in paths
    assert (
        "/projects/{project_id}/brand-intelligence/product-knowledge/general/import-file" in paths
    )
    assert (
        "/projects/{project_id}/brand-intelligence/product-knowledge/general/apply-proposal"
        in paths
    )
    assert "/projects/{project_id}/brand-intelligence/product-knowledge/shopify-products" in paths
    assert "/projects/{project_id}/brand-intelligence/product-knowledge/items" in paths
    assert (
        "/projects/{project_id}/brand-intelligence/product-knowledge/items/from-shopify" in paths
    )
    assert (
        "/projects/{project_id}/brand-intelligence/product-knowledge/items/{item_id}" in paths
    )
