"""Editorial item AI usage lookup from AiUsageLog."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_usage_log import AiUsageLog
from app.schemas.content_seo_editorial import (
    EditorialAiGenerationInfo,
    EditorialItemAiUsageResponse,
)

BRIEF_OPERATION_KEYS = ("blog_brief_generation", "blog_brief_batch_item")
ARTICLE_OPERATION_KEYS = ("article_draft_generation",)
IMAGE_OPERATION_KEYS = ("editorial_image_generation", "editorial_image_edit")
EDITORIAL_GENERATOR_VERSION = "0.5.14-alpha"


def build_ai_generation_snapshot_from_log(log: AiUsageLog) -> dict:
    """Build payload aiGeneration snapshot from a usage log row."""
    cost = log.estimated_total_cost
    return {
        "model": log.model,
        "model_tier": log.model_tier or "",
        "operation_key": log.operation_key or "",
        "context_profile": log.context_profile or "",
        "estimated_total_cost": float(cost) if cost is not None else None,
        "input_tokens": log.input_tokens,
        "output_tokens": log.output_tokens,
        "generated_at": log.created_at.isoformat() if log.created_at else "",
        "generator_version": EDITORIAL_GENERATOR_VERSION,
        "log_id": str(log.id),
        "status": log.status,
        "context_hash": log.context_hash or "",
        "prompt_hash": log.prompt_hash or "",
    }


def _log_to_info(log: AiUsageLog | None) -> EditorialAiGenerationInfo | None:
    if log is None:
        return None
    cost = log.estimated_total_cost
    return EditorialAiGenerationInfo(
        generated=log.status == "success",
        model=log.model,
        model_tier=log.model_tier,
        operation_key=log.operation_key,
        context_profile=log.context_profile,
        estimated_total_cost=float(cost) if cost is not None else None,
        input_tokens=log.input_tokens,
        output_tokens=log.output_tokens,
        created_at=log.created_at.isoformat() if log.created_at else None,
        status=log.status,
        error_message=log.error_message,
        generator_version=EDITORIAL_GENERATOR_VERSION,
        log_id=str(log.id),
        context_hash=log.context_hash,
        prompt_hash=log.prompt_hash,
    )


async def _fetch_latest_log(
    session: AsyncSession,
    project_id: UUID,
    entity_id: str,
    operation_keys: tuple[str, ...],
    *,
    prefer_success: bool = True,
) -> AiUsageLog | None:
    base = (
        select(AiUsageLog)
        .where(
            AiUsageLog.project_id == project_id,
            AiUsageLog.entity_type == "editorial_item",
            AiUsageLog.entity_id == entity_id,
            AiUsageLog.operation_key.in_(operation_keys),
        )
        .order_by(AiUsageLog.created_at.desc())
    )
    if prefer_success:
        success = (
            await session.execute(base.where(AiUsageLog.status == "success").limit(1))
        ).scalar_one_or_none()
        if success is not None:
            return success
    return (await session.execute(base.limit(1))).scalar_one_or_none()


async def fetch_latest_editorial_ai_log(
    session: AsyncSession,
    project_id: UUID,
    item_id: UUID,
    operation_keys: tuple[str, ...],
) -> AiUsageLog | None:
    return await _fetch_latest_log(
        session,
        project_id,
        str(item_id),
        operation_keys,
    )


async def get_editorial_item_ai_usage(
    session: AsyncSession,
    project_id: UUID,
    item_id: UUID,
) -> EditorialItemAiUsageResponse:
    entity_id = str(item_id)
    brief_log = await _fetch_latest_log(session, project_id, entity_id, BRIEF_OPERATION_KEYS)
    article_log = await _fetch_latest_log(session, project_id, entity_id, ARTICLE_OPERATION_KEYS)
    image_log = await _fetch_latest_log(session, project_id, entity_id, IMAGE_OPERATION_KEYS)

    all_keys = (*BRIEF_OPERATION_KEYS, *ARTICLE_OPERATION_KEYS, *IMAGE_OPERATION_KEYS)
    logs_stmt = (
        select(AiUsageLog)
        .where(
            AiUsageLog.project_id == project_id,
            AiUsageLog.entity_type == "editorial_item",
            AiUsageLog.entity_id == entity_id,
            AiUsageLog.operation_key.in_(all_keys),
        )
        .order_by(AiUsageLog.created_at.desc())
        .limit(20)
    )
    log_rows = list((await session.execute(logs_stmt)).scalars().all())

    return EditorialItemAiUsageResponse(
        brief=_log_to_info(brief_log),
        article=_log_to_info(article_log),
        image=_log_to_info(image_log),
        logs=[
            EditorialAiGenerationInfo(
                generated=row.status == "success",
                model=row.model,
                model_tier=row.model_tier,
                operation_key=row.operation_key,
                context_profile=row.context_profile,
                estimated_total_cost=(
                    float(row.estimated_total_cost)
                    if row.estimated_total_cost is not None
                    else None
                ),
                input_tokens=row.input_tokens,
                output_tokens=row.output_tokens,
                created_at=row.created_at.isoformat() if row.created_at else None,
                status=row.status,
                error_message=row.error_message,
                generator_version=EDITORIAL_GENERATOR_VERSION,
                log_id=str(row.id),
                context_hash=row.context_hash,
                prompt_hash=row.prompt_hash,
            )
            for row in log_rows
        ],
    )
