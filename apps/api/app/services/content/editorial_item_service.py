"""CRUD for Content SEO editorial calendar items."""

from __future__ import annotations

import calendar
from datetime import date, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_seo_editorial import ContentSeoEditorialItem
from app.schemas.content_seo_editorial import (
    ContentSeoEditorialItemCreate,
    ContentSeoEditorialItemRead,
    ContentSeoEditorialItemUpdate,
    EditorialItemRescheduleRequest,
)
from app.services.content.editorial_image_utils import is_image_stale
from app.services.content.editorial_publishing_utils import (
    is_publishing_stale,
    normalize_publishing_payload,
)
from app.services.content.editorial_schedule_utils import (
    resolve_editorial_timezone,
    resolve_scheduled_publish_at_from_payload,
    sync_ped_schedule_on_planned_date_change,
)
from app.services.shopify.connect import get_shopify_store_for_project


def _apply_planned_date_schedule_sync(
    row: ContentSeoEditorialItem,
    *,
    timezone_name: str | None,
) -> None:
    updated_payload = sync_ped_schedule_on_planned_date_change(
        row.publishing_payload,
        planned_date=row.planned_date,
        timezone_name=timezone_name,
    )
    if updated_payload is None:
        return
    row.publishing_payload = updated_payload
    publishing = normalize_publishing_payload(updated_payload)
    scheduled_at = resolve_scheduled_publish_at_from_payload(publishing)
    if scheduled_at is not None:
        from datetime import UTC

        row.scheduled_publish_at = scheduled_at.astimezone(UTC)
    elif publishing.mode != "schedule":
        row.scheduled_publish_at = None


def serialize_editorial_item_read(row: ContentSeoEditorialItem) -> ContentSeoEditorialItemRead:
    """Serialize DB row with computed publishingIsStale and imageIsStale."""
    base = ContentSeoEditorialItemRead.model_validate(row)
    return base.model_copy(
        update={
            "publishing_is_stale": is_publishing_stale(
                row.article_payload,
                row.publishing_payload,
            ),
            "image_is_stale": is_image_stale(
                row.article_payload,
                row.image_payload,
            ),
        }
    )


def _month_range(month: str) -> tuple[date, date]:
    year, mon = map(int, month.split("-"))
    last_day = calendar.monthrange(year, mon)[1]
    return date(year, mon, 1), date(year, mon, last_day)


async def list_editorial_items(
    session: AsyncSession,
    project_id: UUID,
    *,
    month: str | None = None,
    status: str | None = None,
    content_type: str | None = None,
) -> list[ContentSeoEditorialItem]:
    stmt = select(ContentSeoEditorialItem).where(
        ContentSeoEditorialItem.project_id == project_id
    )
    if month:
        start, end = _month_range(month)
        stmt = stmt.where(
            ContentSeoEditorialItem.planned_date >= start,
            ContentSeoEditorialItem.planned_date <= end,
        )
    if status:
        stmt = stmt.where(ContentSeoEditorialItem.status == status)
    if content_type:
        stmt = stmt.where(ContentSeoEditorialItem.content_type == content_type)
    stmt = stmt.order_by(
        ContentSeoEditorialItem.planned_date.asc(),
        ContentSeoEditorialItem.created_at.asc(),
    )
    return list((await session.execute(stmt)).scalars().all())


async def get_editorial_item(
    session: AsyncSession,
    project_id: UUID,
    item_id: UUID,
) -> ContentSeoEditorialItem:
    row = (
        await session.execute(
            select(ContentSeoEditorialItem).where(
                ContentSeoEditorialItem.project_id == project_id,
                ContentSeoEditorialItem.id == item_id,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Contenuto editoriale non trovato.")
    return row


async def get_editorial_item_read(
    session: AsyncSession,
    project_id: UUID,
    item_id: UUID,
) -> ContentSeoEditorialItemRead:
    """Load editorial item and serialize safely after async flush/commit."""
    row = await get_editorial_item(session, project_id, item_id)
    await session.refresh(row)
    return serialize_editorial_item_read(row)


async def create_editorial_item(
    session: AsyncSession,
    project_id: UUID,
    payload: ContentSeoEditorialItemCreate,
) -> ContentSeoEditorialItem:
    row = ContentSeoEditorialItem(
        project_id=project_id,
        title=payload.title.strip(),
        content_type=payload.content_type,
        planned_date=payload.planned_date,
        status=payload.status,
        objective=payload.objective,
        primary_keyword=(payload.primary_keyword or "").strip() or None,
        secondary_keywords=payload.secondary_keywords,
        target_audience=payload.target_audience,
        search_intent=payload.search_intent,
        commercial_intensity=payload.commercial_intensity,
        linked_shopify_product_id=payload.linked_shopify_product_id,
        linked_shopify_product_gid=payload.linked_shopify_product_gid,
        linked_shopify_product_title=payload.linked_shopify_product_title,
        linked_shopify_product_handle=payload.linked_shopify_product_handle,
        linked_collection_id=payload.linked_collection_id,
        linked_collection_title=payload.linked_collection_title,
        notes=payload.notes,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def update_editorial_item(
    session: AsyncSession,
    project_id: UUID,
    item_id: UUID,
    payload: ContentSeoEditorialItemUpdate,
) -> ContentSeoEditorialItem:
    row = await get_editorial_item(session, project_id, item_id)
    data = payload.model_dump(exclude_unset=True)
    planned_date_changed = "planned_date" in data
    for key, value in data.items():
        if key == "title" and isinstance(value, str):
            value = value.strip()
        if key == "primary_keyword" and isinstance(value, str):
            value = value.strip() or None
        setattr(row, key, value)
    if planned_date_changed:
        store = await get_shopify_store_for_project(project_id, session)
        _apply_planned_date_schedule_sync(
            row,
            timezone_name=resolve_editorial_timezone(store),
        )
    await session.commit()
    await session.refresh(row)
    return row


async def delete_editorial_item(
    session: AsyncSession,
    project_id: UUID,
    item_id: UUID,
) -> None:
    row = await get_editorial_item(session, project_id, item_id)
    await session.delete(row)
    await session.commit()


async def _duplicate_planned_date_warning(
    session: AsyncSession,
    project_id: UUID,
) -> str | None:
    rows = (
        await session.execute(
            select(ContentSeoEditorialItem.planned_date).where(
                ContentSeoEditorialItem.project_id == project_id
            )
        )
    ).scalars().all()
    if len(rows) != len(set(rows)):
        return "Alcuni contenuti potrebbero cadere nello stesso giorno."
    return None


async def reschedule_editorial_item(
    session: AsyncSession,
    project_id: UUID,
    item_id: UUID,
    payload: EditorialItemRescheduleRequest,
) -> tuple[list[ContentSeoEditorialItem], int, str | None]:
    row = await get_editorial_item(session, project_id, item_id)
    old_date = row.planned_date
    new_date = payload.planned_date
    delta = (new_date - old_date).days

    row.planned_date = new_date
    updated: list[ContentSeoEditorialItem] = [row]
    store = await get_shopify_store_for_project(project_id, session)
    timezone_name = resolve_editorial_timezone(store)

    if payload.cascade and delta != 0:
        following = (
            await session.execute(
                select(ContentSeoEditorialItem)
                .where(
                    ContentSeoEditorialItem.project_id == project_id,
                    ContentSeoEditorialItem.planned_date > old_date,
                    ContentSeoEditorialItem.id != item_id,
                )
                .order_by(
                    ContentSeoEditorialItem.planned_date.asc(),
                    ContentSeoEditorialItem.created_at.asc(),
                )
            )
        ).scalars().all()
        for item in following:
            item.planned_date = item.planned_date + timedelta(days=delta)
            _apply_planned_date_schedule_sync(item, timezone_name=timezone_name)
            updated.append(item)

    _apply_planned_date_schedule_sync(row, timezone_name=timezone_name)

    await session.commit()
    for item in updated:
        await session.refresh(item)

    warning = await _duplicate_planned_date_warning(session, project_id)
    return updated, delta, warning
