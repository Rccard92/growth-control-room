"""Merchant Center product matching to Growth Audit Shopify product pages."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from app.models.growth_audit import GrowthAuditPage
from app.services.growth_audit.ga4_item_product_matching import _extract_shopify_legacy_id
from app.services.growth_audit.url_utils import normalize_url

_SHOPIFY_COMPOSITE_ITEM_ID_RE = re.compile(
    r"^shopify_([A-Za-z]{2})_(\d+)_(\d+)$",
    re.IGNORECASE,
)
_PRODUCT_HANDLE_RE = re.compile(r"/products/([^/?#]+)", re.IGNORECASE)


@dataclass
class MerchantPageMatchProfile:
    page_id: UUID
    normalized_urls: set[str] = field(default_factory=set)
    handle: str | None = None
    product_legacy_id: str | None = None
    variant_legacy_ids: set[str] = field(default_factory=set)
    skus: set[str] = field(default_factory=set)


@dataclass
class MerchantMatchResult:
    page_id: UUID
    product: dict[str, Any]
    matched_by: str


def _safe_normalize_url(url: str | None) -> str | None:
    if not url or not isinstance(url, str):
        return None
    try:
        return normalize_url(url.strip())
    except Exception:
        return None


def _extract_handle_from_url(url: str | None) -> str | None:
    if not url:
        return None
    match = _PRODUCT_HANDLE_RE.search(url)
    return match.group(1).lower() if match else None


def build_merchant_page_match_profiles(pages: list[GrowthAuditPage]) -> list[MerchantPageMatchProfile]:
    profiles: list[MerchantPageMatchProfile] = []
    for page in pages:
        normalized_urls: set[str] = set()
        for candidate in (page.normalized_url, page.url, page.canonical_url):
            normalized = _safe_normalize_url(candidate)
            if normalized:
                normalized_urls.add(normalized)

        handle = (page.source_entity_handle or "").strip().lower() or None
        if not handle:
            for candidate in (page.url, page.canonical_url):
                handle = _extract_handle_from_url(candidate)
                if handle:
                    break

        product_legacy_id = _extract_shopify_legacy_id(page.source_entity_gid)
        variant_legacy_ids: set[str] = set()
        skus: set[str] = set()

        shopify_meta = (page.page_metadata or {}).get("shopifyCommerce")
        if isinstance(shopify_meta, dict):
            pass

        ga4_meta = (page.page_metadata or {}).get("ga4Ecommerce")
        if isinstance(ga4_meta, dict):
            for variant in ga4_meta.get("variantBreakdown") or []:
                if not isinstance(variant, dict):
                    continue
                variant_id = variant.get("variantLegacyId")
                if isinstance(variant_id, str) and variant_id.strip():
                    variant_legacy_ids.add(variant_id.strip())
                sku = variant.get("sku")
                if isinstance(sku, str) and sku.strip():
                    skus.add(sku.strip().lower())

        profiles.append(
            MerchantPageMatchProfile(
                page_id=page.id,
                normalized_urls=normalized_urls,
                handle=handle,
                product_legacy_id=product_legacy_id,
                variant_legacy_ids=variant_legacy_ids,
                skus=skus,
            )
        )
    return profiles


def _match_by_link(
    product: dict[str, Any],
    profiles: list[MerchantPageMatchProfile],
) -> MerchantMatchResult | None:
    link = _safe_normalize_url(product.get("link"))
    if not link:
        return None
    matches = [profile for profile in profiles if link in profile.normalized_urls]
    if len(matches) == 1:
        return MerchantMatchResult(
            page_id=matches[0].page_id,
            product=product,
            matched_by="link",
        )
    return None


def _match_by_handle(
    product: dict[str, Any],
    profiles: list[MerchantPageMatchProfile],
) -> MerchantMatchResult | None:
    handle = _extract_handle_from_url(product.get("link"))
    if not handle:
        return None
    matches = [profile for profile in profiles if profile.handle and profile.handle == handle]
    if len(matches) == 1:
        return MerchantMatchResult(
            page_id=matches[0].page_id,
            product=product,
            matched_by="handle",
        )
    return None


def _match_by_offer_id(
    product: dict[str, Any],
    profiles: list[MerchantPageMatchProfile],
) -> MerchantMatchResult | None:
    offer_id = str(product.get("offerId") or "").strip()
    if not offer_id:
        return None

    parsed = _SHOPIFY_COMPOSITE_ITEM_ID_RE.match(offer_id)
    if parsed:
        product_legacy_id = parsed.group(2)
        variant_legacy_id = parsed.group(3)
        matches = [
            profile
            for profile in profiles
            if profile.product_legacy_id == product_legacy_id
            and (
                not profile.variant_legacy_ids
                or variant_legacy_id in profile.variant_legacy_ids
            )
        ]
        if len(matches) == 1:
            return MerchantMatchResult(
                page_id=matches[0].page_id,
                product=product,
                matched_by="offer_id",
            )
        return None

    matches: list[MerchantPageMatchProfile] = []
    for profile in profiles:
        if offer_id == profile.product_legacy_id:
            matches.append(profile)
            continue
        if offer_id in profile.variant_legacy_ids:
            matches.append(profile)

    if len(matches) == 1:
        return MerchantMatchResult(
            page_id=matches[0].page_id,
            product=product,
            matched_by="offer_id",
        )
    return None


def _match_by_gtin_or_sku(
    product: dict[str, Any],
    profiles: list[MerchantPageMatchProfile],
) -> MerchantMatchResult | None:
    gtin = str(product.get("gtin") or "").strip().lower()
    mpn = str(product.get("mpn") or "").strip().lower()
    candidates = [value for value in (gtin, mpn) if value]
    if not candidates:
        return None

    matches: list[MerchantPageMatchProfile] = []
    for profile in profiles:
        if not profile.skus:
            continue
        if any(candidate in profile.skus for candidate in candidates):
            matches.append(profile)

    if len(matches) == 1:
        return MerchantMatchResult(
            page_id=matches[0].page_id,
            product=product,
            matched_by="sku",
        )
    return None


def match_merchant_products_to_pages(
    pages: list[GrowthAuditPage],
    merchant_products: list[dict[str, Any]],
) -> tuple[dict[UUID, MerchantMatchResult], list[dict[str, Any]]]:
    profiles = build_merchant_page_match_profiles(pages)
    matched_by_page: dict[UUID, MerchantMatchResult] = {}
    unmatched_products: list[dict[str, Any]] = []

    matchers = (
        _match_by_link,
        _match_by_handle,
        _match_by_offer_id,
        _match_by_gtin_or_sku,
    )

    for product in merchant_products:
        result: MerchantMatchResult | None = None
        for matcher in matchers:
            candidate = matcher(product, profiles)
            if candidate is not None:
                result = candidate
                break

        if result is None:
            unmatched_products.append(product)
            continue

        existing = matched_by_page.get(result.page_id)
        if existing is not None:
            unmatched_products.append(product)
            continue

        matched_by_page[result.page_id] = result

    return matched_by_page, unmatched_products
