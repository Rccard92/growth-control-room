"""Save editorial publishing payload without calling Shopify."""

from __future__ import annotations

from datetime import UTC
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_seo_editorial import ContentSeoEditorialItem
from app.schemas.content_seo_editorial import (
    EditorialPublishingUpdateRequest,
    normalize_editorial_article_payload,
)
from app.services.content.editorial_item_service import get_editorial_item
from app.services.content.editorial_plan_service import _brand_name
from app.services.content.editorial_publishing_utils import (
    attach_publishing_sync_metadata,
    build_publishing_payload_from_article,
    merge_article_into_publishing,
    normalize_publishing_payload,
    resolve_publishing_author,
    validate_publishing_payload,
)
from app.services.content.editorial_schedule_utils import (
    resolve_editorial_timezone,
    resolve_scheduled_publish_at_from_payload,
)
from app.services.shopify.connect import get_shopify_store_for_project


def _sync_row_schedule_fields(
    row: ContentSeoEditorialItem,
    publishing,
) -> None:
    row.publish_mode = publishing.mode
    scheduled_at = resolve_scheduled_publish_at_from_payload(publishing)
    if scheduled_at is not None:
        row.scheduled_publish_at = scheduled_at.astimezone(UTC)
    elif publishing.mode != "schedule":
        row.scheduled_publish_at = None


async def update_editorial_publishing(
    session: AsyncSession,
    project_id: UUID,
    item_id: UUID,
    payload: EditorialPublishingUpdateRequest,
) -> ContentSeoEditorialItem:
    row = await get_editorial_item(session, project_id, item_id)
    normalized = normalize_publishing_payload(payload.publishing_payload)
    errors = validate_publishing_payload(normalized, for_publish=False)
    if errors:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="; ".join(errors),
        )

    if payload.publish_mode is not None:
        normalized = normalized.model_copy(update={"mode": payload.publish_mode})

    if payload.scheduled_publish_at is not None:
        scheduled_at = payload.scheduled_publish_at
        if scheduled_at.tzinfo is None:
            scheduled_at = scheduled_at.replace(tzinfo=UTC)
        normalized = normalized.model_copy(
            update={
                "scheduled_publish_at": scheduled_at.isoformat(),
                "publish_date": scheduled_at.isoformat(),
                "scheduled_publish_source": "manual",
            }
        )

    row.publishing_payload = normalized.model_dump(by_alias=True, mode="json")
    _sync_row_schedule_fields(row, normalized)

    await session.flush()
    await session.refresh(row)
    return row


async def sync_publishing_from_article(
    session: AsyncSession,
    project_id: UUID,
    item_id: UUID,
) -> ContentSeoEditorialItem:
    """Overwrite publishing content fields from article; preserve blog/image/mode."""
    row = await get_editorial_item(session, project_id, item_id)
    if not row.article_payload:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Genera l'articolo prima di sincronizzare i dati di pubblicazione.",
        )

    article = normalize_editorial_article_payload(row.article_payload)
    store = await get_shopify_store_for_project(project_id, session)
    brand_name = await _brand_name(session, project_id)
    shop_name = store.shop_name if store else None
    timezone_name = resolve_editorial_timezone(store)

    if row.publishing_payload:
        base = normalize_publishing_payload(row.publishing_payload)
    else:
        base = build_publishing_payload_from_article(
            article,
            shop_name=shop_name,
            brand_name=brand_name,
            planned_date=row.planned_date,
            timezone_name=timezone_name,
        )

    merged = merge_article_into_publishing(
        base,
        article,
        overwrite=True,
        shop_name=shop_name,
        brand_name=brand_name,
    )
    author = resolve_publishing_author(
        merged,
        article_author_name=article.author_name,
        shop_name=shop_name,
        brand_name=brand_name,
    )
    merged = merged.model_copy(update={"author": author})
    merged = attach_publishing_sync_metadata(merged, article)

    row.publishing_payload = merged.model_dump(by_alias=True, mode="json")
    _sync_row_schedule_fields(row, merged)
    await session.flush()
    await session.refresh(row)
    return row


async def disconnect_editorial_shopify_article(
    session: AsyncSession,
    project_id: UUID,
    item_id: UUID,
) -> ContentSeoEditorialItem:
    """Clear Shopify article link without deleting GCR article or publishing payload."""
    row = await get_editorial_item(session, project_id, item_id)
    row.shopify_article_gid = None
    row.shopify_article_id = None
    row.shopify_article_admin_url = None
    row.shopify_article_public_url = None
    row.shopify_status = None
    row.publish_status = "not_published"
    row.last_publish_error = None
    await session.flush()
    await session.refresh(row)
    return row
