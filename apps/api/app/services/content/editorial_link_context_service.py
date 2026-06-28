"""Verified Shopify product/collection link targets for editorial generation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_seo import ShopifyCollection
from app.models.shopify import ShopifyProduct
from app.schemas.content_seo_editorial import EditorialBriefPayload, normalize_editorial_brief_payload
from app.services.shopify.connect import get_shopify_store_for_project

if TYPE_CHECKING:
    from app.models.content_seo_editorial import ContentSeoEditorialItem

EntityType = Literal["product", "collection"]
_MAX_PRODUCTS = 3
_MAX_COLLECTIONS = 3


@dataclass(frozen=True)
class EditorialLinkTarget:
    entity_type: EntityType
    title: str
    handle: str
    path: str

    def to_prompt_dict(self) -> dict[str, str]:
        return {
            "type": self.entity_type,
            "title": self.title,
            "handle": self.handle,
            "path": self.path,
        }


def _product_path(handle: str) -> str:
    return f"/products/{handle.strip()}"


def _collection_path(handle: str) -> str:
    return f"/collections/{handle.strip()}"


def _dedupe_key(target: EditorialLinkTarget) -> tuple[str, str]:
    return (target.entity_type, target.handle.lower())


def format_editorial_link_context_for_prompt(targets: list[EditorialLinkTarget]) -> str:
    import json

    if not targets:
        return "LINK INTERNI VERIFICATI: [] (nessun prodotto/collezione con handle verificato — non inventare URL)"
    payload = [t.to_prompt_dict() for t in targets]
    return f"LINK INTERNI VERIFICATI (usa solo questi path per link nel bodyHtml, max 1–3 link):\n{json.dumps(payload, ensure_ascii=False, indent=2)}"


async def build_editorial_link_context(
    session: AsyncSession,
    project_id: UUID,
    item: "ContentSeoEditorialItem",
    brief: EditorialBriefPayload | dict | None = None,
) -> list[EditorialLinkTarget]:
    """Resolve verified product/collection link targets from DB — never invent URLs."""
    store = await get_shopify_store_for_project(project_id, session)
    if store is None:
        return []

    brief_norm = (
        normalize_editorial_brief_payload(brief)
        if isinstance(brief, dict)
        else (brief or EditorialBriefPayload())
    )
    if brief is None and item.brief_payload:
        brief_norm = normalize_editorial_brief_payload(item.brief_payload)

    seen: set[tuple[str, str]] = set()
    targets: list[EditorialLinkTarget] = []

    def add(target: EditorialLinkTarget) -> None:
        key = _dedupe_key(target)
        if key in seen or not target.handle.strip():
            return
        seen.add(key)
        targets.append(target)

    # 1. Linked product on editorial item
    item_handle = getattr(item, "linked_shopify_product_handle", None) or ""
    item_title = getattr(item, "linked_shopify_product_title", None) or ""
    if item_handle.strip():
        add(
            EditorialLinkTarget(
                entity_type="product",
                title=item_title.strip() or item_handle.strip(),
                handle=item_handle.strip(),
                path=_product_path(item_handle),
            )
        )
    elif getattr(item, "linked_shopify_product_id", None):
        product = await session.get(ShopifyProduct, item.linked_shopify_product_id)
        if product and product.shopify_store_id == store.id and product.handle:
            add(
                EditorialLinkTarget(
                    entity_type="product",
                    title=product.title,
                    handle=product.handle,
                    path=_product_path(product.handle),
                )
            )

    # 2. Products from brief.products_to_link — title match on store catalog
    for product_name in (brief_norm.products_to_link or [])[:_MAX_PRODUCTS]:
        name = str(product_name).strip()
        if not name:
            continue
        stmt = (
            select(ShopifyProduct)
            .where(
                ShopifyProduct.shopify_store_id == store.id,
                ShopifyProduct.handle.isnot(None),
                ShopifyProduct.handle != "",
                or_(
                    ShopifyProduct.title.ilike(name),
                    ShopifyProduct.title.ilike(f"%{name}%"),
                ),
            )
            .limit(1)
        )
        row = (await session.execute(stmt)).scalar_one_or_none()
        if row and row.handle:
            add(
                EditorialLinkTarget(
                    entity_type="product",
                    title=row.title,
                    handle=row.handle,
                    path=_product_path(row.handle),
                )
            )

    # 3. Collections by keyword relevance
    keywords: list[str] = []
    if brief_norm.primary_keyword.strip():
        keywords.append(brief_norm.primary_keyword.strip())
    if getattr(item, "primary_keyword", None) and str(item.primary_keyword).strip():
        kw = str(item.primary_keyword).strip()
        if kw not in keywords:
            keywords.append(kw)
    for kw in (brief_norm.secondary_keywords or [])[:2]:
        if kw.strip() and kw.strip() not in keywords:
            keywords.append(kw.strip())

    collection_count = 0
    for keyword in keywords:
        if collection_count >= _MAX_COLLECTIONS:
            break
        pattern = f"%{keyword}%"
        stmt = (
            select(ShopifyCollection)
            .where(
                ShopifyCollection.shopify_store_id == store.id,
                ShopifyCollection.handle.isnot(None),
                ShopifyCollection.handle != "",
                or_(
                    ShopifyCollection.title.ilike(pattern),
                    ShopifyCollection.handle.ilike(pattern),
                ),
            )
            .limit(_MAX_COLLECTIONS)
        )
        for col in (await session.execute(stmt)).scalars().all():
            if collection_count >= _MAX_COLLECTIONS:
                break
            if col.handle:
                add(
                    EditorialLinkTarget(
                        entity_type="collection",
                        title=col.title,
                        handle=col.handle,
                        path=_collection_path(col.handle),
                    )
                )
                collection_count += 1

    return targets


def split_link_targets_by_type(
    targets: list[EditorialLinkTarget],
) -> tuple[list[str], list[str]]:
    """Return (product_titles, collection_titles) for payload enrichment."""
    products: list[str] = []
    collections: list[str] = []
    for t in targets:
        if t.entity_type == "product" and t.title not in products:
            products.append(t.title)
        elif t.entity_type == "collection" and t.title not in collections:
            collections.append(t.title)
    return products, collections
