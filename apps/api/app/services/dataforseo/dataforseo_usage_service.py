"""DataForSEO usage logging and aggregation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.datetime import to_utc_naive
from app.models.data_provider_usage_log import DataProviderUsageLog


@dataclass
class DataForSeoUsageLogInput:
    project_id: UUID | None
    endpoint: str
    operation: str
    status: str
    request_hash: str | None = None
    cost_usd: Decimal | None = None
    credits_used: Decimal | None = None
    items_count: int | None = None
    metadata_json: dict[str, Any] | None = None
    response_summary: dict[str, Any] | None = None
    error_message: str | None = None
    provider: str = "dataforseo"


async def record_dataforseo_usage(
    session: AsyncSession,
    data: DataForSeoUsageLogInput,
) -> DataProviderUsageLog:
    row = DataProviderUsageLog(
        project_id=data.project_id,
        provider=data.provider,
        endpoint=data.endpoint,
        operation=data.operation,
        request_hash=data.request_hash,
        status=data.status,
        cost_usd=data.cost_usd,
        credits_used=data.credits_used,
        items_count=data.items_count,
        metadata_json=data.metadata_json,
        response_summary=data.response_summary,
        error_message=data.error_message,
    )
    session.add(row)
    await session.flush()
    return row


async def sum_dataforseo_usage(
    session: AsyncSession,
    project_id: UUID,
    *,
    since: datetime,
) -> Decimal:
    since_naive = to_utc_naive(since)
    assert since_naive is not None
    result = await session.execute(
        select(func.coalesce(func.sum(DataProviderUsageLog.cost_usd), 0)).where(
            DataProviderUsageLog.project_id == project_id,
            DataProviderUsageLog.provider == "dataforseo",
            DataProviderUsageLog.created_at >= since_naive,
            DataProviderUsageLog.status == "success",
        )
    )
    value = result.scalar_one()
    return Decimal(str(value)) if value is not None else Decimal("0")


async def list_recent_dataforseo_logs(
    session: AsyncSession,
    project_id: UUID,
    *,
    limit: int = 50,
) -> list[DataProviderUsageLog]:
    result = await session.execute(
        select(DataProviderUsageLog)
        .where(
            DataProviderUsageLog.project_id == project_id,
            DataProviderUsageLog.provider == "dataforseo",
        )
        .order_by(DataProviderUsageLog.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


_OBSERVED_OPERATIONS = (
    "search_volume",
    "search_volume_batch",
    "keyword_ideas",
    "serp",
)


async def observed_unit_costs(
    session: AsyncSession,
    project_id: UUID,
) -> dict[str, float | None]:
    result = await session.execute(
        select(
            DataProviderUsageLog.operation,
            func.avg(
                DataProviderUsageLog.cost_usd / func.nullif(DataProviderUsageLog.items_count, 0)
            ),
            func.avg(DataProviderUsageLog.cost_usd),
        )
        .where(
            DataProviderUsageLog.project_id == project_id,
            DataProviderUsageLog.provider == "dataforseo",
            DataProviderUsageLog.status == "success",
            DataProviderUsageLog.cost_usd.is_not(None),
            DataProviderUsageLog.operation.in_(_OBSERVED_OPERATIONS),
        )
        .group_by(DataProviderUsageLog.operation)
    )

    costs: dict[str, float | None] = {op: None for op in _OBSERVED_OPERATIONS}
    for operation, avg_per_item, avg_total in result.all():
        op = str(operation)
        if avg_per_item is not None:
            costs[op] = float(avg_per_item)
        elif avg_total is not None:
            costs[op] = float(avg_total)
    return costs


async def average_cost_by_operation(
    session: AsyncSession,
    project_id: UUID,
) -> dict[str, float]:
    result = await session.execute(
        select(
            DataProviderUsageLog.operation,
            func.avg(DataProviderUsageLog.cost_usd),
        )
        .where(
            DataProviderUsageLog.project_id == project_id,
            DataProviderUsageLog.provider == "dataforseo",
            DataProviderUsageLog.status == "success",
            DataProviderUsageLog.cost_usd.is_not(None),
        )
        .group_by(DataProviderUsageLog.operation)
    )
    return {
        str(operation): float(avg) if avg is not None else 0.0
        for operation, avg in result.all()
    }
