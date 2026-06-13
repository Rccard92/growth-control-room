"""Diff utilities for SEO proposals — only changed fields are saved/applied."""

from typing import Any


def _normalize_scalar(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip()
    return value


def _scalars_equal(current: Any, proposed: Any) -> bool:
    return _normalize_scalar(current) == _normalize_scalar(proposed)


def _current_alt_for_image(
    image_id: str,
    current: dict[str, Any],
) -> str:
    for item in current.get("image_alts") or []:
        if not isinstance(item, dict):
            continue
        iid = str(item.get("image_id") or item.get("imageId") or "")
        if iid == image_id:
            return str(item.get("current_alt") or item.get("proposed_alt") or item.get("alt") or "")
    for image in current.get("media_images") or []:
        if not isinstance(image, dict):
            continue
        iid = str(image.get("id") or image.get("image_id") or "")
        if iid == image_id:
            return str(image.get("altText") or image.get("alt") or "")
    return ""


def _diff_image_alts(
    current: dict[str, Any],
    proposed: dict[str, Any],
) -> list[dict[str, Any]] | None:
    proposed_alts = proposed.get("image_alts") or proposed.get("imageAlts")
    if not proposed_alts:
        return None
    if not isinstance(proposed_alts, list):
        return None

    changed: list[dict[str, Any]] = []
    for entry in proposed_alts:
        if not isinstance(entry, dict):
            continue
        image_id = str(entry.get("image_id") or entry.get("imageId") or "")
        proposed_alt = str(
            entry.get("proposed_alt") or entry.get("proposedAlt") or entry.get("alt") or ""
        ).strip()
        if not image_id or not proposed_alt:
            continue
        current_alt = _current_alt_for_image(image_id, current).strip()
        if proposed_alt != current_alt:
            changed.append(
                {
                    "image_id": image_id,
                    "current_alt": current_alt,
                    "proposed_alt": proposed_alt,
                    "reason": entry.get("reason") or entry.get("reasoning") or "",
                }
            )
    return changed or None


def _diff_media_images(
    current: dict[str, Any],
    proposed: dict[str, Any],
    changed_image_alts: list[dict[str, Any]] | None,
) -> list[dict[str, Any]] | None:
    if not changed_image_alts:
        return None
    alt_by_id = {
        str(item["image_id"]): item["proposed_alt"] for item in changed_image_alts
    }
    source_media = proposed.get("media_images") or proposed.get("mediaImages")
    if not isinstance(source_media, list):
        source_media = current.get("media_images") or []

    updated: list[dict[str, Any]] = []
    for index, image in enumerate(source_media):
        if not isinstance(image, dict):
            continue
        row = dict(image)
        image_id = str(row.get("id") or row.get("image_id") or "")
        if image_id in alt_by_id:
            row["altText"] = alt_by_id[image_id]
        row.setdefault("position", index + 1)
        if image_id in alt_by_id:
            updated.append(row)
    return updated or None


def compute_changed_proposed(
    current: dict[str, Any] | None,
    proposed: dict[str, Any] | None,
) -> tuple[dict[str, Any], list[str]]:
    """Return delta proposed_values and list of changed snake_case field keys."""
    current = current or {}
    proposed = proposed or {}
    delta: dict[str, Any] = {}
    changed_fields: list[str] = []

    scalar_keys = [
        "product_title",
        "collection_title",
        "handle",
        "seo_title",
        "meta_description",
        "description_html",
        "description_text",
        "image_alt",
    ]
    for key in scalar_keys:
        if key not in proposed:
            continue
        prop_val = proposed.get(key)
        if prop_val is None:
            continue
        cur_val = current.get(key)
        if not _scalars_equal(cur_val, prop_val):
            delta[key] = prop_val
            changed_fields.append(key)

    changed_alts = _diff_image_alts(current, proposed)
    if changed_alts:
        delta["image_alts"] = changed_alts
        changed_fields.append("image_alts")
        media_delta = _diff_media_images(current, proposed, changed_alts)
        if media_delta:
            delta["media_images"] = media_delta
            if "media_images" not in changed_fields:
                changed_fields.append("media_images")

    changed_metafields = _diff_metafields(current, proposed)
    if changed_metafields:
        delta["metafields"] = changed_metafields
        changed_fields.append("metafields")

    return delta, changed_fields


def _diff_metafields(
    current: dict[str, Any],
    proposed: dict[str, Any],
) -> list[dict[str, Any]] | None:
    proposed_list = proposed.get("metafields")
    if not proposed_list or not isinstance(proposed_list, list):
        return None

    current_list = current.get("metafields") or []
    current_by_id: dict[str, dict[str, Any]] = {}
    current_by_ns_key: dict[tuple[str, str], dict[str, Any]] = {}
    for item in current_list:
        if not isinstance(item, dict):
            continue
        mid = str(item.get("id") or item.get("metafield_id") or "")
        if mid:
            current_by_id[mid] = item
        ns = str(item.get("namespace") or "")
        key = str(item.get("key") or "")
        if ns and key:
            current_by_ns_key[(ns, key)] = item

    changed: list[dict[str, Any]] = []
    for entry in proposed_list:
        if not isinstance(entry, dict):
            continue
        mid = str(entry.get("id") or entry.get("metafield_id") or "")
        namespace = str(entry.get("namespace") or "")
        key = str(entry.get("key") or "")
        type_name = str(entry.get("type") or "")
        definition_id = entry.get("definition_id") or entry.get("definitionId")
        prop_val = str(entry.get("value") or "").strip()
        if not namespace or not key or not type_name:
            continue

        cur = current_by_id.get(mid) if mid else None
        if cur is None:
            cur = current_by_ns_key.get((namespace, key))
        cur_val = str(cur.get("value") or cur.get("display_value") or "").strip() if cur else ""
        if prop_val == cur_val:
            continue
        if not prop_val:
            continue
        changed.append(
            {
                "id": mid or None,
                "metafield_id": mid or None,
                "definition_id": definition_id,
                "namespace": namespace,
                "key": key,
                "type": type_name,
                "value": prop_val,
            }
        )
    return changed or None


def proposal_changed_fields(
    current: dict[str, Any] | None,
    proposed: dict[str, Any] | None,
) -> list[str]:
    return compute_changed_proposed(current, proposed)[1]
