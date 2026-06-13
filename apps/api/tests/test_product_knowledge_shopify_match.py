"""Shopify matching for Product Knowledge item import."""

from types import SimpleNamespace

from app.services.brand_intelligence.product_knowledge_shopify_match import (
    normalize_product_label,
    score_name_to_product,
    score_shopify_match,
)


def _product(title: str, handle: str) -> SimpleNamespace:
    return SimpleNamespace(title=title, handle=handle)


def test_normalize_product_label_strips_prefix() -> None:
    assert normalize_product_label("MIELE DI LIMONE") == "limone"
    assert normalize_product_label("Miele di Limone") == "limone"


def test_score_exact_title_match() -> None:
    product = _product("Miele di Limone", "miele-limone")
    assert score_shopify_match("Miele di Limone", product) == 1.0  # type: ignore[arg-type]


def test_score_containment_match() -> None:
    product = _product("Miele di Limone Bio 250g", "miele-limone-bio")
    score = score_shopify_match("MIELE DI LIMONE", product)  # type: ignore[arg-type]
    assert score >= 0.85


def test_score_polline_pappa_reale() -> None:
    polline = _product("Polline d'Api", "polline-api")
    assert score_name_to_product("POLLINE", polline.title, polline.handle) >= 0.75

    pappa = _product("Pappa Reale Fresca", "pappa-reale-fresca")
    assert score_name_to_product("PAPPA REALE", pappa.title, pappa.handle) >= 0.75


def test_score_no_match_returns_zero() -> None:
    product = _product("Candela Profumata", "candela")
    assert score_shopify_match("Miele di Limone", product) == 0.0  # type: ignore[arg-type]
