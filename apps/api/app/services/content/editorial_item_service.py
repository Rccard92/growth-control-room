"""CRUD for Content SEO editorial calendar items."""

from __future__ import annotations

import calendar
from datetime import date
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_seo_editorial import ContentSeoEditorialItem
from app.schemas.content_seo_editorial import (
    ContentSeoEditorialItemCreate,
    ContentSeoEditorialItemUpdate,
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
    for key, value in data.items():
        if key == "title" and isinstance(value, str):
            value = value.strip()
        if key == "primary_keyword" and isinstance(value, str):
            value = value.strip() or None
        setattr(row, key, value)
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
