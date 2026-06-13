import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

from app.services.shopify.content_sync import parse_products_count


def test_parse_products_count_object() -> None:
    assert parse_products_count({"productsCount": {"count": 12}}) == 12


def test_parse_products_count_scalar() -> None:
    assert parse_products_count({"productsCount": 5}) == 5


def test_parse_products_count_missing() -> None:
    assert parse_products_count({}) is None
