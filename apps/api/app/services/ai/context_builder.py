"""Compact brand context builder for AI tasks."""

from __future__ import annotations

import hashlib
from enum import Enum
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.brand_intelligence.context import BrandIntelligenceContextBuilder
from app.services.brand_intelligence.product_knowledge_context import (
    get_product_knowledge_prompt_for_entity,
)
from app.services.brand_intelligence.safe_claims_service import safe_claims_completion


class AiTaskType(str, Enum):
    PRODUCT_SEO_FIELD = "product_seo_field"
    PRODUCT_SEO_ALT = "product_seo_alt"
    PRODUCT_SEO_PROPOSAL = "product_seo_proposal"
    COLLECTION_SEO_FIELD = "collection_seo_field"
    COLLECTION_SEO_PROPOSAL = "collection_seo_proposal"
    BLOG_BRIEF = "blog_brief"
    ARTICLE_GENERATOR = "article_generator"
    BRAND_INTELLIGENCE_IMPORT = "brand_intelligence_import"


def _hash_context(text: str | None) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()[:16]


def build_prompt_cache_key(
    project_id: UUID,
    module: str,
    context_hash: str,
) -> str:
    return f"project:{project_id}:ctx:{context_hash}:module:{module}"


def _compact_blocks(bundle) -> dict[str, str | None]:
    pc = bundle.prompt_context
    if not pc:
        return {}
    return {
        "profile": pc.brand_profile,
        "identity": pc.brand_identity,
        "safe_claims": pc.safe_claims,
        "product_knowledge": pc.product_knowledge,
        "faq": pc.faq_objections,
        "editorial": pc.editorial_guidelines,
        "full": pc.full_text,
    }


def _join_blocks(blocks: list[str | None]) -> str | None:
    parts = [b.strip() for b in blocks if b and b.strip()]
    return "\n\n".join(parts) if parts else None


async def build_ai_context_for_task(
    session: AsyncSession,
    project_id: UUID,
    task_type: AiTaskType,
    *,
    shopify_product_id: str | None = None,
    brief_payload: dict[str, Any] | None = None,
) -> tuple[str | None, str]:
    bundle = await BrandIntelligenceContextBuilder.build_brand_context(session, project_id)
    if bundle.primary_source == "minimal":
        return None, _hash_context(None)

    blocks = _compact_blocks(bundle)
    text: str | None = None

    if task_type in (
        AiTaskType.PRODUCT_SEO_FIELD,
        AiTaskType.PRODUCT_SEO_ALT,
        AiTaskType.COLLECTION_SEO_FIELD,
    ):
        text = _join_blocks([blocks.get("profile"), blocks.get("identity"), blocks.get("safe_claims")])
        if shopify_product_id and task_type != AiTaskType.COLLECTION_SEO_FIELD:
            pk = await get_product_knowledge_prompt_for_entity(
                session, project_id, shopify_product_id=shopify_product_id
            )
            if pk:
                text = f"{text}\n\n{pk}" if text else pk
    elif task_type == AiTaskType.PRODUCT_SEO_PROPOSAL:
        text = _join_blocks(
            [
                blocks.get("profile"),
                blocks.get("identity"),
                blocks.get("safe_claims"),
                blocks.get("product_knowledge"),
            ]
        )
        if shopify_product_id:
            pk = await get_product_knowledge_prompt_for_entity(
                session, project_id, shopify_product_id=shopify_product_id
            )
            if pk:
                text = f"{text}\n\n{pk}" if text else pk
    elif task_type == AiTaskType.COLLECTION_SEO_PROPOSAL:
        text = _join_blocks(
            [blocks.get("profile"), blocks.get("identity"), blocks.get("safe_claims")]
        )
    elif task_type == AiTaskType.BLOG_BRIEF:
        text = blocks.get("full") or BrandIntelligenceContextBuilder.format_for_prompt(bundle)
        if shopify_product_id:
            pk = await get_product_knowledge_prompt_for_entity(
                session, project_id, shopify_product_id=shopify_product_id
            )
            if pk:
                text = f"{text}\n\n{pk}" if text else pk
    elif task_type == AiTaskType.ARTICLE_GENERATOR:
        article_blocks: list[str | None] = [
            blocks.get("profile"),
            blocks.get("identity"),
            blocks.get("safe_claims"),
            blocks.get("faq"),
            blocks.get("editorial"),
        ]
        if brief_payload:
            title = str(brief_payload.get("proposedTitle") or "").strip()
            keyword = str(brief_payload.get("primaryKeyword") or "").strip()
            if title or keyword:
                article_blocks.append(f"BRIEF APPROVATO\n- Titolo: {title}\n- Keyword: {keyword}")
        text = _join_blocks(article_blocks)
        if shopify_product_id:
            pk = await get_product_knowledge_prompt_for_entity(
                session, project_id, shopify_product_id=shopify_product_id
            )
            if pk:
                text = f"{text}\n\n{pk}" if text else pk
    elif task_type == AiTaskType.BRAND_INTELLIGENCE_IMPORT:
        if bundle.safe_claims and safe_claims_completion(bundle.safe_claims) != "empty":
            text = blocks.get("safe_claims")
        else:
            text = blocks.get("profile")
    else:
        text = blocks.get("full") or BrandIntelligenceContextBuilder.format_for_prompt(bundle)

    return text, _hash_context(text)
