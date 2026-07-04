"""Tests for Growth Audit URL utilities."""

from __future__ import annotations

import pytest

from app.services.growth_audit.exceptions import GrowthAuditValidationError
from app.services.growth_audit.url_utils import (
    extract_domain,
    get_url_path,
    is_excluded_audit_url,
    normalize_root_url,
    normalize_url,
)


def test_normalize_root_url_strips_trailing_slash() -> None:
    assert normalize_root_url("https://Example.com/shop/") == "https://example.com/shop"


def test_normalize_url_preserves_path() -> None:
    assert normalize_url("https://example.com/products/foo") == "https://example.com/products/foo"


def test_extract_domain() -> None:
    assert extract_domain("https://shop.example.com/page") == "shop.example.com"


def test_get_url_path_homepage() -> None:
    assert get_url_path("https://example.com") == "/"
    assert get_url_path("https://example.com/") == "/"


def test_reject_file_scheme() -> None:
    with pytest.raises(GrowthAuditValidationError):
        normalize_root_url("file:///etc/passwd")


def test_reject_localhost() -> None:
    with pytest.raises(GrowthAuditValidationError):
        normalize_root_url("http://localhost/")


def test_is_excluded_audit_url_cart() -> None:
    assert is_excluded_audit_url("https://example.com/cart") is True


def test_is_excluded_audit_url_static_asset() -> None:
    assert is_excluded_audit_url("https://example.com/assets/app.js") is True
    assert is_excluded_audit_url("https://example.com/image.jpg") is True


def test_is_excluded_audit_url_product_allowed() -> None:
    assert is_excluded_audit_url("https://example.com/products/foo") is False
