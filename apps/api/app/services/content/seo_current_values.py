from typing import Any

from app.models.content_seo import ShopifyCollection
from app.models.shopify import ShopifyProduct

# CamelCase keys for API detail responses (currentValues)
PRODUCT_API_KEYS = {
    "title",
    "handle",
    "seoTitle",
    "metaDescription",
    "descriptionHtml",
    "descriptionText",
    "tags",
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
    "tags": "tags",
    "productType": "product_type",
    "product_type": "product_type",
    "vendor": "vendor",
    "images": "media_images",
    "mediaImages": "media_images",
    "media_images": "media_images",
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


def product_api_current_values(
    product: ShopifyProduct,
    *,
    images: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    media = images if images is not None else (product.media_images or [])
    if not media and product.featured_image_url:
        media = [{"url": product.featured_image_url, "altText": None}]
    return {
        "title": product.title or "",
        "handle": product.handle or "",
        "seoTitle": product.seo_title or "",
        "metaDescription": product.seo_description or "",
        "descriptionHtml": product.description_html or "",
        "descriptionText": product.description_text or "",
        "tags": product.tags or [],
        "productType": product.product_type or "",
        "vendor": product.vendor or "",
        "images": media,
    }


def collection_api_current_values(collection: ShopifyCollection) -> dict[str, Any]:
    return {
        "title": collection.title or "",
        "handle": collection.handle or "",
        "seoTitle": collection.seo_title or "",
        "metaDescription": collection.seo_description or "",
        "descriptionHtml": collection.description_html or "",
        "descriptionText": collection.description_text or "",
        "imageAlt": collection.image_alt or "",
    }


def normalize_proposal_values(
    entity_type: str,
    values: dict[str, Any],
) -> dict[str, Any]:
    """Convert camelCase or mixed keys from API/AI to snake_case proposal keys."""
    mapping = _PRODUCT_CAMEL_TO_SNAKE if entity_type == "product" else _COLLECTION_CAMEL_TO_SNAKE
    allowed_snake = (
        set(_PRODUCT_CAMEL_TO_SNAKE.values())
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
