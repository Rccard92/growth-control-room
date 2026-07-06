"""DataForSEO Cost Sandbox API routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.schemas.dataforseo import (
    DataForSeoEstimateRequest,
    DataForSeoEstimateResponse,
    DataForSeoEstimatedCalls,
    DataForSeoStatusResponse,
    DataForSeoTestRequest,
    DataForSeoTestResponse,
    DataForSeoUsageLogRead,
    DataForSeoUsageResponse,
)
from app.services.dataforseo.dataforseo_budget import (
    get_dataforseo_usage_month,
    get_dataforseo_usage_today,
)
from app.services.dataforseo.dataforseo_client import get_dataforseo_account_status
from app.services.dataforseo.dataforseo_cost_estimator import estimate_dataforseo_cost
from app.services.dataforseo.dataforseo_sandbox_service import run_dataforseo_sandbox_test
from app.services.dataforseo.dataforseo_usage_service import (
    average_cost_by_operation,
    list_recent_dataforseo_logs,
)
from app.services.dataforseo.exceptions import (
    DataForSeoApiError,
    DataForSeoBudgetExceededError,
    DataForSeoNotConfiguredError,
    DataForSeoRealCallsDisabledError,
)
from app.services.projects import get_project_in_default_workspace

router = APIRouter(prefix="/projects", tags=["dataforseo"])


def _log_to_read(row) -> DataForSeoUsageLogRead:
    return DataForSeoUsageLogRead(
        id=row.id,
        endpoint=row.endpoint,
        operation=row.operation,
        status=row.status,
        cost_usd=float(row.cost_usd) if row.cost_usd is not None else None,
        items_count=row.items_count,
        metadata_json=row.metadata_json,
        response_summary=row.response_summary,
        error_message=row.error_message,
        created_at=row.created_at.isoformat() if row.created_at else "",
    )


@router.get(
    "/{project_id}/dataforseo/status",
    response_model=DataForSeoStatusResponse,
    response_model_by_alias=True,
)
async def get_dataforseo_status(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> DataForSeoStatusResponse:
    await get_project_in_default_workspace(project_id, session)

    account = None
    if settings.dataforseo_configured:
        try:
            account_status = await get_dataforseo_account_status()
            account = account_status.get("account")
        except DataForSeoApiError:
            account = None

    usage_today = await get_dataforseo_usage_today(session, project_id)
    usage_month = await get_dataforseo_usage_month(session, project_id)

    return DataForSeoStatusResponse(
        configured=settings.dataforseo_configured,
        real_calls_enabled=settings.dataforseo_enable_real_calls,
        missing_vars=settings.dataforseo_missing_vars,
        single_run_limit_usd=settings.dataforseo_single_run_limit_usd,
        daily_budget_usd=settings.dataforseo_daily_budget_usd,
        monthly_budget_usd=settings.dataforseo_monthly_budget_usd,
        usage_today_usd=float(usage_today),
        usage_month_usd=float(usage_month),
        account=account,
    )


@router.post(
    "/{project_id}/dataforseo/cost-sandbox/estimate",
    response_model=DataForSeoEstimateResponse,
    response_model_by_alias=True,
)
async def estimate_dataforseo_cost_endpoint(
    project_id: UUID,
    request: DataForSeoEstimateRequest,
    session: AsyncSession = Depends(get_db),
) -> DataForSeoEstimateResponse:
    await get_project_in_default_workspace(project_id, session)

    try:
        result = await estimate_dataforseo_cost(
            session,
            project_id=project_id,
            mode=request.mode,
            run_id=request.run_id,
            product_pages_count=request.product_pages_count,
            seed_queries_per_page=request.seed_queries_per_page,
            keyword_ideas_per_seed=request.keyword_ideas_per_seed,
            serp_queries_per_page=request.serp_queries_per_page,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    calls = result["estimatedCalls"]
    return DataForSeoEstimateResponse(
        mode=result["mode"],
        estimated_calls=DataForSeoEstimatedCalls(
            search_volume=calls["searchVolume"],
            keyword_ideas=calls["keywordIdeas"],
            serp=calls["serp"],
        ),
        estimated_cost_usd=result["estimatedCostUsd"],
        assumptions=result["assumptions"],
        budget_warnings=result.get("budgetWarnings", []),
        audit_context=result.get("auditContext"),
    )


@router.post(
    "/{project_id}/dataforseo/cost-sandbox/test",
    response_model=DataForSeoTestResponse,
    response_model_by_alias=True,
)
async def run_dataforseo_test_endpoint(
    project_id: UUID,
    request: DataForSeoTestRequest,
    session: AsyncSession = Depends(get_db),
) -> DataForSeoTestResponse:
    await get_project_in_default_workspace(project_id, session)

    try:
        result = await run_dataforseo_sandbox_test(
            session,
            project_id=project_id,
            test_type=request.test_type,
            keyword=request.keyword.strip(),
            location_code=request.location_code,
            language_code=request.language_code,
        )
    except DataForSeoRealCallsDisabledError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message) from exc
    except DataForSeoNotConfiguredError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=exc.message) from exc
    except DataForSeoBudgetExceededError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=exc.message) from exc
    except DataForSeoApiError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=exc.message,
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return DataForSeoTestResponse(
        test_type=result["testType"],
        keyword=result["keyword"],
        cost_usd=result["costUsd"],
        endpoints=result["endpoints"],
        response_summary=result.get("responseSummary"),
        raw_preview=result.get("rawPreview"),
    )


@router.get(
    "/{project_id}/dataforseo/usage",
    response_model=DataForSeoUsageResponse,
    response_model_by_alias=True,
)
async def get_dataforseo_usage_endpoint(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> DataForSeoUsageResponse:
    await get_project_in_default_workspace(project_id, session)

    logs = await list_recent_dataforseo_logs(session, project_id, limit=50)
    usage_today = await get_dataforseo_usage_today(session, project_id)
    usage_month = await get_dataforseo_usage_month(session, project_id)
    avg_by_operation = await average_cost_by_operation(session, project_id)

    return DataForSeoUsageResponse(
        logs=[_log_to_read(row) for row in logs],
        usage_today_usd=float(usage_today),
        usage_month_usd=float(usage_month),
        average_cost_by_operation=avg_by_operation,
    )
