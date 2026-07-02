"""Multi-skill SEO Skill run orchestration and background processing."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_session_factory
from app.models.seo_skills import SeoSkillRun, SeoSkillRunResult
from app.schemas.seo_skills import SeoSkillCatalogItem, SeoSkillRunCreateRequest
from app.services.seo_skills.catalog_loader import get_seo_skill_by_key
from app.services.seo_skills.error_messages import humanize_skill_error
from app.services.seo_skills.exceptions import (
    SeoSkillRunError,
    SeoSkillRunnerError,
    SeoSkillRunValidationError,
)
from app.services.seo_skills.input_collector import SUPPORTED_TARGET_TYPES
from app.services.seo_skills.skill_runner import SUPPORTED_PROVIDERS, run_single_seo_skill

logger = logging.getLogger(__name__)

MAX_LIST_LIMIT = 100


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _validate_provider(provider: str) -> str:
    normalized = (provider or "").strip().lower()
    if normalized not in SUPPORTED_PROVIDERS:
        raise SeoSkillRunValidationError(f"Unsupported AI provider: {provider}")
    return normalized


def _validate_target(request: SeoSkillRunCreateRequest) -> str:
    target_type = (request.target_type or "").strip().lower()
    if target_type not in SUPPORTED_TARGET_TYPES:
        raise SeoSkillRunValidationError(
            f"Unsupported SEO skill target_type: {request.target_type}"
        )

    if target_type == "url" and not (request.url and request.url.strip()):
        raise SeoSkillRunValidationError("url is required for target_type=url")
    if target_type == "shopify_product" and request.target_id is None:
        raise SeoSkillRunValidationError("target_id is required for shopify_product")
    if target_type == "shopify_collection" and request.target_id is None:
        raise SeoSkillRunValidationError("target_id is required for shopify_collection")

    return target_type


def _validate_runnable_skill(skill_key: str) -> SeoSkillCatalogItem:
    skill = get_seo_skill_by_key(skill_key)
    if skill is None:
        raise SeoSkillRunValidationError(f"SEO skill is not runnable: {skill_key}")

    if not skill.enabled:
        raise SeoSkillRunValidationError(f"SEO skill is not runnable: {skill_key}")

    if skill.status != "available":
        raise SeoSkillRunValidationError(f"SEO skill is not runnable: {skill_key}")

    if skill.runtime != "prompt_only":
        raise SeoSkillRunValidationError(f"SEO skill is not runnable: {skill_key}")

    return skill


def _validate_create_request(request: SeoSkillRunCreateRequest) -> tuple[str, str, list[str]]:
    if not request.selected_skills:
        raise SeoSkillRunValidationError("At least one SEO skill must be selected")

    selected_skills = [skill.strip() for skill in request.selected_skills if skill.strip()]
    if not selected_skills:
        raise SeoSkillRunValidationError("At least one SEO skill must be selected")

    target_type = _validate_target(request)
    provider = _validate_provider(request.provider)

    for skill_key in selected_skills:
        _validate_runnable_skill(skill_key)

    return target_type, provider, selected_skills


def _progress_percent(completed_count: int, total_count: int) -> int:
    if total_count <= 0:
        return 0
    return min(100, round(completed_count / total_count * 100))


def _ordered_pending_results(run: SeoSkillRun) -> list[SeoSkillRunResult]:
    by_key = {result.skill_key: result for result in run.results}
    ordered: list[SeoSkillRunResult] = []
    for skill_key in run.selected_skills:
        result = by_key.get(skill_key)
        if result is not None and result.status == "pending":
            ordered.append(result)
    return ordered


def _summarize_run_error_message(results: list[SeoSkillRunResult]) -> str | None:
    failed = [result for result in results if result.status == "failed"]
    if not failed:
        return None
    if len(failed) == 1:
        return failed[0].error_message or "One SEO skill failed during the run."
    return f"{len(failed)} SEO skills failed during the run."


async def create_seo_skill_run(
    session: AsyncSession,
    project_id: UUID,
    request: SeoSkillRunCreateRequest,
) -> SeoSkillRun:
    target_type, provider, selected_skills = _validate_create_request(request)

    run = SeoSkillRun(
        project_id=project_id,
        target_type=target_type,
        target_id=request.target_id,
        url=request.url.strip() if request.url else None,
        provider=provider,
        selected_skills=selected_skills,
        status="pending",
        progress_percent=0,
    )
    session.add(run)
    await session.flush()

    for skill_key in selected_skills:
        session.add(
            SeoSkillRunResult(
                run_id=run.id,
                project_id=project_id,
                skill_key=skill_key,
                status="pending",
            )
        )

    await session.commit()
    await session.refresh(run, attribute_names=["results"])
    return run


async def get_seo_skill_run(
    session: AsyncSession,
    project_id: UUID,
    run_id: UUID,
) -> SeoSkillRun | None:
    result = await session.execute(
        select(SeoSkillRun)
        .where(
            SeoSkillRun.id == run_id,
            SeoSkillRun.project_id == project_id,
        )
        .options(selectinload(SeoSkillRun.results))
    )
    return result.scalar_one_or_none()


async def list_seo_skill_runs(
    session: AsyncSession,
    project_id: UUID,
    limit: int = 20,
) -> list[SeoSkillRun]:
    capped_limit = max(1, min(limit, MAX_LIST_LIMIT))
    result = await session.execute(
        select(SeoSkillRun)
        .where(SeoSkillRun.project_id == project_id)
        .order_by(SeoSkillRun.created_at.desc())
        .limit(capped_limit)
    )
    return list(result.scalars().all())


def schedule_seo_skill_run(run_id: UUID) -> None:
    logger.info("Scheduling SEO skill run %s", run_id)
    asyncio.create_task(process_seo_skill_run(run_id))


async def start_seo_skill_run(
    session: AsyncSession,
    project_id: UUID,
    request: SeoSkillRunCreateRequest,
) -> SeoSkillRun:
    run = await create_seo_skill_run(session, project_id, request)
    schedule_seo_skill_run(run.id)
    return run


async def process_seo_skill_run(run_id: UUID) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        run = (
            await session.execute(
                select(SeoSkillRun)
                .where(SeoSkillRun.id == run_id)
                .options(selectinload(SeoSkillRun.results))
            )
        ).scalar_one_or_none()

        if run is None:
            logger.error("SEO skill run %s not found", run_id)
            return

        if run.status != "pending":
            logger.info(
                "Skipping SEO skill run %s because status is %s",
                run_id,
                run.status,
            )
            return

        total_skills = len(run.selected_skills)
        if total_skills <= 0:
            run.status = "failed"
            run.error_message = "No SEO skills selected for this run."
            run.completed_at = _utcnow()
            run.progress_percent = 100
            await session.commit()
            return

        run.status = "running"
        run.started_at = _utcnow()
        run.progress_percent = 0
        await session.commit()

        completed_count = 0
        failed_count = 0

        for result in _ordered_pending_results(run):
            run.current_skill = result.skill_key
            result.status = "running"
            result.started_at = _utcnow()
            await session.commit()

            try:
                output = await run_single_seo_skill(
                    session=session,
                    project_id=run.project_id,
                    skill_key=result.skill_key,
                    target_type=run.target_type,
                    target_id=run.target_id,
                    url=run.url,
                    provider=run.provider,
                    run_id=run.id,
                )
            except (SeoSkillRunnerError, SeoSkillRunError, Exception) as exc:
                logger.warning(
                    "SEO skill run %s skill %s failed: %s",
                    run_id,
                    result.skill_key,
                    exc,
                )
                result.status = "failed"
                result.error_message = humanize_skill_error(exc, provider=run.provider)
                result.completed_at = _utcnow()
                failed_count += 1
            else:
                result.status = "completed"
                result.score = output.get("score")
                result.findings = output.get("findings")
                result.recommendations = output.get("recommendations")
                result.tasks = output.get("tasks")
                result.artifacts = output.get("artifacts")
                result.raw_output = output
                result.error_message = None
                result.completed_at = _utcnow()
                completed_count += 1

            processed_count = completed_count + failed_count
            run.progress_percent = _progress_percent(processed_count, total_skills)
            await session.commit()

        run.current_skill = None
        run.completed_at = _utcnow()
        run.progress_percent = 100

        if failed_count == 0:
            run.status = "completed"
            run.error_message = None
        elif completed_count == 0:
            run.status = "failed"
            run.error_message = _summarize_run_error_message(run.results)
        else:
            run.status = "partial_failed"
            run.error_message = _summarize_run_error_message(run.results)

        await session.commit()
