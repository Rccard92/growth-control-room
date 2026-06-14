"""Rule-based editorial calendar plan generation (no OpenAI).

Future Brief Generator will use BrandIntelligenceContextBuilder + Safe Claims.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_seo_editorial import ContentSeoEditorialItem
from app.models.shopify import ShopifyProduct, ShopifyStore
from app.schemas.content_seo_editorial import EditorialPlanGenerateRequest

logger = logging.getLogger(__name__)

_WEEKDAY_MAP = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

_MONTH_NAMES_IT = [
    "Gennaio",
    "Febbraio",
    "Marzo",
    "Aprile",
    "Maggio",
    "Giugno",
    "Luglio",
    "Agosto",
    "Settembre",
    "Ottobre",
    "Novembre",
    "Dicembre",
]

_TITLE_TEMPLATES: dict[str, list[str]] = {
    "educational_article": [
        "Guida: {keyword}",
        "Tutto su {keyword}",
        "Come scegliere {keyword}",
    ],
    "product_guide": [
        "Guida completa: {product}",
        "Come usare {product}",
        "{product}: caratteristiche e consigli",
    ],
    "recipe": [
        "Ricetta con {product}",
        "Ricetta: {keyword}",
        "Idee ricetta — {product}",
    ],
    "faq_objection_article": [
        "Domande frequenti su {keyword}",
        "Obiezioni comuni su {product}",
        "FAQ: {keyword}",
    ],
    "product_comparison": [
        "Confronto prodotti: {keyword}",
        "Quale scegliere? {product}",
        "Confronto guidato — {keyword}",
    ],
    "seasonal_article": [
        "Contenuto stagionale — {month}",
        "{month}: {keyword}",
        "Idee per {month}",
    ],
    "brand_storytelling": [
        "La storia di {brand}",
        "Dietro le quinte — {brand}",
        "Valori e missione — {brand}",
    ],
}


def _iter_dates(request: EditorialPlanGenerateRequest) -> list[date]:
    start = request.start_date
    end = request.end_date
    preferred = request.preferred_weekdays or []
    preferred_nums = {_WEEKDAY_MAP[d] for d in preferred}

    if request.frequency == "daily":
        out: list[date] = []
        current = start
        while current <= end:
            out.append(current)
            current += timedelta(days=1)
        return out

    if request.frequency == "every_2_days":
        step = 2
    elif request.frequency == "every_3_days":
        step = 3
    elif request.frequency == "every_4_days":
        step = 4
    else:
        step = 0

    if step:
        out = []
        current = start
        while current <= end:
            out.append(current)
            current += timedelta(days=step)
        return out

    if request.frequency == "weekly":
        target_weekday = preferred_nums.pop() if preferred_nums else start.weekday()
        out = []
        current = start
        while current.weekday() != target_weekday and current <= end:
            current += timedelta(days=1)
        while current <= end:
            out.append(current)
            current += timedelta(days=7)
        return out

    if request.frequency == "twice_weekly":
        if len(preferred_nums) < 2:
            preferred_nums = {start.weekday(), (start.weekday() + 3) % 7}
        out = []
        current = start
        while current <= end:
            if current.weekday() in preferred_nums:
                out.append(current)
            current += timedelta(days=1)
        return out

    # custom
    out = []
    current = start
    while current <= end:
        if current.weekday() in preferred_nums:
            out.append(current)
        current += timedelta(days=1)
    return out


def _pick_keyword(keywords: list[str], index: int) -> str:
    if not keywords:
        return "argomento SEO"
    return keywords[index % len(keywords)].strip() or "argomento SEO"


def _build_title(
    content_type: str,
    *,
    keyword: str,
    product_title: str | None,
    brand_name: str | None,
    planned: date,
    index: int,
) -> str:
    templates = _TITLE_TEMPLATES.get(content_type, ["Contenuto: {keyword}"])
    template = templates[index % len(templates)]
    month = _MONTH_NAMES_IT[planned.month - 1]
    return template.format(
        keyword=keyword,
        product=product_title or keyword,
        brand=brand_name or "il brand",
        month=month,
    )


def _initial_status(request: EditorialPlanGenerateRequest) -> str:
    if request.primary_keywords:
        return "brief_pending"
    return "idea"


async def _load_products(
    session: AsyncSession,
    project_id: UUID,
    product_ids: list[UUID],
) -> list[ShopifyProduct]:
    if not product_ids:
        return []
    rows = (
        await session.execute(
            select(ShopifyProduct)
            .join(ShopifyStore, ShopifyProduct.shopify_store_id == ShopifyStore.id)
            .where(
                ShopifyStore.project_id == project_id,
                ShopifyProduct.id.in_(product_ids),
            )
        )
    ).scalars().all()
    return list(rows)


async def _brand_name(session: AsyncSession, project_id: UUID) -> str | None:
    try:
        from app.services.brand_intelligence.context import BrandIntelligenceContextBuilder

        bundle = await BrandIntelligenceContextBuilder.build_brand_context(session, project_id)
        if bundle.profile and bundle.profile.brand_name:
            return bundle.profile.brand_name.strip()
    except Exception as exc:
        logger.warning("Editorial plan: Brand context unavailable: %s", exc)
    return None


async def generate_editorial_calendar(
    session: AsyncSession,
    project_id: UUID,
    request: EditorialPlanGenerateRequest,
    *,
    dry_run: bool = False,
) -> list[ContentSeoEditorialItem]:
    dates = _iter_dates(request)
    if not dates:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Nessuna data valida nel periodo selezionato.",
        )

    linked_products = await _load_products(session, project_id, request.linked_product_ids)
    avoid_ids = set(request.avoid_product_ids)
    usable_products = [p for p in linked_products if p.id not in avoid_ids]

    brand = await _brand_name(session, project_id)
    status_value = _initial_status(request)
    content_types = request.content_types
    objectives = request.objectives

    built: list[ContentSeoEditorialItem] = []
    for index, planned in enumerate(dates):
        content_type = content_types[index % len(content_types)]
        objective = objectives[index % len(objectives)]
        keyword = _pick_keyword(request.primary_keywords, index)
        product = usable_products[index % len(usable_products)] if usable_products else None
        title = _build_title(
            content_type,
            keyword=keyword,
            product_title=product.title if product else None,
            brand_name=brand,
            planned=planned,
            index=index,
        )
        row = ContentSeoEditorialItem(
            project_id=project_id,
            title=title,
            content_type=content_type,
            planned_date=planned,
            status=status_value,
            objective=objective,
            primary_keyword=keyword if request.primary_keywords else None,
            commercial_intensity=request.commercial_intensity,
            linked_shopify_product_id=product.id if product else None,
            linked_shopify_product_gid=product.shopify_gid if product else None,
            linked_shopify_product_title=product.title if product else None,
            linked_shopify_product_handle=product.handle if product else None,
            notes=request.notes.strip() or None,
        )
        built.append(row)

    if dry_run:
        now = datetime.now(timezone.utc)
        for row in built:
            row.id = uuid4()
            row.created_at = now
            row.updated_at = now
        return built

    for row in built:
        session.add(row)
    await session.commit()
    for row in built:
        await session.refresh(row)
    return built
