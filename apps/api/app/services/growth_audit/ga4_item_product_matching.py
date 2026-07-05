"""GA4 item-level row matching to Growth Audit Shopify product pages."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from app.models.growth_audit import GrowthAuditPage

MATCH_PRIORITY = (
    "shopify_composite_item_id",
    "item_id",
    "variant_id",
    "sku",
    "item_name",
)

_SHOPIFY_COMPOSITE_ITEM_ID_RE = re.compile(
    r"^shopify_([A-Za-z]{2})_(\d+)_(\d+)$",
    re.IGNORECASE,
)


def _normalize_match_text(value: str | None) -> str:
    if not value:
        return ""
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    collapsed = re.sub(r"\s+", " ", ascii_text.lower().strip())
    return collapsed


def _extract_shopify_legacy_id(gid: str | None) -> str | None:
    if not gid:
        return None
    match = re.search(r"/(\d+)$", gid.strip())
    return match.group(1) if match else None


def _parse_shopify_composite_item_id(item_id: str) -> dict[str, str] | None:
    normalized = (item_id or "").strip()
    if not normalized:
        return None
    match = _SHOPIFY_COMPOSITE_ITEM_ID_RE.match(normalized)
    if not match:
        return None
    return {
        "productLegacyId": match.group(2),
        "variantLegacyId": match.group(3),
    }


def _profile_matches_composite_item_id(
    profile: ProductMatchProfile,
    parsed: dict[str, str],
) -> bool:
    product_legacy_id = parsed.get("productLegacyId")
    variant_legacy_id = parsed.get("variantLegacyId")
    if product_legacy_id and profile.product_legacy_id == product_legacy_id:
        return True
    if variant_legacy_id and variant_legacy_id in profile.variant_legacy_ids:
        return True
    return False


@dataclass
class ProductMatchProfile:
    page_id: UUID
    product_gid: str
    product_legacy_id: str | None = None
    variant_legacy_ids: set[str] = field(default_factory=set)
    skus: set[str] = field(default_factory=set)
    title_normalized: str = ""
    handle_normalized: str = ""

    def to_shopify_keys_dict(self) -> dict[str, Any]:
        return {
            "productGid": self.product_gid,
            "productLegacyId": self.product_legacy_id,
            "variantLegacyIds": sorted(self.variant_legacy_ids),
            "skus": sorted(self.skus),
            "titleNormalized": self.title_normalized,
            "handleNormalized": self.handle_normalized,
        }


def _ga4_row_key(row: dict[str, Any]) -> str:
    item_id = str(row.get("itemId") or "").strip()
    item_name = str(row.get("itemName") or "").strip()
    item_variant = str(row.get("itemVariant") or "").strip()
    return f"{item_id}|{item_name}|{item_variant}"


def _candidate_row_dict(row: dict[str, Any], *, candidate_reason: str) -> dict[str, Any]:
    return {
        "itemId": str(row.get("itemId") or ""),
        "itemName": str(row.get("itemName") or ""),
        "itemVariant": str(row.get("itemVariant") or ""),
        "itemsViewed": int(row.get("itemsViewed") or row.get("itemViewEvents") or 0),
        "itemsAddedToCart": int(row.get("itemsAddedToCart") or 0),
        "itemsPurchased": int(row.get("itemsPurchased") or 0),
        "itemRevenue": round(float(row.get("itemRevenue") or 0), 2),
        "candidateReason": candidate_reason,
    }


def _weak_candidate_reason(
    profile: ProductMatchProfile,
    *,
    item_id: str,
    item_name: str,
) -> str | None:
    normalized_item_name = _normalize_match_text(item_name)
    if not normalized_item_name or normalized_item_name == "(not set)":
        normalized_item_name = ""

    if profile.title_normalized and normalized_item_name:
        if (
            profile.title_normalized in normalized_item_name
            or normalized_item_name in profile.title_normalized
        ) and profile.title_normalized != normalized_item_name:
            return "Nome simile ma non identico: non assegnato automaticamente."

    if profile.handle_normalized and normalized_item_name:
        if profile.handle_normalized in normalized_item_name:
            return "Handle Shopify presente nel nome item GA4: non assegnato automaticamente."

    item_id_lower = item_id.strip().lower()
    if item_id_lower:
        for sku in profile.skus:
            if sku and (sku in item_id_lower or item_id_lower in sku) and sku != item_id_lower:
                return "SKU parzialmente simile: non assegnato automaticamente."

    return None


def find_potential_unmatched_candidates_for_profile(
    profile: ProductMatchProfile,
    rows: list[dict[str, Any]],
    *,
    limit: int = 5,
    assigned_row_keys: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Suggest GA4 rows to inspect manually. Never used for metric assignment."""
    assigned = assigned_row_keys or set()
    candidates: list[tuple[int, dict[str, Any]]] = []

    for row in rows:
        row_key = _ga4_row_key(row)
        if row_key in assigned:
            continue

        item_id = str(row.get("itemId") or "")
        item_name = str(row.get("itemName") or "")

        id_matches = _find_profiles_by_item_id([profile], item_id)
        if len(id_matches) == 1:
            continue
        name_matches = _find_profiles_by_item_name([profile], item_name)
        if len(name_matches) == 1:
            continue

        candidate_reason = _weak_candidate_reason(
            profile,
            item_id=item_id,
            item_name=item_name,
        )
        if not candidate_reason:
            continue

        item_views = int(row.get("itemsViewed") or row.get("itemViewEvents") or 0)
        candidates.append(
            (
                item_views,
                _candidate_row_dict(row, candidate_reason=candidate_reason),
            )
        )

    candidates.sort(key=lambda item: item[0], reverse=True)
    return [item[1] for item in candidates[:limit]]


def build_page_match_debug(
    profile: ProductMatchProfile,
    *,
    aggregate: dict[str, Any] | None,
    rows: list[dict[str, Any]],
    assigned_row_keys: set[str] | None = None,
) -> dict[str, Any]:
    shopify_keys = profile.to_shopify_keys_dict()
    matched_by = (aggregate or {}).get("matchedBy")

    if aggregate and matched_by and matched_by != "none":
        if matched_by == "shopify_composite_item_id":
            reason = (
                "Prodotto abbinato tramite itemId Shopify composto: "
                "product legacy id e/o variant id coincidono."
            )
        else:
            reason = f"Prodotto abbinato tramite {matched_by}."
        return {
            "shopifyKeys": shopify_keys,
            "matchedBy": matched_by,
            "matchStatus": "matched",
            "reason": reason,
            "candidateItems": [],
        }

    return {
        "shopifyKeys": shopify_keys,
        "matchedBy": "none",
        "matchStatus": "no_reliable_match",
        "reason": (
            "Nessuna riga GA4 ha itemId/SKU/title uguale alle chiavi Shopify del prodotto."
        ),
        "candidateItems": find_potential_unmatched_candidates_for_profile(
            profile,
            rows,
            assigned_row_keys=assigned_row_keys,
        ),
    }


def build_assigned_row_keys(
    profiles: list[ProductMatchProfile],
    rows: list[dict[str, Any]],
) -> set[str]:
    """Row keys that received a strict unique match to any product page."""
    assigned: set[str] = set()
    for row in rows:
        item_id = str(row.get("itemId") or "")
        item_name = str(row.get("itemName") or "")

        id_matches = _find_profiles_by_item_id(profiles, item_id)
        if len(id_matches) == 1:
            assigned.add(_ga4_row_key(row))
            continue

        name_matches = _find_profiles_by_item_name(profiles, item_name)
        if len(name_matches) == 1:
            assigned.add(_ga4_row_key(row))

    return assigned


def build_product_match_profiles(
    pages: list[GrowthAuditPage],
    *,
    variant_data_by_gid: dict[str, dict[str, Any]] | None = None,
) -> list[ProductMatchProfile]:
    profiles: list[ProductMatchProfile] = []
    variant_data_by_gid = variant_data_by_gid or {}

    for page in pages:
        product_gid = (page.source_entity_gid or "").strip()
        if not product_gid:
            continue

        title = page.source_entity_title or page.title or ""
        handle = page.source_entity_handle or ""
        profile = ProductMatchProfile(
            page_id=page.id,
            product_gid=product_gid,
            product_legacy_id=_extract_shopify_legacy_id(product_gid),
            title_normalized=_normalize_match_text(title),
            handle_normalized=_normalize_match_text(handle),
        )

        variant_info = variant_data_by_gid.get(product_gid) or {}
        for variant_id in variant_info.get("variantLegacyIds") or []:
            if variant_id:
                profile.variant_legacy_ids.add(str(variant_id))
        for sku in variant_info.get("skus") or []:
            if sku:
                profile.skus.add(str(sku).strip().lower())

        profiles.append(profile)

    return profiles


def _find_profiles_by_item_id(
    profiles: list[ProductMatchProfile],
    item_id: str,
) -> list[ProductMatchProfile]:
    normalized_item_id = item_id.strip()
    if not normalized_item_id or normalized_item_id == "(not set)":
        return []

    parsed_composite = _parse_shopify_composite_item_id(normalized_item_id)
    if parsed_composite:
        composite_matches: list[ProductMatchProfile] = []
        seen_page_ids: set[UUID] = set()
        for profile in profiles:
            if profile.page_id in seen_page_ids:
                continue
            if _profile_matches_composite_item_id(profile, parsed_composite):
                composite_matches.append(profile)
                seen_page_ids.add(profile.page_id)
        if composite_matches:
            return composite_matches

    matches: list[ProductMatchProfile] = []
    item_id_lower = normalized_item_id.lower()

    for profile in profiles:
        if profile.product_legacy_id and profile.product_legacy_id == normalized_item_id:
            matches.append(profile)
            continue
        if normalized_item_id in profile.variant_legacy_ids:
            matches.append(profile)
            continue
        if item_id_lower in profile.skus:
            matches.append(profile)

    return matches


def _find_profiles_by_item_name(
    profiles: list[ProductMatchProfile],
    item_name: str,
) -> list[ProductMatchProfile]:
    normalized_name = _normalize_match_text(item_name)
    if not normalized_name or normalized_name == "(not set)":
        return []

    matches: list[ProductMatchProfile] = []
    for profile in profiles:
        if profile.title_normalized and profile.title_normalized == normalized_name:
            matches.append(profile)
        elif profile.handle_normalized and profile.handle_normalized == normalized_name:
            matches.append(profile)
    return matches


def _resolve_match_type(
    profile: ProductMatchProfile,
    *,
    item_id: str,
    item_name: str,
) -> str | None:
    normalized_item_id = item_id.strip()
    item_id_lower = normalized_item_id.lower()

    parsed_composite = _parse_shopify_composite_item_id(normalized_item_id)
    if parsed_composite and _profile_matches_composite_item_id(profile, parsed_composite):
        return "shopify_composite_item_id"

    if profile.product_legacy_id and profile.product_legacy_id == normalized_item_id:
        return "item_id"
    if normalized_item_id in profile.variant_legacy_ids:
        return "variant_id"
    if item_id_lower in profile.skus:
        return "sku"

    normalized_name = _normalize_match_text(item_name)
    if normalized_name and (
        profile.title_normalized == normalized_name
        or profile.handle_normalized == normalized_name
    ):
        return "item_name"
    return None


def match_ga4_rows_to_pages(
    profiles: list[ProductMatchProfile],
    rows: list[dict[str, Any]],
) -> tuple[dict[UUID, dict[str, Any]], int, int]:
    """Match GA4 item rows to product pages.

    Returns page aggregates, unmatched count, and ambiguous match count.
    """
    page_aggregates: dict[UUID, dict[str, Any]] = {}
    unmatched_items = 0
    ambiguous_items = 0

    for row in rows:
        item_id = str(row.get("itemId") or "")
        item_name = str(row.get("itemName") or "")
        item_variant = str(row.get("itemVariant") or "")

        item_views = int(row.get("itemsViewed") or row.get("itemViewEvents") or 0)
        item_view_events = int(row.get("itemViewEvents") or 0)
        items_added_to_cart = int(row.get("itemsAddedToCart") or 0)
        items_checked_out = int(row.get("itemsCheckedOut") or 0)
        items_purchased = int(row.get("itemsPurchased") or 0)
        item_revenue = float(row.get("itemRevenue") or 0)

        id_matches = _find_profiles_by_item_id(profiles, item_id)
        if len(id_matches) == 1:
            matched_profiles = id_matches
            matched_by = _resolve_match_type(
                id_matches[0],
                item_id=item_id,
                item_name=item_name,
            ) or "item_id"
        elif len(id_matches) > 1:
            unmatched_items += 1
            ambiguous_items += 1
            continue
        else:
            name_matches = _find_profiles_by_item_name(profiles, item_name)
            if len(name_matches) == 1:
                matched_profiles = name_matches
                matched_by = "item_name"
            elif len(name_matches) > 1:
                unmatched_items += 1
                ambiguous_items += 1
                continue
            else:
                unmatched_items += 1
                continue

        for profile in matched_profiles:
            bucket = page_aggregates.setdefault(
                profile.page_id,
                {
                    "itemViews": 0,
                    "itemViewEvents": 0,
                    "itemsAddedToCart": 0,
                    "itemsCheckedOut": 0,
                    "itemsPurchased": 0,
                    "itemRevenue": 0.0,
                    "matchedBy": matched_by,
                    "matchedItemIds": set(),
                    "matchedItemNames": set(),
                    "matchedVariants": set(),
                },
            )
            bucket["itemViews"] += item_views
            bucket["itemViewEvents"] += item_view_events
            bucket["itemsAddedToCart"] += items_added_to_cart
            bucket["itemsCheckedOut"] += items_checked_out
            bucket["itemsPurchased"] += items_purchased
            bucket["itemRevenue"] += item_revenue
            if item_id and item_id != "(not set)":
                bucket["matchedItemIds"].add(item_id)
            if item_name and item_name != "(not set)":
                bucket["matchedItemNames"].add(item_name)
            if item_variant and item_variant != "(not set)":
                bucket["matchedVariants"].add(item_variant)

    return page_aggregates, unmatched_items, ambiguous_items
