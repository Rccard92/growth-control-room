"""Editorial hero image helpers: stale check, alt sync, publishing sync."""

from __future__ import annotations

from typing import Any

from app.schemas.content_seo_editorial import (
    EditorialApprovedImageBackup,
    EditorialArticlePayload,
    EditorialImagePayload,
    EditorialPublishingPayload,
    normalize_editorial_image_payload,
)
from app.services.content.editorial_image_filename import (
    build_editorial_image_filename,
    filename_slug_from_image_filename,
)
from app.services.content.editorial_image_storage import (
    is_shopify_image_publishable,
    storage_warning_if_needed as resolve_editorial_storage_warning,
)
from app.utils.slug import slugify

IMAGE_STALE_MESSAGE = (
    "L'immagine potrebbe non essere aggiornata rispetto all'ultima versione dell'articolo."
)
IMAGE_STALE_PUBLISH_WARNING = (
    "L'immagine approvata potrebbe non essere allineata all'ultima versione dell'articolo."
)
NO_APPROVED_IMAGE_WARNING = "Nessuna immagine approvata associata all'articolo."
FILENAME_STALE_MESSAGE = (
    "Il titolo articolo è cambiato: il nome file SEO potrebbe non essere più allineato."
)
DEFAULT_IMAGE_ALT = "Immagine articolo Solmielato"


def _read_str_field(payload: dict[str, Any] | None, *keys: str) -> str | None:
    if not payload or not isinstance(payload, dict):
        return None
    for key in keys:
        value = payload.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return None


def _payload_is_present(payload: dict[str, Any] | EditorialImagePayload | None) -> bool:
    if payload is None:
        return False
    if isinstance(payload, EditorialImagePayload):
        return payload.image_status != "not_generated"
    if not isinstance(payload, dict):
        return False
    status = _read_str_field(payload, "imageStatus", "image_status") or "not_generated"
    return status != "not_generated"


def resolve_editorial_image_alt(
    article: EditorialArticlePayload | dict[str, Any] | None,
    brief: dict[str, Any] | None,
    item_title: str | None,
) -> str:
    if article is not None:
        title = (
            article.title.strip()
            if isinstance(article, EditorialArticlePayload)
            else str(article.get("title") or article.get("Title") or "").strip()
        )
        if title:
            return title
    if brief and isinstance(brief, dict):
        proposed = str(brief.get("proposedTitle") or brief.get("proposed_title") or "").strip()
        if proposed:
            return proposed
    if item_title and item_title.strip():
        return item_title.strip()
    return DEFAULT_IMAGE_ALT


def is_image_stale(
    article_payload: dict[str, Any] | EditorialArticlePayload | None,
    image_payload: dict[str, Any] | EditorialImagePayload | None,
) -> bool:
    if article_payload is None or not _payload_is_present(image_payload):
        return False
    source_hash = _read_str_field(
        image_payload if isinstance(image_payload, dict) else image_payload.model_dump(by_alias=True),
        "sourceArticleHash",
        "source_article_hash",
    )
    if isinstance(image_payload, EditorialImagePayload):
        source_hash = image_payload.source_article_hash or source_hash
    article_hash = _read_str_field(
        article_payload if isinstance(article_payload, dict) else article_payload.model_dump(by_alias=True),
        "articleHash",
        "article_hash",
    )
    if isinstance(article_payload, EditorialArticlePayload):
        article_hash = article_payload.article_hash or article_hash
    if not source_hash or not article_hash:
        return False
    return article_hash != source_hash


def is_image_filename_stale(
    image_payload: EditorialImagePayload,
    article_title: str,
) -> bool:
    if not image_payload.image_filename:
        return False
    current_slug = slugify(article_title.strip())
    file_slug = filename_slug_from_image_filename(image_payload.image_filename)
    if not current_slug or not file_slug:
        return False
    if file_slug.endswith("-v2") or "-v" in file_slug:
        base_file = file_slug.rsplit("-v", 1)[0]
        return base_file != current_slug[: len(base_file)]
    return file_slug != current_slug


def _effective_publishing_image(image_payload: EditorialImagePayload) -> EditorialImagePayload:
    if image_payload.image_status in ("generated", "uploaded") and image_payload.approved_image_backup:
        backup = image_payload.approved_image_backup
        return image_payload.model_copy(
            update={
                "image_status": "approved",
                "image_url": backup.image_url,
                "image_alt": backup.image_alt,
                "image_storage_path": backup.image_storage_path,
                "image_filename": backup.image_filename,
                "shopify_image_ready": backup.shopify_image_ready,
            }
        )
    return image_payload


def sync_image_alt_from_article(
    image_payload: EditorialImagePayload,
    article: EditorialArticlePayload | dict[str, Any],
    *,
    brief: dict[str, Any] | None = None,
    item_title: str | None = None,
) -> EditorialImagePayload:
    alt = resolve_editorial_image_alt(article, brief, item_title)
    return image_payload.model_copy(update={"image_alt": alt})


def sync_approved_image_to_publishing(
    publishing: EditorialPublishingPayload,
    image_payload: EditorialImagePayload,
) -> EditorialPublishingPayload:
    effective = _effective_publishing_image(image_payload)
    if effective.image_status != "approved":
        return publishing
    if not effective.shopify_image_ready or not effective.image_url:
        return publishing
    return publishing.model_copy(
        update={
            "image_url": effective.image_url,
            "image_alt": effective.image_alt or publishing.image_alt,
        }
    )


def compute_shopify_image_ready(image_url: str | None) -> bool:
    return is_shopify_image_publishable(image_url)


def build_approved_image_backup(image_payload: EditorialImagePayload) -> EditorialApprovedImageBackup:
    return EditorialApprovedImageBackup(
        image_url=image_payload.image_url,
        image_storage_path=image_payload.image_storage_path,
        image_filename=image_payload.image_filename,
        image_alt=image_payload.image_alt,
        image_hash=image_payload.image_hash,
        image_approved_at=image_payload.image_approved_at,
        shopify_image_ready=image_payload.shopify_image_ready,
        image_width=image_payload.image_width,
        image_height=image_payload.image_height,
        image_mime_type=image_payload.image_mime_type,
    )


def storage_warning_if_needed(
    shopify_ready: bool,
    *,
    effective_provider: str | None = None,
    shopify_connected: bool | None = None,
    can_upload_files: bool | None = None,
    upload_error: str | None = None,
) -> str | None:
    return resolve_editorial_storage_warning(
        shopify_ready,
        effective_provider=effective_provider,
        shopify_connected=shopify_connected,
        can_upload_files=can_upload_files,
        upload_error=upload_error,
    )


def is_image_publish_sync_stale(
    image_payload: EditorialImagePayload,
    publishing: EditorialPublishingPayload,
) -> bool:
    if image_payload.image_status != "approved":
        return False
    if not image_payload.image_url:
        return False
    if publishing.image_url and publishing.image_url != image_payload.image_url:
        return True
    if publishing.image_alt and image_payload.image_alt and publishing.image_alt != image_payload.image_alt:
        return True
    return False


def is_image_shopify_synced(image_payload: EditorialImagePayload) -> bool:
    if not image_payload.shopify_image_synced_at:
        return False
    if image_payload.image_approved_at:
        return image_payload.shopify_image_synced_at >= image_payload.image_approved_at
    return True


def empty_editorial_image_payload() -> EditorialImagePayload:
    return EditorialImagePayload()


def normalize_image_payload(raw: dict[str, Any] | None) -> EditorialImagePayload:
    if not raw:
        return empty_editorial_image_payload()
    return normalize_editorial_image_payload(raw)


def refresh_image_filename_from_title(
    image_payload: EditorialImagePayload,
    article_title: str,
    *,
    version_hint: str | None = None,
) -> EditorialImagePayload:
    alt = article_title.strip() or DEFAULT_IMAGE_ALT
    filename = build_editorial_image_filename(alt)
    if version_hint:
        from app.services.content.editorial_image_filename import resolve_unique_editorial_image_filename

        filename = resolve_unique_editorial_image_filename(
            alt,
            existing_filenames=set(),
            version_hint=version_hint,
        )
    return image_payload.model_copy(
        update={
            "image_alt": alt,
            "image_filename": filename,
        }
    )
