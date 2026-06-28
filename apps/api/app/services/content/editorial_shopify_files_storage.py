"""Upload editorial hero images to Shopify Files via staged upload + fileCreate."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from app.services.shopify.client import ShopifyAPIError, ShopifyGraphQLClient


@dataclass(frozen=True)
class ShopifyFileUploadResult:
    media_gid: str
    file_status: str
    cdn_url: str
    shopify_uploaded_at: str
    image_width: int | None = None
    image_height: int | None = None


def extract_shopify_cdn_url(media_node: dict[str, Any]) -> str | None:
    image_block = media_node.get("image") or {}
    url = image_block.get("url")
    if url:
        return str(url)
    preview = media_node.get("preview") or {}
    preview_image = preview.get("image") or {}
    preview_url = preview_image.get("url")
    if preview_url:
        return str(preview_url)
    return None


async def upload_editorial_image_to_shopify_files(
    client: ShopifyGraphQLClient,
    *,
    filename: str,
    alt_text: str,
    image_bytes: bytes,
    mime_type: str = "image/jpeg",
) -> ShopifyFileUploadResult:
    target = await client.create_staged_upload_for_image(
        filename=filename,
        mime_type=mime_type,
        file_size=len(image_bytes),
    )
    resource_url = target.get("resourceUrl")
    if not resource_url:
        raise ShopifyAPIError("Shopify non ha restituito resourceUrl per l'upload.")

    await client.upload_to_staged_target(target, image_bytes, mime_type=mime_type)
    created = await client.file_create_from_staged_upload(str(resource_url), alt_text)
    media_gid = str(created.get("id") or "")
    if not media_gid:
        raise ShopifyAPIError("Shopify non ha restituito l'ID del file creato.")

    ready_node = await client.wait_until_file_ready(media_gid)
    cdn_url = extract_shopify_cdn_url(ready_node)
    if not cdn_url:
        raise ShopifyAPIError(
            "File Shopify pronto ma URL CDN non disponibile. Riprova l'upload."
        )

    image_block = ready_node.get("image") or {}
    width = image_block.get("width")
    height = image_block.get("height")
    return ShopifyFileUploadResult(
        media_gid=media_gid,
        file_status=str(ready_node.get("fileStatus") or "READY"),
        cdn_url=cdn_url,
        shopify_uploaded_at=datetime.now(UTC).isoformat(),
        image_width=int(width) if width is not None else None,
        image_height=int(height) if height is not None else None,
    )
