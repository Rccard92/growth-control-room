def parse_products_count(node: dict) -> int | None:
    raw = node.get("productsCount")
    if isinstance(raw, dict):
        return raw.get("count")
    return raw


def test_parse_products_count_object() -> None:
    assert parse_products_count({"productsCount": {"count": 12}}) == 12


def test_parse_products_count_scalar() -> None:
    assert parse_products_count({"productsCount": 5}) == 5


def test_parse_products_count_missing() -> None:
    assert parse_products_count({}) is None
