"""Shared DataForSEO usage logging for paid API calls."""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.dataforseo.dataforseo_usage_service import (
    DataForSeoUsageLogInput,
    record_dataforseo_usage,
)


async def record_dataforseo_call(
    session: AsyncSession,
    *,
    project_id: UUID,
    endpoint: str,
    operation: str,
    request_hash: str,
    result: dict[str, Any],
    metadata: dict[str, Any],
    items_count: int | None = None,
    status: str = "success",
    error_message: str | None = None,
) -> Decimal:
    cost = result.get("cost_usd")
    cost_decimal = Decimal(str(cost)) if cost is not None else None
    summary = result.get("summary") or {}
    resolved_items_count = (
        items_count
        if items_count is not None
        else summary.get("keywordCount")
        or summary.get("itemsCount")
        or summary.get("ideasCount")
        or summary.get("resultCount")
    )
    await record_dataforseo_usage(
        session,
        DataForSeoUsageLogInput(
            project_id=project_id,
            endpoint=endpoint,
            operation=operation,
            status=status,
            request_hash=request_hash,
            cost_usd=cost_decimal,
            items_count=resolved_items_count,
            metadata_json=metadata,
            response_summary=summary if status == "success" else None,
            error_message=error_message,
        ),
    )
    return cost_decimal or Decimal("0")
