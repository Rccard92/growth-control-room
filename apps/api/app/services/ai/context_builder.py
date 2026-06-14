"""Compact brand context builder for AI tasks (shim → context_profiles)."""

from __future__ import annotations

from enum import Enum
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai.context_profiles import (
    AiContextProfile,
    build_context_for_profile,
    build_prompt_cache_key,
)

__all__ = [
    "AiTaskType",
    "build_ai_context_for_task",
    "build_prompt_cache_key",
]


class AiTaskType(str, Enum):

    PRODUCT_SEO_FIELD = "product_seo_field"
    PRODUCT_SEO_ALT = "product_seo_alt"
    PRODUCT_SEO_PROPOSAL = "product_seo_proposal"
    COLLECTION_SEO_FIELD = "collection_seo_field"
    COLLECTION_SEO_PROPOSAL = "collection_seo_proposal"
    BLOG_BRIEF = "blog_brief"
    ARTICLE_GENERATOR = "article_generator"
    BRAND_INTELLIGENCE_IMPORT = "brand_intelligence_import"


_TASK_TO_PROFILE: dict[AiTaskType, AiContextProfile] = {
    AiTaskType.PRODUCT_SEO_FIELD: AiContextProfile.PRODUCT_SEO_FIELD,
    AiTaskType.PRODUCT_SEO_ALT: AiContextProfile.IMAGE_ALT,
    AiTaskType.PRODUCT_SEO_PROPOSAL: AiContextProfile.PRODUCT_SEO_FULL,
    AiTaskType.COLLECTION_SEO_FIELD: AiContextProfile.COLLECTION_SEO_FIELD,
    AiTaskType.COLLECTION_SEO_PROPOSAL: AiContextProfile.COLLECTION_SEO_FULL,
    AiTaskType.BLOG_BRIEF: AiContextProfile.BLOG_BRIEF,
    AiTaskType.ARTICLE_GENERATOR: AiContextProfile.ARTICLE_DRAFT,
    AiTaskType.BRAND_INTELLIGENCE_IMPORT: AiContextProfile.BRAND_IMPORT,
}


async def build_ai_context_for_task(
    session: AsyncSession,
    project_id: UUID,
    task_type: AiTaskType,
    *,
    shopify_product_id: str | None = None,
    brief_payload: dict[str, Any] | None = None,
) -> tuple[str | None, str]:
    """Deprecated shim — prefer build_context_for_profile()."""
    profile = _TASK_TO_PROFILE.get(task_type, AiContextProfile.GENERIC)
    options: dict[str, Any] = {}
    entity_type: str | None = None
    entity_id: str | None = None

    if shopify_product_id:
        options["shopify_product_id"] = shopify_product_id
        entity_type = "product"
        entity_id = shopify_product_id
    if brief_payload:
        options["brief_payload"] = brief_payload

    result = await build_context_for_profile(
        session,
        project_id,
        profile,
        entity_type=entity_type,
        entity_id=entity_id,
        options=options or None,
    )
    text = result.context_text if result.context_text else None
    return text, result.context_hash
