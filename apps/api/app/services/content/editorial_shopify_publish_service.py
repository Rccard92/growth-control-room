"""Publish editorial articles to Shopify via articleCreate."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_seo import ShopifyBlog
from app.models.content_seo_editorial import ContentSeoEditorialItem
from app.schemas.content_seo_editorial import (
    ContentSeoEditorialItemRead,
    EditorialPublishShopifyRequest,
    EditorialPublishShopifyResponse,
    EditorialPublishingPayload,
)
from app.services.content.editorial_item_service import get_editorial_item
from app.services.content.editorial_publishing_utils import (
    build_article_create_input,
    build_publishing_payload_from_article,
    normalize_publishing_payload,
    shopify_gid_numeric_id,
    validate_publishing_payload,
)
from app.services.shopify.client import ShopifyAPIError, ShopifyGraphQLClient
from app.services.shopify.connect import get_shopify_client_for_store, get_shopify_store_for_project
from app.services.shopify.scopes import can_publish_with_write_content

logger = logging.getLogger(__name__)


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

    if row.status != "ready_to_publish":
        warnings.append(
            "L'articolo non è marcato come pronto per la pubblicazione. "
            "Verrà comunque inviato a Shopify."
        )

    if request.mode == "schedule":
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La pubblicazione programmata non è ancora disponibile.",
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

    if row.publishing_payload:
        publishing = normalize_publishing_payload(row.publishing_payload)
    else:
        publishing = build_publishing_payload_from_article(row.article_payload)
        warnings.append(
            "Payload di pubblicazione generato dall'articolo. "
            "Salva la tab Pubblicazione per conservarlo."
        )

    errors = validate_publishing_payload(publishing, for_publish=True)
    if errors:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="; ".join(errors),
        )

    blog_gid, blog_row = await _resolve_blog_gid(session, store.id, publishing)
    article_input = build_article_create_input(
        publishing,
        blog_gid=blog_gid,
        mode=request.mode,
    )

    try:
        client = await get_shopify_client_for_store(store)
        result = await client.create_article(article_input)
    except ShopifyAPIError as exc:
        row.publish_status = "publish_error"
        row.last_publish_error = exc.message
        row.publish_mode = request.mode
        await session.flush()
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            detail=f"Errore Shopify: {exc.message}",
        ) from exc

    user_errors = result.get("userErrors") or []
    if user_errors:
        messages = "; ".join(
            err.get("message", str(err)) for err in user_errors if isinstance(err, dict)
        )
        row.publish_status = "publish_error"
        row.last_publish_error = messages or "Errore durante la creazione dell'articolo."
        row.publish_mode = request.mode
        await session.flush()
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=row.last_publish_error,
        )

    article_node = result.get("article") or {}
    article_gid = article_node.get("id")
    if not article_gid:
        row.publish_status = "publish_error"
        row.last_publish_error = "Shopify non ha restituito l'articolo creato."
        await session.flush()
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            detail=row.last_publish_error,
        )

    article_numeric = shopify_gid_numeric_id(article_gid)
    blog_numeric = shopify_gid_numeric_id(blog_gid)
    blog_handle = blog_row.handle if blog_row else None
    article_handle = article_node.get("handle") or publishing.handle

    row.shopify_article_gid = article_gid
    row.shopify_article_id = article_numeric
    row.shopify_blog_id = blog_numeric or row.shopify_blog_id
    row.shopify_article_admin_url = _build_admin_url(
        store.shop_domain,
        blog_numeric,
        article_numeric,
    )
    row.shopify_article_public_url = _build_public_url(
        store.shop_domain,
        blog_handle,
        article_handle,
    )
    row.publish_mode = request.mode
    row.last_publish_error = None

    if request.mode == "publish_now":
        row.publish_status = "published"
        row.shopify_status = "published"
        row.status = "published"
        row.published_at = datetime.now(UTC)
        publishing = publishing.model_copy(update={"is_published": True, "mode": "publish_now"})
    else:
        row.publish_status = "draft_created"
        row.shopify_status = "draft"
        publishing = publishing.model_copy(update={"is_published": False, "mode": "draft"})

    publishing = publishing.model_copy(
        update={
            "blog_id": str(blog_row.id) if blog_row else publishing.blog_id,
            "blog_gid": blog_gid,
        }
    )
    row.publishing_payload = publishing.model_dump(by_alias=True, mode="json")

    await session.flush()
    return EditorialPublishShopifyResponse(
        item=ContentSeoEditorialItemRead.model_validate(row),
        warnings=warnings,
    )
