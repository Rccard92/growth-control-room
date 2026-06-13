"""CamelCase API field keys ↔ snake_case internal proposal keys."""

from __future__ import annotations

from typing import Any

PRODUCT_TITLE_SNAKE = "product_title"
COLLECTION_TITLE_SNAKE = "collection_title"

API_TO_SNAKE_PRODUCT: dict[str, str] = {
    "title": PRODUCT_TITLE_SNAKE,
    "handle": "handle",
    "seoTitle": "seo_title",
    "metaDescription": "meta_description",
    "descriptionHtml": "description_html",
    "imageAlts": "image_alts",
    "metafields": "metafields",
}

API_TO_SNAKE_COLLECTION: dict[str, str] = {
    "title": COLLECTION_TITLE_SNAKE,
    "handle": "handle",
    "seoTitle": "seo_title",
    "metaDescription": "meta_description",
    "descriptionHtml": "description_html",
    "imageAlt": "image_alt",
}

SNAKE_TO_API_PRODUCT: dict[str, str] = {v: k for k, v in API_TO_SNAKE_PRODUCT.items()}
SNAKE_TO_API_COLLECTION: dict[str, str] = {v: k for k, v in API_TO_SNAKE_COLLECTION.items()}


def api_to_snake_map(entity_type: str) -> dict[str, str]:
    if entity_type == "product":
        return API_TO_SNAKE_PRODUCT
    if entity_type == "collection":
        return API_TO_SNAKE_COLLECTION
    raise ValueError(f"entity_type non supportato: {entity_type}")


def normalize_api_fields_to_snake(
    entity_type: str,
    fields: dict[str, Any] | None,
) -> dict[str, Any]:
    if not fields:
        return {}
    mapping = api_to_snake_map(entity_type)
    normalized: dict[str, Any] = {}
    for api_key, value in fields.items():
        snake = mapping.get(api_key)
        if snake is None:
            continue
        if api_key == "imageAlts" and entity_type == "product":
            normalized["image_alts"] = value
            if "mediaImages" in fields:
                normalized["media_images"] = fields["mediaImages"]
            continue
        normalized[snake] = value
    return normalized


def whitelist_changed_fields(
    entity_type: str,
    changed_fields: list[str] | None,
) -> set[str]:
    if not changed_fields:
        return set()
    mapping = api_to_snake_map(entity_type)
    snake_values = set(mapping.values())
    allowed: set[str] = set()
    for key in changed_fields:
        snake = mapping.get(key)
        if snake:
            allowed.add(snake)
        elif key in snake_values:
            allowed.add(key)
        if key == "imageAlts" and entity_type == "product":
            allowed.add("image_alts")
            allowed.add("media_images")
        if key == "image_alts":
            allowed.add("image_alts")
            allowed.add("media_images")
    return allowed


def filter_proposed_by_whitelist(
    proposed_snake: dict[str, Any],
    whitelist: set[str],
) -> dict[str, Any]:
    if not whitelist:
        return {}
    filtered: dict[str, Any] = {}
    for key, value in proposed_snake.items():
        if key not in whitelist:
            continue
        if key == "media_images" and "image_alts" in whitelist:
            filtered[key] = value
            continue
        filtered[key] = value
    return filtered


def api_labels_for_snake_fields(entity_type: str, snake_fields: list[str]) -> list[str]:
    labels = {
        "product_title": "Titolo",
        "collection_title": "Titolo",
        "handle": "Handle URL",
        "seo_title": "SEO title",
        "meta_description": "Meta description",
        "description_html": "Descrizione",
        "image_alts": "Alt immagini",
        "image_alt": "Alt immagine",
        "metafields": "Metafield",
    }
    reverse = (
        SNAKE_TO_API_PRODUCT if entity_type == "product" else SNAKE_TO_API_COLLECTION
    )
    return [labels.get(f, reverse.get(f, f)) for f in snake_fields]
