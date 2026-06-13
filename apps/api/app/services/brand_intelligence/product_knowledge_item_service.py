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
from app.schemas.brand_product_knowledge import (
    BrandProductKnowledgeDuplicateCandidate,
    BrandProductKnowledgeItemProposal,
    BrandProductKnowledgeItemRead,
    BrandProductKnowledgeItemsApplyImportResponse,
    BrandProductKnowledgeSkippedItem,
    BrandProductKnowledgeItemUpdate,
)
from app.services.brand_intelligence.product_knowledge_shopify_match import (
    normalize_product_label,
    score_name_to_product,
)
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


def _proposal_to_item_fields(proposal: BrandProductKnowledgeItemProposal) -> dict:
    fields: dict = {
        "product_name": proposal.product_name.strip(),
        "source_type": "ai_import",
    }
    optional_strings = (
        ("product_line", proposal.product_line),
        ("priority", proposal.priority),
        ("strategic_description", proposal.strategic_description),
        ("origin", proposal.origin),
        ("ingredients", proposal.ingredients),
        ("production_process", proposal.production_process),
        ("taste_notes", proposal.taste_notes),
        ("color_notes", proposal.color_notes),
        ("texture_notes", proposal.texture_notes),
        ("usage_suggestions", proposal.usage_suggestions),
        ("conservation", proposal.conservation),
        ("target_audience", proposal.target_audience),
        ("seo_notes", proposal.seo_notes),
        ("ads_social_notes", proposal.ads_social_notes),
    )
    for key, value in optional_strings:
        if value and str(value).strip():
            fields[key] = str(value).strip()

    optional_lists = (
        ("objections", proposal.objections),
        ("faq", proposal.faq),
        ("allowed_claims", proposal.allowed_claims),
        ("forbidden_claims", proposal.forbidden_claims),
        ("related_products", proposal.related_products),
    )
    for key, value in optional_lists:
        if value and len(value) > 0:
            fields[key] = value

    return fields


async def _find_duplicate_candidates(
    session: AsyncSession,
    project_id: UUID,
    proposal: BrandProductKnowledgeItemProposal,
    shopify_product_id: UUID | None,
) -> list[BrandProductKnowledgeDuplicateCandidate]:
    existing_items = await list_items(session, project_id)
    candidates: list[BrandProductKnowledgeDuplicateCandidate] = []
    norm_name = normalize_product_label(proposal.product_name)

    for existing in existing_items:
        if shopify_product_id and existing.shopify_product_id == shopify_product_id:
            candidates.append(
                BrandProductKnowledgeDuplicateCandidate(
                    existing_item_id=existing.id,
                    product_name=existing.product_name,
                    shopify_handle=existing.shopify_handle,
                    reason="Esiste già una scheda collegata a questo prodotto Shopify.",
                    completion_status=item_completion(existing),
                )
            )
            continue

        if normalize_product_label(existing.product_name) == norm_name:
            candidates.append(
                BrandProductKnowledgeDuplicateCandidate(
                    existing_item_id=existing.id,
                    product_name=existing.product_name,
                    shopify_handle=existing.shopify_handle,
                    reason="Esiste già una scheda con lo stesso nome prodotto.",
                    completion_status=item_completion(existing),
                )
            )
            continue

        if (
            existing.shopify_product_id
            and item_completion(existing) != "empty"
            and score_name_to_product(
                proposal.product_name,
                existing.shopify_title or existing.product_name,
                existing.shopify_handle or "",
            )
            >= 0.85
        ):
            candidates.append(
                BrandProductKnowledgeDuplicateCandidate(
                    existing_item_id=existing.id,
                    product_name=existing.product_name,
                    shopify_handle=existing.shopify_handle,
                    reason="Scheda esistente simile già compilata.",
                    completion_status=item_completion(existing),
                )
            )

    return candidates


async def _resolve_shopify_product(
    session: AsyncSession,
    project_id: UUID,
    proposal: BrandProductKnowledgeItemProposal,
) -> ShopifyProduct | None:
    store = await get_shopify_store_for_project(project_id, session)
    if store is None:
        return None

    shopify_id = proposal.shopify_product_id or proposal.suggested_shopify_product_id
    if shopify_id is None:
        return None

    return (
        await session.execute(
            select(ShopifyProduct).where(
                ShopifyProduct.id == shopify_id,
                ShopifyProduct.shopify_store_id == store.id,
            )
        )
    ).scalar_one_or_none()


async def apply_items_import_proposal(
    session: AsyncSession,
    project_id: UUID,
    items: list[BrandProductKnowledgeItemProposal],
) -> BrandProductKnowledgeItemsApplyImportResponse:
    saved: list[BrandProductKnowledgeItemRead] = []
    skipped: list[BrandProductKnowledgeSkippedItem] = []

    for proposal in items:
        if not proposal.product_name or not proposal.product_name.strip():
            skipped.append(
                BrandProductKnowledgeSkippedItem(
                    product_name=proposal.product_name or "(senza nome)",
                    reason="Nome prodotto obbligatorio.",
                )
            )
            continue

        shopify_product = await _resolve_shopify_product(session, project_id, proposal)
        shopify_id = shopify_product.id if shopify_product else None

        duplicates = await _find_duplicate_candidates(session, project_id, proposal, shopify_id)
        if duplicates:
            skipped.append(
                BrandProductKnowledgeSkippedItem(
                    product_name=proposal.product_name,
                    reason="Possibile duplicato: scheda non sovrascritta.",
                    duplicate_candidates=duplicates,
                )
            )
            continue

        fields = _proposal_to_item_fields(proposal)
        if shopify_product:
            fields.update(
                {
                    "shopify_product_id": shopify_product.id,
                    "shopify_product_gid": shopify_product.shopify_gid,
                    "shopify_handle": shopify_product.handle,
                    "shopify_title": shopify_product.title,
                }
            )

        row = BrandProductKnowledgeItem(project_id=project_id, **fields)
        session.add(row)
        await session.flush()
        await session.refresh(row)
        read = BrandProductKnowledgeItemRead.model_validate(row)
        read.completion_status = item_completion(row)
        saved.append(read)

    await session.commit()

    message = f"{len(saved)} scheda/e salvata/e."
    if skipped:
        message += f" {len(skipped)} saltata/e (duplicati o dati mancanti)."

    return BrandProductKnowledgeItemsApplyImportResponse(
        saved=saved,
        skipped=skipped,
        message=message,
    )
