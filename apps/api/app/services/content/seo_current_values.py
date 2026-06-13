from typing import Any

from app.models.content_seo import ShopifyCollection
from app.models.shopify import ShopifyProduct
from app.services.shopify.html_utils import html_to_text

# CamelCase keys for API detail responses (currentValues)
PRODUCT_API_KEYS = {
    "title",
    "handle",
    "seoTitle",
    "metaDescription",
    "descriptionHtml",
    "descriptionText",
    "productType",
    "vendor",
    "images",
}

COLLECTION_API_KEYS = {
    "title",
    "handle",
    "seoTitle",
    "metaDescription",
    "descriptionHtml",
    "descriptionText",
    "imageAlt",
}

# Snake_case keys for internal proposals
_PRODUCT_CAMEL_TO_SNAKE: dict[str, str] = {
    "title": "product_title",
    "productTitle": "product_title",
    "product_title": "product_title",
    "handle": "handle",
    "seoTitle": "seo_title",
    "seo_title": "seo_title",
    "metaDescription": "meta_description",
    "meta_description": "meta_description",
    "descriptionHtml": "description_html",
    "description_html": "description_html",
    "descriptionText": "description_text",
    "description_text": "description_text",
    "productType": "product_type",
    "product_type": "product_type",
    "vendor": "vendor",
    "images": "media_images",
    "mediaImages": "media_images",
    "media_images": "media_images",
    "imageAlts": "image_alts",
    "image_alts": "image_alts",
}

_COLLECTION_CAMEL_TO_SNAKE: dict[str, str] = {
    "title": "collection_title",
    "collectionTitle": "collection_title",
    "collection_title": "collection_title",
    "handle": "handle",
    "seoTitle": "seo_title",
    "seo_title": "seo_title",
    "metaDescription": "meta_description",
    "meta_description": "meta_description",
    "descriptionHtml": "description_html",
    "description_html": "description_html",
    "descriptionText": "description_text",
    "description_text": "description_text",
    "imageAlt": "image_alt",
    "image_alt": "image_alt",
}

_PRODUCT_EXTRA_KEYS = {"image_alts"}


def _normalize_media_for_api(media: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for index, item in enumerate(media or []):
        result.append(
            {
                "id": item.get("id"),
                "url": item.get("url"),
                "altText": item.get("altText") or item.get("alt"),
                "position": item.get("position") or index + 1,
            }
        )
    return result


def _resolve_product_description(product: ShopifyProduct) -> tuple[str | None, str | None]:
    html = product.description_html
    text = product.description_text
    if html or text:
        return html, text
    raw = product.raw_payload if isinstance(product.raw_payload, dict) else {}
    html = raw.get("descriptionHtml")
    if isinstance(html, str) and html.strip():
        return html, html_to_text(html)
    return None, None


def product_api_current_values(
    product: ShopifyProduct,
    *,
    images: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    media = images if images is not None else (product.media_images or [])
    if not media and product.featured_image_url:
        media = [{"url": product.featured_image_url, "altText": None, "position": 1}]
    desc_html, desc_text = _resolve_product_description(product)
    return {
        "title": product.title,
        "handle": product.handle,
        "seoTitle": product.seo_title,
        "metaDescription": product.seo_description,
        "descriptionHtml": desc_html,
        "descriptionText": desc_text,
        "productType": product.product_type,
        "vendor": product.vendor,
        "images": _normalize_media_for_api(media),
    }


def collection_api_current_values(collection: ShopifyCollection) -> dict[str, Any]:
    html = collection.description_html
    text = collection.description_text
    if not html and not text:
        raw = collection.raw_payload if isinstance(collection.raw_payload, dict) else {}
        html = raw.get("descriptionHtml") or raw.get("description")
        if isinstance(html, str) and html.strip():
            text = html_to_text(html)
    return {
        "title": collection.title,
        "handle": collection.handle,
        "seoTitle": collection.seo_title,
        "metaDescription": collection.seo_description,
        "descriptionHtml": html,
        "descriptionText": text,
        "imageAlt": collection.image_alt,
    }


def normalize_proposal_values(
    entity_type: str,
    values: dict[str, Any],
) -> dict[str, Any]:
    """Convert camelCase or mixed keys from API/AI to snake_case proposal keys."""
    mapping = _PRODUCT_CAMEL_TO_SNAKE if entity_type == "product" else _COLLECTION_CAMEL_TO_SNAKE
    allowed_snake = (
        set(_PRODUCT_CAMEL_TO_SNAKE.values()) | _PRODUCT_EXTRA_KEYS
        if entity_type == "product"
        else set(_COLLECTION_CAMEL_TO_SNAKE.values())
    )
    result: dict[str, Any] = {}
    for key, val in values.items():
        if key in ("reasoning", "risk_level", "riskLevel"):
            continue
        snake = mapping.get(key, key if key in allowed_snake else None)
        if snake and snake in allowed_snake:
            result[snake] = val
    return result
