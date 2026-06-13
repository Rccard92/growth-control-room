import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

from app.services.content.seo_apply_shopify import build_product_update_input


def test_product_update_only_meta_description() -> None:
    delta = {"meta_description": "Nuova meta description SEO"}
    input_data = build_product_update_input("gid://shopify/Product/1", delta)
    assert input_data is not None
    assert input_data["id"] == "gid://shopify/Product/1"
    assert "title" not in input_data
    assert "handle" not in input_data
    assert "descriptionHtml" not in input_data
    assert input_data["seo"] == {"description": "Nuova meta description SEO"}
    assert "title" not in input_data["seo"]


def test_product_update_only_seo_title() -> None:
    delta = {"seo_title": "SEO title ottimizzato"}
    input_data = build_product_update_input("gid://shopify/Product/1", delta)
    assert input_data is not None
    assert input_data["seo"] == {"title": "SEO title ottimizzato"}
    assert "description" not in input_data["seo"]
