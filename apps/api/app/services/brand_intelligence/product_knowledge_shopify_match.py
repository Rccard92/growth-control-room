"""Shopify product matching for Product Knowledge item import."""

from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shopify import ShopifyProduct
from app.schemas.brand_product_knowledge import BrandProductKnowledgeItemProposal
from app.services.shopify.connect import get_shopify_store_for_project

_MATCH_THRESHOLD = 0.75

_PREFIXES = (
    "miele di ",
    "miele ",
    "miele",
)


def normalize_product_label(value: str) -> str:
    if not value:
        return ""
    text = unicodedata.normalize("NFKD", value.strip().lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    for prefix in _PREFIXES:
        if text.startswith(prefix):
            text = text[len(prefix) :].strip()
            break
    return text


def _token_set(value: str) -> set[str]:
    return {t for t in normalize_product_label(value).split() if t}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def score_shopify_match(proposal_name: str, product: ShopifyProduct) -> float:
    return score_name_to_product(proposal_name, product.title, product.handle)


def score_name_to_product(proposal_name: str, title: str, handle: str) -> float:
    norm_proposal = normalize_product_label(proposal_name)
    norm_title = normalize_product_label(title)
    norm_handle = normalize_product_label(handle.replace("-", " "))

    if not norm_proposal:
        return 0.0

    if norm_proposal == norm_title:
        return 1.0

    if norm_proposal in norm_title or norm_title in norm_proposal:
        return 0.9

    if norm_proposal == norm_handle or norm_proposal in norm_handle or norm_handle in norm_proposal:
        return 0.85

    token_score = _jaccard(_token_set(proposal_name), _token_set(title))
    if token_score >= 0.6:
        return round(0.6 + token_score * 0.25, 2)

    seq_score = SequenceMatcher(None, norm_proposal, norm_title).ratio()
    if seq_score >= 0.75:
        return round(seq_score * 0.85, 2)

    return 0.0


async def load_shopify_products_for_project(
    session: AsyncSession, project_id: UUID
) -> list[ShopifyProduct]:
    store = await get_shopify_store_for_project(project_id, session)
    if store is None:
        return []
    result = await session.execute(
        select(ShopifyProduct)
        .where(ShopifyProduct.shopify_store_id == store.id)
        .order_by(ShopifyProduct.title.asc())
    )
    return list(result.scalars().all())


async def suggest_shopify_matches(
    session: AsyncSession,
    project_id: UUID,
    proposals: list[BrandProductKnowledgeItemProposal],
) -> None:
    products = await load_shopify_products_for_project(session, project_id)
    if not products:
        return

    for proposal in proposals:
        best_score = 0.0
        best_product: ShopifyProduct | None = None
        for product in products:
            score = score_shopify_match(proposal.product_name, product)
            if score > best_score:
                best_score = score
                best_product = product

        if best_product is not None and best_score >= _MATCH_THRESHOLD:
            proposal.suggested_shopify_product_id = best_product.id
            proposal.suggested_shopify_title = best_product.title
            proposal.suggested_shopify_handle = best_product.handle
            proposal.shopify_match_confidence = best_score
