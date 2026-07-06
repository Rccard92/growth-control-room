"""DataForSEO budget guardrails."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.datetime import (
    day_start_utc_naive,
    month_start_utc_naive,
    utc_now_naive,
)
from app.services.dataforseo.exceptions import (
    DataForSeoBudgetExceededError,
    DataForSeoRealCallsDisabledError,
)
from app.services.dataforseo.dataforseo_usage_service import sum_dataforseo_usage


async def get_dataforseo_usage_today(session: AsyncSession, project_id: UUID) -> Decimal:
    today = utc_now_naive().date()
    return await sum_dataforseo_usage(
        session,
        project_id,
        since=day_start_utc_naive(today),
    )


async def get_dataforseo_usage_month(session: AsyncSession, project_id: UUID) -> Decimal:
    today = utc_now_naive().date()
    return await sum_dataforseo_usage(
        session,
        project_id,
        since=month_start_utc_naive(today),
    )


async def assert_dataforseo_budget_allows(
    session: AsyncSession,
    project_id: UUID,
    estimated_cost_usd: float,
) -> None:
    if not settings.dataforseo_enable_real_calls:
        raise DataForSeoRealCallsDisabledError("DataForSEO real calls disabled.")

    estimated = Decimal(str(estimated_cost_usd))
    single_limit = Decimal(str(settings.dataforseo_single_run_limit_usd))
    if estimated > single_limit:
        raise DataForSeoBudgetExceededError(
            f"Costo stimato ({estimated:.4f} USD) supera il limite singola run "
            f"({single_limit} USD)."
        )

    daily_budget = Decimal(str(settings.dataforseo_daily_budget_usd))
    daily_spent = await get_dataforseo_usage_today(session, project_id)
    if daily_spent + estimated > daily_budget:
        raise DataForSeoBudgetExceededError(
            f"Budget giornaliero DataForSEO superato "
            f"({daily_budget} USD, speso oggi {daily_spent:.4f} USD)."
        )

    monthly_budget = Decimal(str(settings.dataforseo_monthly_budget_usd))
    monthly_spent = await get_dataforseo_usage_month(session, project_id)
    if monthly_spent + estimated > monthly_budget:
        raise DataForSeoBudgetExceededError(
            f"Budget mensile DataForSEO superato "
            f"({monthly_budget} USD, speso nel mese {monthly_spent:.4f} USD)."
        )
