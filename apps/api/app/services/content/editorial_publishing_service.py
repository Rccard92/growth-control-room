"""Save editorial publishing payload without calling Shopify."""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_seo_editorial import ContentSeoEditorialItem
from app.schemas.content_seo_editorial import EditorialPublishingUpdateRequest
from app.services.content.editorial_item_service import get_editorial_item
from app.services.content.editorial_publishing_utils import (
    normalize_publishing_payload,
    validate_publishing_payload,
)


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

    row.publishing_payload = normalized.model_dump(by_alias=True, mode="json")
    if payload.publish_mode is not None:
        row.publish_mode = payload.publish_mode
        normalized_mode = payload.publish_mode
        row.publishing_payload["mode"] = normalized_mode
    if payload.scheduled_publish_at is not None:
        row.scheduled_publish_at = payload.scheduled_publish_at

    await session.flush()
    await session.refresh(row)
    return row
