"""AI editorial hero image generation for Content SEO items."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from html import unescape
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_seo_editorial import ContentSeoEditorialItem
from app.schemas.content_seo_editorial import (
    EditorialAiGenerationSnapshot,
    EditorialArticlePayload,
    EditorialImageActionResponse,
    EditorialImagePayload,
    normalize_editorial_article_payload,
)
from app.services.ai.ai_client import AiRequestMetadata, OpenAINotConfiguredError, OpenAIRequestError, generate_image, generate_structured_json, is_openai_configured
from app.services.ai.context_profiles import (
    AiContextProfile,
    build_context_for_profile,
    build_prompt_cache_key,
    enrich_ai_metadata,
)
from app.services.content.editorial_ai_usage_service import (
    build_ai_generation_snapshot_from_log,
    fetch_latest_editorial_ai_log,
)
from app.services.content.editorial_image_filename import resolve_unique_editorial_image_filename
from app.core.config import settings
from app.services.content.editorial_image_processing import (
    EDITORIAL_IMAGE_PROVIDER_SIZE,
    normalize_editorial_image_bytes,
    read_image_dimensions,
)
from app.services.content.editorial_image_prompt_builder import (
    EditorialImagePromptContext,
    build_editorial_image_prompt_system,
    build_editorial_image_prompt_user,
)
from app.services.content.editorial_image_skill_loader import (
    EDITORIAL_IMAGE_SKILL_NAME,
    load_editorial_image_skill_context,
)
from app.services.content.editorial_image_storage import (
    delete_editorial_image,
    generate_access_token,
    list_existing_filenames,
    read_editorial_image_bytes,
    resolve_effective_storage_provider,
    resolve_preview_image_url,
    save_editorial_image,
)
from app.services.content.editorial_shopify_files_storage import (
    ShopifyFileUploadResult,
    upload_editorial_image_to_shopify_files,
)
from app.services.content.editorial_image_utils import (
    build_approved_image_backup,
    compute_shopify_image_ready,
    empty_editorial_image_payload,
    normalize_image_payload,
    resolve_editorial_image_alt,
    storage_warning_if_needed,
    sync_approved_image_to_publishing,
    sync_image_alt_from_article,
)
from app.services.content.editorial_item_service import get_editorial_item, get_editorial_item_read
from app.services.content.editorial_publishing_utils import normalize_publishing_payload
from app.services.shopify.client import ShopifyAPIError
from app.services.shopify.connect import get_shopify_client_for_store, get_shopify_store_for_project
from app.services.shopify.scopes import can_upload_shopify_files

logger = logging.getLogger(__name__)

IMAGE_SIZE_USER_MESSAGE = (
    "Formato immagine non supportato dal provider. "
    "Il sistema genera in 1536×1024 e converte a 1200×800."
)

EDITORIAL_IMAGE_MODEL_FALLBACKS = ("gpt-image-2", "gpt-image-1")


def _user_friendly_image_error(exc: OpenAIRequestError) -> str:
    message = str(exc).strip()
    if "invalid size" in message.lower():
        return IMAGE_SIZE_USER_MESSAGE
    return message


async def _generate_editorial_image_bytes(
    image_prompt: str,
    *,
    metadata: AiRequestMetadata,
) -> object:
    """Call OpenAI Images with gpt-image-2 fallback chain and size auto retry."""
    preferred = (settings.openai_image_model or "gpt-image-2").strip()
    models: list[str] = []
    for candidate in (preferred, *EDITORIAL_IMAGE_MODEL_FALLBACKS):
        if candidate and candidate not in models:
            models.append(candidate)

    last_exc: OpenAIRequestError | None = None
    for model in models:
        try:
            return await generate_image(
                image_prompt,
                metadata=metadata,
                model=model,
                size=EDITORIAL_IMAGE_PROVIDER_SIZE,
            )
        except OpenAIRequestError as exc:
            last_exc = exc
            if "invalid size" in str(exc).lower():
                logger.warning(
                    "Editorial image: model %s rejected size %s, retrying with auto",
                    model,
                    EDITORIAL_IMAGE_PROVIDER_SIZE,
                )
                try:
                    return await generate_image(
                        image_prompt,
                        metadata=metadata,
                        model=model,
                        size="auto",
                    )
                except OpenAIRequestError as auto_exc:
                    last_exc = auto_exc
                    logger.warning("Editorial image: model %s auto size failed", model)
                    continue
            logger.warning("Editorial image: model %s failed: %s", model, exc)
            continue

    raise OpenAIRequestError(IMAGE_SIZE_USER_MESSAGE) from last_exc


def _strip_html(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value or "")
    return unescape(re.sub(r"\s+", " ", text)).strip()


def _build_article_summary(article: EditorialArticlePayload) -> str:
    body_excerpt = _strip_html(article.body_html)[:800]
    parts = [
        f"Titolo: {article.title}",
        f"Excerpt: {article.excerpt[:400]}" if article.excerpt else "",
        f"Sommario: {body_excerpt}" if body_excerpt else "",
    ]
    return "\n".join(part for part in parts if part)


def _build_editorial_item_context(row: ContentSeoEditorialItem) -> dict[str, str]:
    brief_angle = ""
    if row.brief_payload and isinstance(row.brief_payload, dict):
        brief_angle = str(
            row.brief_payload.get("contentAngle")
            or row.brief_payload.get("content_angle")
            or ""
        ).strip()
    return {
        "title": row.title,
        "content_type": row.content_type,
        "primary_keyword": row.primary_keyword or "",
        "search_intent": row.search_intent or "",
        "target_audience": row.target_audience or "",
        "content_angle": brief_angle,
        "notes": row.notes or "",
    }


def _extract_secondary_keywords(brief: dict[str, Any] | None) -> list[str]:
    if not brief or not isinstance(brief, dict):
        return []
    raw = brief.get("secondaryKeywords") or brief.get("secondary_keywords") or []
    if not isinstance(raw, list):
        return []
    return [str(item).strip() for item in raw if str(item).strip()]


def _build_prompt_context(
    row: ContentSeoEditorialItem,
    article: EditorialArticlePayload,
    *,
    brand_context: str | None,
    skill_context: str,
    revision_note: str | None = None,
    previous_prompt: str | None = None,
) -> EditorialImagePromptContext:
    brief = row.brief_payload if isinstance(row.brief_payload, dict) else None
    brief_angle = ""
    if brief:
        brief_angle = str(
            brief.get("contentAngle") or brief.get("content_angle") or ""
        ).strip()
    return EditorialImagePromptContext(
        content_type=row.content_type or "",
        article_title=article.title,
        article_excerpt=article.excerpt or "",
        article_body_excerpt=_strip_html(article.body_html)[:800],
        primary_keyword=row.primary_keyword or "",
        secondary_keywords=_extract_secondary_keywords(brief),
        search_intent=row.search_intent or "",
        target_audience=row.target_audience or "",
        content_angle=brief_angle,
        linked_products=list(article.linked_products or []),
        linked_collections=list(article.linked_collections or []),
        brand_context=brand_context,
        skill_context=skill_context,
        revision_note=revision_note,
        previous_prompt=previous_prompt,
    )


async def _build_image_prompt(
    session: AsyncSession,
    project_id: UUID,
    item_id: UUID,
    row: ContentSeoEditorialItem,
    article: EditorialArticlePayload,
    *,
    operation_key: str,
    operation: str,
    revision_note: str | None = None,
    base_prompt: str | None = None,
) -> tuple[str, EditorialAiGenerationSnapshot | None]:
    brief_payload = row.brief_payload if isinstance(row.brief_payload, dict) else None
    ctx = await build_context_for_profile(
        session,
        project_id,
        AiContextProfile.EDITORIAL_IMAGE,
        entity_type="editorial_item",
        entity_id=str(item_id),
        options={
            "shopify_product_id": str(row.linked_shopify_product_id)
            if row.linked_shopify_product_id
            else None,
            "brief_payload": brief_payload,
            "article_summary": _build_article_summary(article),
            "editorial_item": _build_editorial_item_context(row),
            "linked_products": article.linked_products,
            "linked_collections": article.linked_collections,
        },
    )
    brand_context = ctx.context_text
    skill = load_editorial_image_skill_context()
    prompt_ctx = _build_prompt_context(
        row,
        article,
        brand_context=brand_context,
        skill_context=skill.as_prompt_context(),
        revision_note=revision_note,
        previous_prompt=base_prompt,
    )
    metadata = enrich_ai_metadata(
        AiRequestMetadata(
            project_id=project_id,
            module="content_seo",
            operation=operation,
            operation_key=operation_key,
            entity_type="editorial_item",
            entity_id=str(item_id),
        ),
        ctx,
    )
    system_prompt = build_editorial_image_prompt_system(prompt_ctx)
    user_prompt = build_editorial_image_prompt_user(prompt_ctx)

    parsed = await generate_structured_json(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        metadata=metadata,
        prompt_cache_key=build_prompt_cache_key(project_id, metadata.module, ctx.context_hash),
    )
    image_prompt = str(parsed.get("imagePrompt") or parsed.get("image_prompt") or "").strip()
    if not image_prompt:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Impossibile generare il prompt immagine.",
        )

    log = await fetch_latest_editorial_ai_log(
        session,
        project_id,
        item_id,
        (operation_key,),
    )
    snapshot = (
        EditorialAiGenerationSnapshot.model_validate(build_ai_generation_snapshot_from_log(log))
        if log
        else None
    )
    return image_prompt, snapshot


def _require_article(row: ContentSeoEditorialItem) -> EditorialArticlePayload:
    if not row.article_payload:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Genera l'articolo prima di creare l'immagine hero.",
        )
    return normalize_editorial_article_payload(row.article_payload)


def _collect_existing_filenames(
    existing: EditorialImagePayload,
    project_id: UUID,
) -> set[str]:
    names = list_existing_filenames(project_id)
    if existing.image_filename:
        names.add(existing.image_filename)
    if existing.approved_image_backup and existing.approved_image_backup.image_filename:
        names.add(existing.approved_image_backup.image_filename)
    return names


async def _resolve_shopify_upload_context(
    session: AsyncSession,
    project_id: UUID,
) -> tuple[str, bool, bool | None, str | None]:
    effective_provider = await resolve_effective_storage_provider(project_id, session)
    if effective_provider != "shopify_files":
        return effective_provider, False, None, None
    store = await get_shopify_store_for_project(project_id, session)
    shopify_connected = store is not None and store.connection_status == "connected"
    if not shopify_connected:
        return effective_provider, False, False, None
    scope = await can_upload_shopify_files(store, session)
    if scope["allowed"]:
        return effective_provider, True, True, None
    return effective_provider, True, False, scope.get("message")


async def _try_upload_to_shopify_files(
    session: AsyncSession,
    project_id: UUID,
    *,
    filename: str,
    alt_text: str,
    image_bytes: bytes,
    mime_type: str,
) -> tuple[ShopifyFileUploadResult | None, str | None]:
    effective_provider, shopify_connected, can_upload_files, scope_message = (
        await _resolve_shopify_upload_context(session, project_id)
    )
    if effective_provider != "shopify_files":
        return None, None
    if not shopify_connected:
        return None, None
    if can_upload_files is False:
        return None, scope_message
    store = await get_shopify_store_for_project(project_id, session)
    if store is None:
        return None, "Shopify non connesso."
    try:
        client = await get_shopify_client_for_store(store)
        result = await upload_editorial_image_to_shopify_files(
            client,
            filename=filename,
            alt_text=alt_text,
            image_bytes=image_bytes,
            mime_type=mime_type,
        )
        return result, None
    except ShopifyAPIError as exc:
        return None, str(exc)
    except Exception as exc:
        logger.exception("Shopify Files upload failed for editorial image")
        return None, str(exc) or "Errore sconosciuto durante l'upload Shopify."


def _shopify_upload_fields(
    upload_result: ShopifyFileUploadResult,
    *,
    effective_provider: str,
) -> dict[str, object]:
    return {
        "image_storage_provider": effective_provider,
        "shopify_file_id": upload_result.media_gid,
        "shopify_media_gid": upload_result.media_gid,
        "shopify_file_status": upload_result.file_status,
        "shopify_uploaded_at": upload_result.shopify_uploaded_at,
        "image_public_url": upload_result.cdn_url,
        "image_upload_error": None,
    }


async def _persist_generated_image(
    session: AsyncSession,
    row: ContentSeoEditorialItem,
    *,
    project_id: UUID,
    item_id: UUID,
    article: EditorialArticlePayload,
    image_prompt: str,
    image_bytes: bytes,
    image_model: str,
    log_id: str | None,
    estimated_cost: float | None,
    prompt_snapshot: EditorialAiGenerationSnapshot | None,
    revision_note: str | None,
    warnings: list[str],
) -> EditorialImagePayload:
    existing = normalize_image_payload(row.image_payload)
    brief = row.brief_payload if isinstance(row.brief_payload, dict) else None
    alt = resolve_editorial_image_alt(article, brief, row.title)

    provider_returned_size = read_image_dimensions(image_bytes)
    processed_bytes, meta = normalize_editorial_image_bytes(image_bytes)
    version_hint = f"{item_id}:{image_prompt}:{datetime.now(timezone.utc).isoformat()}"
    filename = resolve_unique_editorial_image_filename(
        alt,
        existing_filenames=_collect_existing_filenames(existing, project_id),
        version_hint=version_hint,
    )

    approved_backup = existing.approved_image_backup
    if existing.image_status == "approved" and not approved_backup:
        approved_backup = build_approved_image_backup(existing)
    elif existing.image_status == "approved" and approved_backup:
        pass
    elif existing.image_status in ("generated", "uploaded", "upload_error") and existing.image_storage_path:
        delete_editorial_image(existing.image_storage_path)

    storage_path, public_url, image_hash = save_editorial_image(
        project_id,
        filename,
        processed_bytes,
        content_type=meta["mime_type"],
    )
    access_token = existing.access_token or generate_access_token()

    effective_provider, shopify_connected, can_upload_files, _scope_message = (
        await _resolve_shopify_upload_context(session, project_id)
    )
    upload_result, upload_error = await _try_upload_to_shopify_files(
        session,
        project_id,
        filename=filename,
        alt_text=alt,
        image_bytes=processed_bytes,
        mime_type=meta["mime_type"],
    )

    shopify_fields: dict[str, object] = {
        "image_storage_provider": effective_provider,
        "shopify_file_id": None,
        "shopify_media_gid": None,
        "shopify_file_status": None,
        "shopify_uploaded_at": None,
        "image_public_url": None,
        "image_upload_error": upload_error,
    }
    if upload_result:
        image_status = "uploaded"
        effective_url = upload_result.cdn_url
        shopify_ready = compute_shopify_image_ready(effective_url)
        shopify_fields = _shopify_upload_fields(
            upload_result,
            effective_provider=effective_provider,
        )
    elif upload_error:
        image_status = "upload_error"
        effective_url = None
        shopify_ready = False
    else:
        image_status = "generated"
        shopify_ready = compute_shopify_image_ready(public_url)
        effective_url = public_url if shopify_ready else None

    preview_url = resolve_preview_image_url(project_id, item_id, access_token)

    storage_warning = storage_warning_if_needed(
        shopify_ready,
        effective_provider=effective_provider,
        shopify_connected=shopify_connected,
        can_upload_files=can_upload_files,
        upload_error=upload_error,
    )
    if storage_warning:
        warnings.append(storage_warning)

    skill = load_editorial_image_skill_context()
    now = datetime.now(timezone.utc).isoformat()
    payload = EditorialImagePayload(
        image_status=image_status,
        image_prompt=image_prompt,
        image_revision_note=revision_note,
        image_model=image_model,
        image_alt=alt,
        image_url=effective_url,
        image_storage_path=storage_path,
        image_filename=filename,
        image_original_provider_filename=None,
        image_width=meta["width"],
        image_height=meta["height"],
        image_aspect_ratio=meta["aspect_ratio"],
        image_mime_type=meta["mime_type"],
        image_file_extension=meta["extension"],
        image_provider_size=meta["provider_size"],
        image_final_size=meta["final_size"],
        image_provider_requested_size=meta["provider_size"],
        image_provider_returned_size=provider_returned_size,
        image_post_processing_applied=meta.get("post_processing_applied"),
        image_revised_prompt=image_prompt if revision_note else None,
        generated_from_article_hash=article.article_hash,
        image_generation_cost=estimated_cost,
        image_generation_log_id=log_id,
        image_approved_at=None,
        image_hash=image_hash,
        source_article_hash=article.article_hash,
        access_token=access_token,
        updated_at=now,
        skill_pack_used=EDITORIAL_IMAGE_SKILL_NAME,
        skill_pack_version=skill.version,
        shopify_image_ready=shopify_ready,
        approved_image_backup=approved_backup,
        ai_generation=prompt_snapshot,
        **shopify_fields,
    )
    if not shopify_ready and preview_url and not effective_url:
        payload = payload.model_copy(update={"image_url": None})

    row.image_payload = payload.model_dump(mode="json", by_alias=True)

    if row.publishing_payload and approved_backup:
        publishing = normalize_publishing_payload(row.publishing_payload)
        publishing = sync_approved_image_to_publishing(publishing, payload)
        row.publishing_payload = publishing.model_dump(mode="json", by_alias=True)

    await session.commit()
    await session.refresh(row)
    return payload


async def generate_editorial_image(
    session: AsyncSession,
    project_id: UUID,
    item_id: UUID,
) -> EditorialImageActionResponse:
    if not is_openai_configured():
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OPENAI_API_KEY non configurata.",
        )
    row = await get_editorial_item(session, project_id, item_id)
    article = _require_article(row)
    warnings: list[str] = []

    try:
        image_prompt, prompt_snapshot = await _build_image_prompt(
            session,
            project_id,
            item_id,
            row,
            article,
            operation_key="editorial_image_generation",
            operation="generate_image_prompt",
        )
        image_result = await _generate_editorial_image_bytes(
            image_prompt,
            metadata=AiRequestMetadata(
                project_id=project_id,
                module="content_seo",
                operation="generate_editorial_image",
                operation_key="editorial_image_generation",
                entity_type="editorial_item",
                entity_id=str(item_id),
            ),
        )
    except OpenAINotConfiguredError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except OpenAIRequestError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=_user_friendly_image_error(exc),
        ) from exc

    await _persist_generated_image(
        session,
        row,
        project_id=project_id,
        item_id=item_id,
        article=article,
        image_prompt=image_prompt,
        image_bytes=image_result.image_bytes,
        image_model=image_result.model,
        log_id=image_result.log_id,
        estimated_cost=image_result.estimated_total_cost,
        prompt_snapshot=prompt_snapshot,
        revision_note=None,
        warnings=warnings,
    )
    item = await get_editorial_item_read(session, project_id, item_id)
    return EditorialImageActionResponse(item=item, warnings=warnings)


async def edit_editorial_image(
    session: AsyncSession,
    project_id: UUID,
    item_id: UUID,
    *,
    revision_note: str,
) -> EditorialImageActionResponse:
    if not is_openai_configured():
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OPENAI_API_KEY non configurata.",
        )
    note = revision_note.strip()
    if not note:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Le istruzioni di modifica sono obbligatorie.",
        )

    row = await get_editorial_item(session, project_id, item_id)
    article = _require_article(row)
    existing = normalize_image_payload(row.image_payload)
    warnings: list[str] = []

    try:
        image_prompt, prompt_snapshot = await _build_image_prompt(
            session,
            project_id,
            item_id,
            row,
            article,
            operation_key="editorial_image_edit",
            operation="edit_image_prompt",
            revision_note=note,
            base_prompt=existing.image_prompt or None,
        )
        image_result = await _generate_editorial_image_bytes(
            image_prompt,
            metadata=AiRequestMetadata(
                project_id=project_id,
                module="content_seo",
                operation="edit_editorial_image",
                operation_key="editorial_image_edit",
                entity_type="editorial_item",
                entity_id=str(item_id),
            ),
        )
    except OpenAINotConfiguredError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except OpenAIRequestError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=_user_friendly_image_error(exc),
        ) from exc

    await _persist_generated_image(
        session,
        row,
        project_id=project_id,
        item_id=item_id,
        article=article,
        image_prompt=image_prompt,
        image_bytes=image_result.image_bytes,
        image_model=image_result.model,
        log_id=image_result.log_id,
        estimated_cost=image_result.estimated_total_cost,
        prompt_snapshot=prompt_snapshot,
        revision_note=note,
        warnings=warnings,
    )
    item = await get_editorial_item_read(session, project_id, item_id)
    return EditorialImageActionResponse(item=item, warnings=warnings)


async def approve_editorial_image(
    session: AsyncSession,
    project_id: UUID,
    item_id: UUID,
) -> EditorialImageActionResponse:
    row = await get_editorial_item(session, project_id, item_id)
    article = _require_article(row)
    image_payload = normalize_image_payload(row.image_payload)
    if image_payload.image_status == "upload_error":
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Carica l'immagine su Shopify prima di approvare.",
        )
    if image_payload.image_status not in ("generated", "uploaded"):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Approva solo un'immagine già generata.",
        )
    if not image_payload.image_storage_path:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File immagine mancante.",
        )
    if not image_payload.image_url or not image_payload.shopify_image_ready:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Serve un URL CDN Shopify prima di approvare.",
        )

    warnings: list[str] = []
    brief = row.brief_payload if isinstance(row.brief_payload, dict) else None
    image_payload = sync_image_alt_from_article(
        image_payload,
        article,
        brief=brief,
        item_title=row.title,
    )

    if image_payload.approved_image_backup:
        backup = image_payload.approved_image_backup
        if backup.image_storage_path and backup.image_storage_path != image_payload.image_storage_path:
            delete_editorial_image(backup.image_storage_path)

    storage_warning = storage_warning_if_needed(
        image_payload.shopify_image_ready,
        effective_provider=image_payload.image_storage_provider,
    )
    if storage_warning:
        warnings.append(storage_warning)

    now = datetime.now(timezone.utc).isoformat()
    image_payload = image_payload.model_copy(
        update={
            "image_status": "approved",
            "image_approved_at": now,
            "approved_image_hash": image_payload.image_hash,
            "updated_at": now,
            "approved_image_backup": None,
        }
    )
    row.image_payload = image_payload.model_dump(mode="json", by_alias=True)

    if row.publishing_payload:
        publishing = normalize_publishing_payload(row.publishing_payload)
        publishing = sync_approved_image_to_publishing(publishing, image_payload)
        row.publishing_payload = publishing.model_dump(mode="json", by_alias=True)

    await session.commit()
    item = await get_editorial_item_read(session, project_id, item_id)
    return EditorialImageActionResponse(item=item, warnings=warnings)


async def retry_editorial_image_upload(
    session: AsyncSession,
    project_id: UUID,
    item_id: UUID,
) -> EditorialImageActionResponse:
    row = await get_editorial_item(session, project_id, item_id)
    image_payload = normalize_image_payload(row.image_payload)
    if image_payload.image_status not in ("generated", "uploaded", "upload_error"):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Nessun upload Shopify da ritentare per questa immagine.",
        )
    if not image_payload.image_storage_path:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File immagine mancante.",
        )

    article = _require_article(row)
    brief = row.brief_payload if isinstance(row.brief_payload, dict) else None
    alt = resolve_editorial_image_alt(article, brief, row.title)
    filename = image_payload.image_filename or "articolo-solmielato.jpg"
    mime_type = image_payload.image_mime_type or "image/jpeg"

    effective_provider, shopify_connected, can_upload_files, scope_message = (
        await _resolve_shopify_upload_context(session, project_id)
    )
    if effective_provider != "shopify_files":
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Storage Shopify Files non disponibile per questo progetto.",
        )
    if not shopify_connected:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Shopify non connesso: connetti lo shop per caricare l'immagine.",
        )
    if can_upload_files is False:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=scope_message or "Permessi Shopify insufficienti per l'upload immagini.",
        )

    try:
        image_bytes = read_editorial_image_bytes(image_payload.image_storage_path)
    except FileNotFoundError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="File immagine non trovato.",
        ) from exc

    warnings: list[str] = []
    upload_result, upload_error = await _try_upload_to_shopify_files(
        session,
        project_id,
        filename=filename,
        alt_text=alt,
        image_bytes=image_bytes,
        mime_type=mime_type,
    )

    now = datetime.now(timezone.utc).isoformat()
    if upload_result:
        shopify_ready = compute_shopify_image_ready(upload_result.cdn_url)
        image_payload = image_payload.model_copy(
            update={
                "image_status": "uploaded",
                "image_alt": alt,
                "image_url": upload_result.cdn_url,
                "shopify_image_ready": shopify_ready,
                "updated_at": now,
                **_shopify_upload_fields(upload_result, effective_provider=effective_provider),
            }
        )
    else:
        image_payload = image_payload.model_copy(
            update={
                "image_status": "upload_error",
                "image_alt": alt,
                "image_url": None,
                "shopify_image_ready": False,
                "image_upload_error": upload_error,
                "updated_at": now,
            }
        )

    storage_warning = storage_warning_if_needed(
        image_payload.shopify_image_ready,
        effective_provider=effective_provider,
        shopify_connected=shopify_connected,
        can_upload_files=can_upload_files,
        upload_error=upload_error,
    )
    if storage_warning:
        warnings.append(storage_warning)

    row.image_payload = image_payload.model_dump(mode="json", by_alias=True)
    await session.commit()
    item = await get_editorial_item_read(session, project_id, item_id)
    return EditorialImageActionResponse(item=item, warnings=warnings)


async def sync_editorial_image_from_title(
    session: AsyncSession,
    project_id: UUID,
    item_id: UUID,
) -> EditorialImageActionResponse:
    row = await get_editorial_item(session, project_id, item_id)
    article = _require_article(row)
    image_payload = normalize_image_payload(row.image_payload)
    if image_payload.image_status == "not_generated":
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Nessuna immagine da sincronizzare.",
        )

    warnings: list[str] = []
    brief = row.brief_payload if isinstance(row.brief_payload, dict) else None
    alt = resolve_editorial_image_alt(article, brief, row.title)
    version_hint = f"{item_id}:sync:{alt}"
    filename = resolve_unique_editorial_image_filename(
        alt,
        existing_filenames=_collect_existing_filenames(image_payload, project_id)
        - {image_payload.image_filename or ""},
        version_hint=version_hint,
    )
    if filename != image_payload.image_filename:
        warnings.append(
            "Il nome file SEO è stato aggiornato dal titolo articolo. "
            "Rigenera l'immagine per applicare il nuovo filename al file."
        )

    now = datetime.now(timezone.utc).isoformat()
    image_payload = image_payload.model_copy(
        update={
            "image_alt": alt,
            "image_filename": filename,
            "updated_at": now,
        }
    )
    row.image_payload = image_payload.model_dump(mode="json", by_alias=True)

    if image_payload.image_status == "approved" and row.publishing_payload:
        publishing = normalize_publishing_payload(row.publishing_payload)
        publishing = sync_approved_image_to_publishing(publishing, image_payload)
        row.publishing_payload = publishing.model_dump(mode="json", by_alias=True)

    await session.commit()
    item = await get_editorial_item_read(session, project_id, item_id)
    return EditorialImageActionResponse(item=item, warnings=warnings)


async def remove_editorial_image(
    session: AsyncSession,
    project_id: UUID,
    item_id: UUID,
) -> EditorialImageActionResponse:
    row = await get_editorial_item(session, project_id, item_id)
    existing = normalize_image_payload(row.image_payload)
    if existing.image_storage_path:
        delete_editorial_image(existing.image_storage_path)
    if existing.approved_image_backup and existing.approved_image_backup.image_storage_path:
        delete_editorial_image(existing.approved_image_backup.image_storage_path)

    row.image_payload = empty_editorial_image_payload().model_dump(mode="json", by_alias=True)

    if row.publishing_payload and isinstance(row.publishing_payload, dict):
        publishing = normalize_publishing_payload(row.publishing_payload)
        if publishing.image_url and publishing.image_url == existing.image_url:
            publishing = publishing.model_copy(update={"image_url": None, "image_alt": None})
            row.publishing_payload = publishing.model_dump(mode="json", by_alias=True)

    await session.commit()
    item = await get_editorial_item_read(session, project_id, item_id)
    return EditorialImageActionResponse(item=item, warnings=[])


async def get_editorial_image_media(
    session: AsyncSession,
    project_id: UUID,
    item_id: UUID,
    *,
    token: str,
) -> tuple[bytes, str]:
    row = await get_editorial_item(session, project_id, item_id)
    image_payload = normalize_image_payload(row.image_payload)
    if not image_payload.image_storage_path:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Immagine non trovata.")
    if not image_payload.access_token or token != image_payload.access_token:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Token immagine non valido.")
    try:
        content = read_editorial_image_bytes(image_payload.image_storage_path)
    except FileNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="File immagine non trovato.") from exc
    media_type = image_payload.image_mime_type or "image/jpeg"
    return content, media_type
