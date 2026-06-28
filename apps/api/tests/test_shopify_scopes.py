"""Tests for Shopify OAuth scope verification."""

import os
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

from app.services.shopify.scopes import (
    REQUIRED_FOR_APPLY,
    build_scope_result,
    configured_scopes,
    parse_scope_string,
)


def test_configured_scopes_parses_env() -> None:
    with patch("app.services.shopify.scopes.settings") as mock_settings:
        mock_settings.shopify_scopes = "read_products, write_products ,read_orders"
        scopes = configured_scopes()
    assert "read_products" in scopes
    assert "write_products" in scopes
    assert "read_orders" in scopes


def test_parse_scope_string() -> None:
    assert parse_scope_string("read_products,write_products") == [
        "read_products",
        "write_products",
    ]
    assert parse_scope_string(None) == []


def test_build_scope_result_case_c_granted() -> None:
    result = build_scope_result(
        shop_domain="shop.myshopify.com",
        configured=["read_products", "write_products", "write_content"],
        granted=["read_products", "write_products", "write_content"],
    )
    assert result["can_write_products"] is True
    assert result["can_write_content"] is True
    assert result["requires_reconnect"] is False
    assert result["missing_scopes"] == []


def test_build_scope_result_case_a_token_old() -> None:
    result = build_scope_result(
        shop_domain="shop.myshopify.com",
        configured=["read_products", "write_products"],
        granted=["read_products"],
    )
    assert result["can_write_products"] is False
    assert result["requires_reconnect"] is True
    assert "write_products" in result["missing_scopes"]
    assert "Riconnetti" in result["message"]


def test_build_scope_result_case_b_not_configured() -> None:
    result = build_scope_result(
        shop_domain="shop.myshopify.com",
        configured=["read_products"],
        granted=["read_products"],
    )
    assert result["can_write_products"] is False
    assert result["requires_reconnect"] is False
    assert "SHOPIFY_SCOPES" in result["message"]


def test_build_scope_result_verify_failed() -> None:
    result = build_scope_result(
        shop_domain="shop.myshopify.com",
        configured=["write_products"],
        granted=[],
        verify_failed=True,
    )
    assert result["can_write_products"] is False
    assert "non riuscita" in result["message"]


def test_required_for_apply_constant() -> None:
    assert "write_products" in REQUIRED_FOR_APPLY


def test_shopify_scopes_response_schema() -> None:
    from app.schemas.shopify import ShopifyScopesResponse

    payload = build_scope_result(
        shop_domain="shop.myshopify.com",
        configured=["write_products"],
        granted=["write_products"],
    )
    response = ShopifyScopesResponse.model_validate(payload)
    dumped = response.model_dump(by_alias=True)
    assert dumped["canWriteProducts"] is True
    assert dumped["shopDomain"] == "shop.myshopify.com"


def test_seo_apply_response_requires_reconnect() -> None:
    from app.schemas.seo_optimizer import SeoApplyResponse

    response = SeoApplyResponse.model_validate(
        {
            "applied": False,
            "requires_scope": "write_products",
            "requires_reconnect": True,
            "message": "Il token Shopify corrente non include write_products. Riconnetti Shopify.",
        }
    )
    dumped = response.model_dump(by_alias=True)
    assert dumped["requiresReconnect"] is True
    assert dumped["applied"] is False
