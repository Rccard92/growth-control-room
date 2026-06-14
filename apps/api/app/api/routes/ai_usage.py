"""AI usage API routes."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.ai_usage import (
    AiBudgetStatusResponse,
    AiRoutingInsights,
    AiUsageBreakdownItem,
    AiUsageEstimateResponse,
    AiUsageLogListResponse,
    AiUsageLogRead,
    AiUsageSummaryResponse,
)
from app.services.ai.usage_service import (
    estimate_operation_cost,
    get_budget_status,
    get_global_usage_summary,
    get_usage_log,
    get_usage_summary,
    list_usage_logs,
)
from app.services.projects import get_project_in_default_workspace

router = APIRouter(prefix="/projects", tags=["ai-usage"])
global_router = APIRouter(tags=["ai-usage"])


def _to_summary_response(data: dict) -> AiUsageSummaryResponse:
    def breakdown(items: list[dict], *, use_date: bool = False) -> list[AiUsageBreakdownItem]:
        result: list[AiUsageBreakdownItem] = []
        for item in items:
            result.append(
                AiUsageBreakdownItem(
                    key=None if use_date else item.get("key"),
                    date=item.get("date") if use_date else None,
                    requests=item["requests"],
                    estimated_cost=item["estimatedCost"],
                    input_tokens=item.get("inputTokens"),
                )
            )
        return result

    return AiUsageSummaryResponse(
        total_estimated_cost=data["totalEstimatedCost"],
        total_requests=data["totalRequests"],
        successful_requests=data["successfulRequests"],
        failed_requests=data["failedRequests"],
        total_input_tokens=data["totalInputTokens"],
        total_output_tokens=data["totalOutputTokens"],
        total_cached_input_tokens=data["totalCachedInputTokens"],
        by_module=breakdown(data["byModule"]),
        by_operation=breakdown(data["byOperation"]),
        by_model=breakdown(data["byModel"]),
        by_tier=breakdown(data.get("byTier", [])),
        by_day=breakdown(data["byDay"], use_date=True),
        routing_insights=(
            AiRoutingInsights(**data["routingInsights"])
            if data.get("routingInsights")
            else None
        ),
        project_count=data.get("projectCount"),
    )


def _log_to_read(row) -> AiUsageLogRead:
    return AiUsageLogRead(
        id=row.id,
        project_id=row.project_id,
        provider=row.provider,
        model=row.model,
        module=row.module,
        operation=row.operation,
        entity_type=row.entity_type,
        entity_id=row.entity_id,
        job_id=row.job_id,
        status=row.status,
        input_tokens=row.input_tokens,
        output_tokens=row.output_tokens,
        total_tokens=row.total_tokens,
        cached_input_tokens=row.cached_input_tokens,
        reasoning_tokens=row.reasoning_tokens,
        estimated_input_cost=float(row.estimated_input_cost) if row.estimated_input_cost is not None else None,
        estimated_output_cost=float(row.estimated_output_cost) if row.estimated_output_cost is not None else None,
        estimated_cached_cost=float(row.estimated_cached_cost) if row.estimated_cached_cost is not None else None,
        estimated_total_cost=float(row.estimated_total_cost) if row.estimated_total_cost is not None else None,
        duration_ms=row.duration_ms,
        prompt_chars=row.prompt_chars,
        output_chars=row.output_chars,
        prompt_hash=row.prompt_hash,
        prompt_preview=row.prompt_preview,
        output_preview=row.output_preview,
        prompt_cache_key=row.prompt_cache_key,
        context_profile=row.context_profile,
        context_hash=row.context_hash,
        context_chars=row.context_chars,
        context_blocks_used=row.context_blocks_used,
        model_tier=row.model_tier,
        model_policy_source=row.model_policy_source,
        requested_model=row.requested_model,
        max_output_tokens=row.max_output_tokens,
        temperature=float(row.temperature) if row.temperature is not None else None,
        reasoning_effort=row.reasoning_effort,
        response_id=row.response_id,
        error_type=row.error_type,
        error_message=row.error_message,
        created_at=row.created_at,
    )


@router.get(
    "/{project_id}/ai-usage/summary",
    response_model=AiUsageSummaryResponse,
    response_model_by_alias=True,
)
async def project_ai_usage_summary(
    project_id: UUID,
    start_date: date | None = Query(default=None, alias="startDate"),
    end_date: date | None = Query(default=None, alias="endDate"),
    module: str | None = None,
    operation: str | None = None,
    model: str | None = None,
    model_tier: str | None = Query(default=None, alias="modelTier"),
    session: AsyncSession = Depends(get_db),
) -> AiUsageSummaryResponse:
    await get_project_in_default_workspace(project_id, session)
    data = await get_usage_summary(
        session,
        project_id,
        start_date=start_date,
        end_date=end_date,
        module=module,
        operation=operation,
        model=model,
        model_tier=model_tier,
    )
    return _to_summary_response(data)


@router.get(
    "/{project_id}/ai-usage/logs",
    response_model=AiUsageLogListResponse,
    response_model_by_alias=True,
)
async def project_ai_usage_logs(
    project_id: UUID,
    start_date: date | None = Query(default=None, alias="startDate"),
    end_date: date | None = Query(default=None, alias="endDate"),
    module: str | None = None,
    operation: str | None = None,
    model: str | None = None,
    model_tier: str | None = Query(default=None, alias="modelTier"),
    status: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db),
) -> AiUsageLogListResponse:
    await get_project_in_default_workspace(project_id, session)
    rows, total = await list_usage_logs(
        session,
        project_id,
        start_date=start_date,
        end_date=end_date,
        module=module,
        operation=operation,
        model=model,
        model_tier=model_tier,
        status=status,
        limit=limit,
        offset=offset,
    )
    return AiUsageLogListResponse(
        items=[_log_to_read(r) for r in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{project_id}/ai-usage/logs/{log_id}",
    response_model=AiUsageLogRead,
    response_model_by_alias=True,
)
async def project_ai_usage_log_detail(
    project_id: UUID,
    log_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> AiUsageLogRead:
    await get_project_in_default_workspace(project_id, session)
    row = await get_usage_log(session, project_id, log_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log AI non trovato.")
    return _log_to_read(row)


@router.get(
    "/{project_id}/ai-usage/budget-status",
    response_model=AiBudgetStatusResponse,
    response_model_by_alias=True,
)
async def project_ai_budget_status(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> AiBudgetStatusResponse:
    await get_project_in_default_workspace(project_id, session)
    data = await get_budget_status(session, project_id)
    return AiBudgetStatusResponse(
        daily_spent=data["dailySpent"],
        monthly_spent=data["monthlySpent"],
        daily_budget_usd=data["dailyBudgetUsd"],
        monthly_budget_usd=data["monthlyBudgetUsd"],
        near_limit=data["nearLimit"],
        blocked=data["blocked"],
    )


@router.get(
    "/{project_id}/ai-usage/estimate",
    response_model=AiUsageEstimateResponse,
    response_model_by_alias=True,
)
async def project_ai_usage_estimate(
    project_id: UUID,
    operation: str = Query(...),
    count: int = Query(default=1, ge=1, le=500),
    session: AsyncSession = Depends(get_db),
) -> AiUsageEstimateResponse:
    await get_project_in_default_workspace(project_id, session)
    data = await estimate_operation_cost(session, project_id, operation=operation, count=count)
    return AiUsageEstimateResponse(
        operation=data["operation"],
        count=data["count"],
        estimated_total_cost=data["estimatedTotalCost"],
        avg_cost_per_request=data["avgCostPerRequest"],
        based_on_requests=data["basedOnRequests"],
        message=data["message"],
    )


@global_router.get(
    "/ai-usage/summary",
    response_model=AiUsageSummaryResponse,
    response_model_by_alias=True,
)
async def global_ai_usage_summary(
    start_date: date | None = Query(default=None, alias="startDate"),
    end_date: date | None = Query(default=None, alias="endDate"),
    session: AsyncSession = Depends(get_db),
) -> AiUsageSummaryResponse:
    data = await get_global_usage_summary(
        session,
        start_date=start_date,
        end_date=end_date,
    )
    return _to_summary_response(data)
