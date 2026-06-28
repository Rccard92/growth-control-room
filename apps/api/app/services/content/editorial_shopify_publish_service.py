"""Publish or update editorial articles on Shopify via articleCreate / articleUpdate."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_seo import ShopifyBlog
from app.models.content_seo_editorial import ContentSeoEditorialItem
from app.schemas.content_seo_editorial import (
    EditorialPublishShopifyRequest,
    EditorialPublishShopifyResponse,
    EditorialPublishingPayload,
    normalize_editorial_article_payload,
)
from app.services.content.editorial_item_service import get_editorial_item, get_editorial_item_read
from app.services.content.editorial_publishing_utils import (
    HANDLE_CONFLICT_MESSAGE,
    SEO_REQUIRED_MESSAGE,
    attach_publishing_sync_metadata,
    build_article_create_input,
    build_article_seo_metafields,
    build_article_update_input,
    build_publish_shopify_error_detail,
    build_publishing_payload_from_article,
    classify_shopify_publish_error_code,
    format_shopify_publish_error,
    get_publishing_seo_warnings,
    is_publishing_stale,
    normalize_publishing_payload,
    PUBLISHING_STALE_MESSAGE,
    resolve_publishing_author,
    shopify_gid_numeric_id,
    shopify_publish_http_status,
    validate_publishing_payload,
)
from app.services.content.editorial_schedule_utils import (
    PED_PAST_DATE_WARNING,
    apply_ped_schedule_defaults,
    classify_planned_date,
    resolve_editorial_timezone,
    resolve_scheduled_publish_at_from_payload,
    resolve_zoneinfo,
)
from app.services.shopify.client import (
    ShopifyAPIError,
    article_seo_metafields_match,
    parse_article_global_seo_metafields,
)
from app.services.shopify.connect import get_shopify_client_for_store, get_shopify_store_for_project
from app.services.shopify.scopes import can_publish_with_write_content

logger = logging.getLogger(__name__)


async def _project_brand_name(session: AsyncSession, project_id: UUID) -> str | None:
    try:
        from app.services.content.editorial_plan_service import _brand_name

        return await _brand_name(session, project_id)
    except Exception as exc:
        logger.warning("Editorial publish: brand name unavailable: %s", exc)
        return None


def _article_author_name(article_payload: dict | None) -> str | None:
    if not article_payload:
        return None
    raw = article_payload.get("authorName") or article_payload.get("author_name")
    return str(raw).strip() if raw else None


def _user_errors_mention_metafields(user_errors: list[Any]) -> bool:
    for err in user_errors:
        if not isinstance(err, dict):
            continue
        fields = err.get("field") or []
        field_text = " ".join(str(f) for f in fields).lower()
        message = str(err.get("message", "")).lower()
        if "metafield" in field_text or "metafield" in message:
            return True
    return False


def _strip_metafields_from_input(article_input: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in article_input.items() if key != "metafields"}


async def _ensure_shopify_seo_synced(
    client: Any,
    *,
    article_gid: str,
    article_node: dict[str, Any],
    publishing: EditorialPublishingPayload,
    warnings: list[str],
) -> EditorialPublishingPayload:
    expected_title = publishing.seo_title.strip()
    expected_description = publishing.meta_description.strip()
    metafields = build_article_seo_metafields(publishing)

    parsed = parse_article_global_seo_metafields(article_node)
    if not article_seo_metafields_match(
        parsed,
        expected_title=expected_title,
        expected_description=expected_description,
    ):
        sync_result = await client.sync_article_seo_metafields(article_gid, metafields)
        if sync_result.get("synced"):
            parsed = await client.get_article_global_metafields(article_gid)
        else:
            error = str(sync_result.get("error") or "Errore sincronizzazione SEO Shopify.")
            error_message = (
                f"Articolo creato/aggiornato, ma SEO Shopify non sincronizzata: {error}"
            )
            warnings.append(error_message)
            return publishing.model_copy(
                update={
                    "shopify_seo_synced": False,
                    "shopify_seo_synced_at": None,
                    "shopify_seo_error": error_message,
                }
            )

    if article_seo_metafields_match(
        parsed,
        expected_title=expected_title,
        expected_description=expected_description,
    ):
        return publishing.model_copy(
            update={
                "shopify_seo_synced": True,
                "shopify_seo_synced_at": datetime.now(UTC).isoformat(),
                "shopify_seo_error": None,
            }
        )

    error = "I metafields SEO non corrispondono ai valori attesi dopo la sincronizzazione."
    error_message = f"Articolo creato/aggiornato, ma SEO Shopify non sincronizzata: {error}"
    warnings.append(error_message)
    return publishing.model_copy(
        update={
            "shopify_seo_synced": False,
            "shopify_seo_synced_at": None,
            "shopify_seo_error": error_message,
        }
    )


async def _mark_publish_error(
    session: AsyncSession,
    row: ContentSeoEditorialItem,
    *,
    message: str,
    mode: str,
) -> None:
    row.publish_status = "publish_error"
    row.last_publish_error = message
    row.publish_mode = mode
    await session.flush()


async def _raise_shopify_publish_error(
    session: AsyncSession,
    row: ContentSeoEditorialItem,
    exc: ShopifyAPIError,
    mode: str,
    *,
    last_attempt_at: str | None = None,
) -> None:
    readable = format_shopify_publish_error(exc.message)
    http_status = shopify_publish_http_status(exc.message, exc.status_code)
    await _mark_publish_error(session, row, message=readable, mode=mode)
    code = classify_shopify_publish_error_code(exc.message)
    raise HTTPException(
        http_status,
        detail=build_publish_shopify_error_detail(
            code,
            readable,
            shopifyErrors=[exc.message],
            lastAttemptAt=last_attempt_at,
        ),
    ) from exc


def _raise_publish_validation_error(
    errors: list[str],
    *,
    last_attempt_at: str | None = None,
) -> None:
    message = "; ".join(errors)
    if any(SEO_REQUIRED_MESSAGE in err for err in errors):
        code = "seo_missing"
    elif any("programmata obbligatoria" in err.lower() for err in errors):
        code = "schedule_missing"
    elif any("deve essere futura" in err.lower() for err in errors):
        code = "schedule_in_past"
    else:
        code = "validation_error"
    raise HTTPException(
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=build_publish_shopify_error_detail(
            code,
            message,
            validationErrors=errors,
            lastAttemptAt=last_attempt_at,
        ),
    )


async def _resolve_blog_gid(
    session: AsyncSession,
    store_id: UUID,
    payload: EditorialPublishingPayload,
) -> tuple[str, ShopifyBlog | None]:
    if payload.blog_gid:
        result = await session.execute(
            select(ShopifyBlog).where(
                ShopifyBlog.shopify_store_id == store_id,
                ShopifyBlog.shopify_gid == payload.blog_gid,
            )
        )
        blog = result.scalar_one_or_none()
        return payload.blog_gid, blog

    if not payload.blog_id:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Seleziona un blog Shopify prima di pubblicare.",
        )

    try:
        blog_uuid = UUID(str(payload.blog_id))
    except ValueError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Blog Shopify non valido.",
        ) from exc

    result = await session.execute(
        select(ShopifyBlog).where(
            ShopifyBlog.shopify_store_id == store_id,
            ShopifyBlog.id == blog_uuid,
        )
    )
    blog = result.scalar_one_or_none()
    if blog is None:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Blog Shopify non trovato. Sincronizza i blog e riprova.",
        )
    return blog.shopify_gid, blog


def _build_admin_url(
    shop_domain: str,
    blog_numeric_id: str | None,
    article_numeric_id: str | None,
) -> str | None:
    if not blog_numeric_id or not article_numeric_id:
        return None
    return f"https://{shop_domain}/admin/blogs/{blog_numeric_id}/articles/{article_numeric_id}"


def _build_public_url(
    shop_domain: str,
    blog_handle: str | None,
    article_handle: str | None,
) -> str | None:
    if not blog_handle or not article_handle:
        return None
    return f"https://{shop_domain}/blogs/{blog_handle}/{article_handle}"


def _apply_publish_result_to_row(
    row: ContentSeoEditorialItem,
    *,
    store_domain: str,
    blog_gid: str,
    blog_row: ShopifyBlog | None,
    article_node: dict,
    publishing: EditorialPublishingPayload,
    mode: str,
    article_payload: dict,
) -> EditorialPublishingPayload:
    article_gid = article_node.get("id") or row.shopify_article_gid
    article_numeric = shopify_gid_numeric_id(article_gid)
    blog_numeric = shopify_gid_numeric_id(blog_gid)
    blog_handle = blog_row.handle if blog_row else None
    article_handle = article_node.get("handle") or publishing.handle

    row.shopify_article_gid = article_gid
    row.shopify_article_id = article_numeric
    row.shopify_blog_id = blog_numeric or row.shopify_blog_id
    row.shopify_article_admin_url = _build_admin_url(
        store_domain,
        blog_numeric,
        article_numeric,
    )
    row.shopify_article_public_url = _build_public_url(
        store_domain,
        blog_handle,
        article_handle,
    )
    row.publish_mode = mode
    row.last_publish_error = None

    if mode == "publish_now":
        row.publish_status = "published"
        row.shopify_status = "published"
        row.status = "published"
        row.published_at = datetime.now(UTC)
        publishing = publishing.model_copy(update={"is_published": True, "mode": "publish_now"})
    elif mode == "schedule":
        scheduled_at = resolve_scheduled_publish_at_from_payload(publishing)
        row.publish_status = "scheduled"
        row.shopify_status = "scheduled"
        if scheduled_at is not None:
            row.scheduled_publish_at = scheduled_at.astimezone(UTC)
        publish_date = scheduled_at.isoformat() if scheduled_at else publishing.publish_date
        publishing = publishing.model_copy(
            update={
                "is_published": False,
                "mode": "schedule",
                "publish_date": publish_date,
                "scheduled_publish_at": publish_date,
            }
        )
    else:
        if row.publish_status != "published":
            row.publish_status = "draft_created"
            row.shopify_status = "draft"
        publishing = publishing.model_copy(update={"is_published": False, "mode": "draft"})

    publishing = publishing.model_copy(
        update={
            "blog_id": str(blog_row.id) if blog_row else publishing.blog_id,
            "blog_gid": blog_gid,
        }
    )
    article_norm = normalize_editorial_article_payload(article_payload)
    publishing = attach_publishing_sync_metadata(publishing, article_norm)
    row.publishing_payload = publishing.model_dump(by_alias=True, mode="json")
    return publishing


async def publish_editorial_to_shopify(
    session: AsyncSession,
    project_id: UUID,
    item_id: UUID,
    request: EditorialPublishShopifyRequest,
) -> EditorialPublishShopifyResponse:
    row = await get_editorial_item(session, project_id, item_id)
    warnings: list[str] = []

    if not row.article_payload:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Genera l'articolo prima di pubblicare su Shopify.",
        )

    if is_publishing_stale(row.article_payload, row.publishing_payload):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail=build_publish_shopify_error_detail(
                "publishing_stale",
                PUBLISHING_STALE_MESSAGE,
            ),
        )

    if row.status != "ready_to_publish":
        warnings.append(
            "L'articolo non è marcato come pronto per la pubblicazione. "
            "Verrà comunque inviato a Shopify."
        )

    store = await get_shopify_store_for_project(project_id, session)
    if store is None or store.connection_status != "connected":
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="Shopify non connesso per questo progetto.",
        )

    scope_check = await can_publish_with_write_content(store, session)
    if not scope_check["allowed"]:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail=scope_check["message"],
        )

    brand_name = await _project_brand_name(session, project_id)
    article_author = _article_author_name(row.article_payload)
    had_saved_payload = row.publishing_payload is not None
    timezone_name = resolve_editorial_timezone(store)

    if had_saved_payload:
        publishing = normalize_publishing_payload(row.publishing_payload)
    else:
        publishing = build_publishing_payload_from_article(
            row.article_payload,
            shop_name=store.shop_name,
            brand_name=brand_name,
            planned_date=row.planned_date,
            timezone_name=timezone_name,
        )
        warnings.append(
            "Payload di pubblicazione generato dall'articolo. "
            "Salva la tab Pubblicazione per conservarlo."
        )

    if publishing.scheduled_publish_source != "manual":
        publishing = apply_ped_schedule_defaults(
            publishing,
            planned_date=row.planned_date,
            timezone_name=timezone_name,
        )

    publishing = publishing.model_copy(update={"mode": request.mode})

    if request.mode == "schedule":
        planned_class = classify_planned_date(
            row.planned_date,
            resolve_zoneinfo(timezone_name),
        )
        if planned_class == "past":
            warnings.append(PED_PAST_DATE_WARNING)

    if not publishing.author.strip() and not had_saved_payload:
        resolved_author = resolve_publishing_author(
            publishing,
            article_author_name=article_author,
            shop_name=store.shop_name,
            brand_name=brand_name,
        )
        publishing = publishing.model_copy(update={"author": resolved_author})

    resolved_schedule = None
    if request.mode == "schedule":
        resolved_schedule = (
            resolve_scheduled_publish_at_from_payload(publishing) or row.scheduled_publish_at
        )

    errors = validate_publishing_payload(
        publishing,
        for_publish=True,
        scheduled_publish_at=resolved_schedule,
    )
    if errors:
        _raise_publish_validation_error(errors)

    warnings.extend(get_publishing_seo_warnings(publishing))

    blog_gid, blog_row = await _resolve_blog_gid(session, store.id, publishing)
    existing_gid = (row.shopify_article_gid or "").strip()

    attempt_at = datetime.now(UTC).isoformat()
    row.last_publish_error = None
    await session.flush()

    try:
        client = await get_shopify_client_for_store(store)
    except Exception as exc:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            detail="Impossibile contattare Shopify.",
        ) from exc

    if existing_gid:
        try:
            update_input = build_article_update_input(publishing, mode=request.mode)
        except ValueError as exc:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            ) from exc
        try:
            result = await client.update_article(existing_gid, update_input)
        except ShopifyAPIError as exc:
            await _raise_shopify_publish_error(
                session, row, exc, request.mode, last_attempt_at=attempt_at
            )
        operation_label = "aggiornamento"
        article_input_for_retry = update_input
    else:
        handle = publishing.handle.strip()
        if handle:
            try:
                existing = await client.find_article_by_handle(blog_gid, handle)
            except ShopifyAPIError as exc:
                await _raise_shopify_publish_error(
                    session, row, exc, request.mode, last_attempt_at=attempt_at
                )
            if existing:
                existing_id = existing.get("id")
                if existing_id and existing_id != existing_gid:
                    await _mark_publish_error(
                        session,
                        row,
                        message=HANDLE_CONFLICT_MESSAGE,
                        mode=request.mode,
                    )
                    raise HTTPException(
                        status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=build_publish_shopify_error_detail(
                            "shopify_handle_conflict",
                            HANDLE_CONFLICT_MESSAGE,
                            lastAttemptAt=attempt_at,
                        ),
                    )

        try:
            create_input = build_article_create_input(
                publishing,
                blog_gid=blog_gid,
                mode=request.mode,
            )
        except ValueError as exc:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            ) from exc
        try:
            result = await client.create_article(create_input)
        except ShopifyAPIError as exc:
            await _raise_shopify_publish_error(
                session, row, exc, request.mode, last_attempt_at=attempt_at
            )
        operation_label = "creazione"
        article_input_for_retry = create_input

    user_errors = result.get("userErrors") or []
    article_node = result.get("article") or {}
    article_gid = article_node.get("id")

    if not article_gid and user_errors and _user_errors_mention_metafields(user_errors):
        retry_input = _strip_metafields_from_input(article_input_for_retry)
        if existing_gid:
            result = await client.update_article(existing_gid, retry_input)
        else:
            result = await client.create_article(retry_input)
        user_errors = result.get("userErrors") or []
        article_node = result.get("article") or {}
        article_gid = article_node.get("id")

    if user_errors and not article_gid:
        messages = "; ".join(
            err.get("message", str(err)) for err in user_errors if isinstance(err, dict)
        )
        readable = format_shopify_publish_error(
            messages or f"Errore durante la {operation_label} dell'articolo."
        )
        await _mark_publish_error(session, row, message=readable, mode=request.mode)
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=build_publish_shopify_error_detail(
                classify_shopify_publish_error_code(messages),
                readable,
                userErrors=user_errors,
                lastAttemptAt=attempt_at,
            ),
        )

    if user_errors and article_gid:
        logger.warning(
            "Editorial publish: article %s created with userErrors: %s",
            article_gid,
            user_errors,
        )

    if not article_gid:
        row.publish_status = "publish_error"
        row.last_publish_error = f"Shopify non ha restituito l'articolo dopo la {operation_label}."
        await session.flush()
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            detail=row.last_publish_error,
        )

    publishing = await _ensure_shopify_seo_synced(
        client,
        article_gid=article_gid,
        article_node=article_node,
        publishing=publishing,
        warnings=warnings,
    )

    _apply_publish_result_to_row(
        row,
        store_domain=store.shop_domain,
        blog_gid=blog_gid,
        blog_row=blog_row,
        article_node=article_node,
        publishing=publishing,
        mode=request.mode,
        article_payload=row.article_payload,
    )

    if publishing.shopify_seo_synced is False and publishing.shopify_seo_error:
        row.publish_status = "publish_error"
        row.last_publish_error = publishing.shopify_seo_error
        await session.flush()
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=build_publish_shopify_error_detail(
                "shopify_metafields_error",
                publishing.shopify_seo_error,
                lastAttemptAt=attempt_at,
            ),
        )

    await session.flush()
    return EditorialPublishShopifyResponse(
        item=await get_editorial_item_read(session, project_id, item_id),
        warnings=warnings,
    )
