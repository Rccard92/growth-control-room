"""Product Knowledge item CRUD and Shopify linking."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brand_intelligence import BrandProductKnowledgeItem
from app.models.shopify import ShopifyProduct
from app.schemas.brand_product_knowledge import BrandProductKnowledgeItemUpdate
from app.services.shopify.connect import get_shopify_store_for_project

CompletionStatus = Literal["complete", "partial", "empty"]

_TEXT_FIELDS = (
    "strategic_description",
    "origin",
    "ingredients",
    "production_process",
    "usage_suggestions",
)


def _has_text(value: str | None) -> bool:
    return bool(value and value.strip())


def _has_list(value: list | None) -> bool:
    return bool(value and len(value) > 0)


def item_completion(item: BrandProductKnowledgeItem | None) -> CompletionStatus:
    if not item:
        return "empty"
    text_count = sum(1 for f in _TEXT_FIELDS if _has_text(getattr(item, f)))
    list_count = sum(
        1
        for f in ("objections", "faq", "allowed_claims", "forbidden_claims")
        if _has_list(getattr(item, f))
    )
    if text_count >= 3 and (list_count >= 1 or _has_text(item.seo_notes)):
        return "complete"
    if text_count >= 1 or list_count >= 1 or _has_text(item.seo_notes):
        return "partial"
    return "empty"


async def list_items(session: AsyncSession, project_id: UUID) -> list[BrandProductKnowledgeItem]:
    result = await session.execute(
        select(BrandProductKnowledgeItem)
        .where(BrandProductKnowledgeItem.project_id == project_id)
        .order_by(BrandProductKnowledgeItem.product_name.asc())
    )
    return list(result.scalars().all())


async def get_item(
    session: AsyncSession, project_id: UUID, item_id: UUID
) -> BrandProductKnowledgeItem:
    row = (
        await session.execute(
            select(BrandProductKnowledgeItem).where(
                BrandProductKnowledgeItem.id == item_id,
                BrandProductKnowledgeItem.project_id == project_id,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scheda prodotto non trovata.")
    return row


async def update_item(
    session: AsyncSession,
    project_id: UUID,
    item_id: UUID,
    payload: BrandProductKnowledgeItemUpdate,
) -> BrandProductKnowledgeItem:
    row = await get_item(session, project_id, item_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    await session.commit()
    await session.refresh(row)
    return row


async def delete_item(session: AsyncSession, project_id: UUID, item_id: UUID) -> None:
    row = await get_item(session, project_id, item_id)
    await session.delete(row)
    await session.commit()


async def create_item_from_shopify(
    session: AsyncSession,
    project_id: UUID,
    shopify_product_id: UUID,
) -> BrandProductKnowledgeItem:
    store = await get_shopify_store_for_project(project_id, session)
    if store is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collega e sincronizza Shopify per selezionare prodotti reali.",
        )

    product = (
        await session.execute(
            select(ShopifyProduct).where(
                ShopifyProduct.id == shopify_product_id,
                ShopifyProduct.shopify_store_id == store.id,
            )
        )
    ).scalar_one_or_none()
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prodotto Shopify non trovato. Sincronizza i prodotti prima.",
        )

    existing = (
        await session.execute(
            select(BrandProductKnowledgeItem).where(
                BrandProductKnowledgeItem.project_id == project_id,
                BrandProductKnowledgeItem.shopify_product_id == shopify_product_id,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        return existing

    row = BrandProductKnowledgeItem(
        project_id=project_id,
        shopify_product_id=product.id,
        shopify_product_gid=product.shopify_gid,
        shopify_handle=product.handle,
        shopify_title=product.title,
        product_name=product.title,
        product_line=product.product_type,
        source_type="shopify",
        last_synced_from_shopify_at=datetime.now(UTC),
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def list_shopify_products_for_picker(
    session: AsyncSession, project_id: UUID
) -> tuple[bool, list[tuple[ShopifyProduct, bool]]]:
    store = await get_shopify_store_for_project(project_id, session)
    if store is None:
        return False, []

    products = list(
        (
            await session.execute(
                select(ShopifyProduct)
                .where(ShopifyProduct.shopify_store_id == store.id)
                .order_by(ShopifyProduct.title.asc())
            )
        ).scalars().all()
    )

    linked_ids = set(
        (
            await session.execute(
                select(BrandProductKnowledgeItem.shopify_product_id).where(
                    BrandProductKnowledgeItem.project_id == project_id,
                    BrandProductKnowledgeItem.shopify_product_id.isnot(None),
                )
            )
        ).scalars().all()
    )

    return True, [(p, p.id in linked_ids) for p in products]
