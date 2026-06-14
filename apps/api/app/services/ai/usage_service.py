"""AI usage logging, aggregation, budget checks."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.datetime import (
    day_end_exclusive_utc_naive,
    day_start_utc_naive,
    month_start_utc_naive,
    to_utc_naive,
    utc_now_naive,
)
from app.models.ai_usage_log import AiUsageLog
from app.models.project import Project
from app.services.ai.model_policy import CHEAP_CONTEXT_PROFILES, AiModelTier, tier_to_model_name
from app.services.workspace import get_default_workspace

PREVIEW_MAX_LEN = 500


@dataclass
class UsageLogInput:
    project_id: UUID | None
    model: str
    module: str
    operation: str
    status: str
    entity_type: str | None = None
    entity_id: str | None = None
    job_id: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cached_input_tokens: int = 0
    reasoning_tokens: int = 0
    estimated_input_cost: Decimal | None = None
    estimated_output_cost: Decimal | None = None
    estimated_cached_cost: Decimal | None = None
    estimated_total_cost: Decimal | None = None
    duration_ms: int | None = None
    prompt_chars: int | None = None
    output_chars: int | None = None
    prompt_hash: str | None = None
    prompt_preview: str | None = None
    output_preview: str | None = None
    prompt_cache_key: str | None = None
    context_profile: str | None = None
    context_hash: str | None = None
    context_chars: int | None = None
    context_blocks_used: list[str] | None = None
    operation_key: str | None = None
    model_tier: str | None = None
    model_policy_source: str | None = None
    requested_model: str | None = None
    max_output_tokens: int | None = None
    temperature: Decimal | None = None
    reasoning_effort: str | None = None
    response_id: str | None = None
    error_type: str | None = None
    error_message: str | None = None
    provider: str = "openai"


def truncate_preview(text: str | None, *, max_len: int = PREVIEW_MAX_LEN) -> str | None:
    if not text:
        return None
    cleaned = text.strip()
    if not cleaned:
        return None
    if len(cleaned) <= max_len:
        return cleaned
    return cleaned[: max_len - 1] + "…"


async def record_usage_log(session: AsyncSession, data: UsageLogInput) -> AiUsageLog:
    row = AiUsageLog(
        project_id=data.project_id,
        provider=data.provider,
        model=data.model,
        module=data.module,
        operation=data.operation,
        entity_type=data.entity_type,
        entity_id=data.entity_id,
        job_id=data.job_id,
        status=data.status,
        input_tokens=data.input_tokens,
        output_tokens=data.output_tokens,
        total_tokens=data.total_tokens,
        cached_input_tokens=data.cached_input_tokens,
        reasoning_tokens=data.reasoning_tokens,
        estimated_input_cost=data.estimated_input_cost,
        estimated_output_cost=data.estimated_output_cost,
        estimated_cached_cost=data.estimated_cached_cost,
        estimated_total_cost=data.estimated_total_cost,
        duration_ms=data.duration_ms,
        prompt_chars=data.prompt_chars,
        output_chars=data.output_chars,
        prompt_hash=data.prompt_hash,
        prompt_preview=truncate_preview(data.prompt_preview),
        output_preview=truncate_preview(data.output_preview),
        prompt_cache_key=data.prompt_cache_key,
        context_profile=data.context_profile,
        context_hash=data.context_hash,
        context_chars=data.context_chars,
        context_blocks_used=data.context_blocks_used,
        operation_key=data.operation_key,
        model_tier=data.model_tier,
        model_policy_source=data.model_policy_source,
        requested_model=data.requested_model,
        max_output_tokens=data.max_output_tokens,
        temperature=data.temperature,
        reasoning_effort=data.reasoning_effort,
        response_id=data.response_id,
        error_type=data.error_type,
        error_message=truncate_preview(data.error_message, max_len=1000),
    )
    session.add(row)
    await session.flush()
    return row


async def sum_project_spend(
    session: AsyncSession,
    project_id: UUID,
    *,
    since: datetime,
) -> Decimal:
    since_naive = to_utc_naive(since)
    assert since_naive is not None
    result = await session.execute(
        select(func.coalesce(func.sum(AiUsageLog.estimated_total_cost), 0)).where(
            AiUsageLog.project_id == project_id,
            AiUsageLog.created_at >= since_naive,
            AiUsageLog.status == "success",
        )
    )
    value = result.scalar_one()
    return Decimal(str(value)) if value is not None else Decimal("0")


from app.services.ai.exceptions import AiBudgetExceededError, AiSingleRequestBlockedError


async def check_budget_before_request(session: AsyncSession, project_id: UUID) -> None:
    today = utc_now_naive().date()
    if settings.ai_daily_budget_usd and settings.ai_daily_budget_usd > 0:
        daily_spent = await sum_project_spend(
            session, project_id, since=day_start_utc_naive(today)
        )
        if daily_spent >= Decimal(str(settings.ai_daily_budget_usd)):
            raise AiBudgetExceededError(
                f"Budget AI giornaliero superato ({settings.ai_daily_budget_usd} USD). "
                "Nuove generazioni AI sono bloccate fino a domani."
            )

    if settings.ai_monthly_budget_usd and settings.ai_monthly_budget_usd > 0:
        monthly_spent = await sum_project_spend(
            session, project_id, since=month_start_utc_naive(today)
        )
        if monthly_spent >= Decimal(str(settings.ai_monthly_budget_usd)):
            raise AiBudgetExceededError(
                f"Budget AI mensile superato ({settings.ai_monthly_budget_usd} USD). "
                "Nuove generazioni AI sono bloccate fino al prossimo mese."
            )


def check_single_request_cost(estimated_total: Decimal | None) -> None:
    if estimated_total is None:
        return
    block = settings.ai_single_request_block_usd
    if block and block > 0 and estimated_total >= Decimal(str(block)):
        raise AiSingleRequestBlockedError(
            f"Costo stimato richiesta ({estimated_total:.4f} USD) supera il limite "
            f"({block} USD)."
        )


def _apply_log_filters(
    stmt,
    *,
    project_id: UUID | None,
    start_date: date | None,
    end_date: date | None,
    module: str | None,
    operation: str | None,
    model: str | None,
    model_tier: str | None,
    operation_key: str | None,
    status: str | None,
):
    if project_id is not None:
        stmt = stmt.where(AiUsageLog.project_id == project_id)
    if start_date:
        stmt = stmt.where(AiUsageLog.created_at >= day_start_utc_naive(start_date))
    if end_date:
        stmt = stmt.where(AiUsageLog.created_at < day_end_exclusive_utc_naive(end_date))
    if module:
        stmt = stmt.where(AiUsageLog.module == module)
    if operation:
        stmt = stmt.where(AiUsageLog.operation == operation)
    if model:
        stmt = stmt.where(AiUsageLog.model == model)
    if model_tier:
        stmt = stmt.where(AiUsageLog.model_tier == model_tier)
    if operation_key:
        stmt = stmt.where(AiUsageLog.operation_key == operation_key)
    if status:
        stmt = stmt.where(AiUsageLog.status == status)
    return stmt


def _compute_routing_insights(rows: list[AiUsageLog], by_tier: dict[str, dict[str, Any]]) -> dict[str, Any]:
    cost_by_tier = {key: item["estimatedCost"] for key, item in by_tier.items()}
    requests_by_tier = {key: item["requests"] for key, item in by_tier.items()}
    premium_on_cheap = sum(
        1
        for row in rows
        if row.model_tier == AiModelTier.PREMIUM.value
        and row.context_profile in CHEAP_CONTEXT_PROFILES
    )
    explicit_override = sum(
        1 for row in rows if row.model_policy_source == "explicit_override"
    )
    schema_fallback = sum(
        1 for row in rows if row.model_policy_source == "schema_fallback_retry"
    )
    unconfigured: list[str] = []
    for tier in (
        AiModelTier.CHEAP,
        AiModelTier.STANDARD,
        AiModelTier.PREMIUM,
        AiModelTier.FALLBACK,
    ):
        if tier_to_model_name(tier) is None:
            unconfigured.append(tier.value)
    return {
        "cost_by_tier": cost_by_tier,
        "requests_by_tier": requests_by_tier,
        "premium_on_cheap_profile_count": premium_on_cheap,
        "explicit_override_count": explicit_override,
        "unconfigured_model_warnings": unconfigured,
        "schema_fallback_retry_count": schema_fallback,
    }


async def get_usage_summary(
    session: AsyncSession,
    project_id: UUID,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
    module: str | None = None,
    operation: str | None = None,
    model: str | None = None,
    model_tier: str | None = None,
    operation_key: str | None = None,
) -> dict[str, Any]:
    base = select(AiUsageLog).where(AiUsageLog.project_id == project_id)
    base = _apply_log_filters(
        base,
        project_id=None,
        start_date=start_date,
        end_date=end_date,
        module=module,
        operation=operation,
        model=model,
        model_tier=model_tier,
        operation_key=operation_key,
        status=None,
    )

    rows = (await session.execute(base)).scalars().all()

    total_cost = Decimal("0")
    total_input = 0
    total_output = 0
    total_cached = 0
    success_count = 0
    failed_count = 0
    by_module: dict[str, dict[str, Any]] = {}
    by_operation: dict[str, dict[str, Any]] = {}
    by_model: dict[str, dict[str, Any]] = {}
    by_tier: dict[str, dict[str, Any]] = {}
    by_operation_key: dict[str, dict[str, Any]] = {}
    by_day: dict[str, dict[str, Any]] = {}

    for row in rows:
        if row.estimated_total_cost is not None:
            total_cost += row.estimated_total_cost
        total_input += row.input_tokens
        total_output += row.output_tokens
        total_cached += row.cached_input_tokens
        if row.status == "success":
            success_count += 1
        else:
            failed_count += 1

        cost = float(row.estimated_total_cost or 0)
        for bucket, key in (
            (by_module, row.module),
            (by_operation, row.operation),
            (by_model, row.model),
        ):
            if key not in bucket:
                bucket[key] = {"key": key, "requests": 0, "estimatedCost": 0.0, "inputTokens": 0}
            bucket[key]["requests"] += 1
            bucket[key]["estimatedCost"] += cost
            bucket[key]["inputTokens"] += row.input_tokens

        tier_key = row.model_tier or "unknown"
        if tier_key not in by_tier:
            by_tier[tier_key] = {
                "key": tier_key,
                "requests": 0,
                "estimatedCost": 0.0,
                "inputTokens": 0,
            }
        by_tier[tier_key]["requests"] += 1
        by_tier[tier_key]["estimatedCost"] += cost
        by_tier[tier_key]["inputTokens"] += row.input_tokens

        op_key = getattr(row, "operation_key", None) or "unknown"
        if op_key not in by_operation_key:
            by_operation_key[op_key] = {
                "key": op_key,
                "requests": 0,
                "estimatedCost": 0.0,
                "inputTokens": 0,
            }
        by_operation_key[op_key]["requests"] += 1
        by_operation_key[op_key]["estimatedCost"] += cost
        by_operation_key[op_key]["inputTokens"] += row.input_tokens

        day_key = row.created_at.date().isoformat()
        if day_key not in by_day:
            by_day[day_key] = {"date": day_key, "requests": 0, "estimatedCost": 0.0}
        by_day[day_key]["requests"] += 1
        by_day[day_key]["estimatedCost"] += cost

    return {
        "totalEstimatedCost": float(total_cost),
        "totalRequests": len(rows),
        "successfulRequests": success_count,
        "failedRequests": failed_count,
        "totalInputTokens": total_input,
        "totalOutputTokens": total_output,
        "totalCachedInputTokens": total_cached,
        "byModule": sorted(by_module.values(), key=lambda x: x["estimatedCost"], reverse=True),
        "byOperation": sorted(by_operation.values(), key=lambda x: x["estimatedCost"], reverse=True),
        "byModel": sorted(by_model.values(), key=lambda x: x["estimatedCost"], reverse=True),
        "byTier": sorted(by_tier.values(), key=lambda x: x["estimatedCost"], reverse=True),
        "byOperationKey": sorted(
            by_operation_key.values(), key=lambda x: x["estimatedCost"], reverse=True
        ),
        "byDay": sorted(by_day.values(), key=lambda x: x["date"]),
        "routingInsights": _compute_routing_insights(rows, by_tier),
    }


async def list_usage_logs(
    session: AsyncSession,
    project_id: UUID,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
    module: str | None = None,
    operation: str | None = None,
    model: str | None = None,
    model_tier: str | None = None,
    operation_key: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[AiUsageLog], int]:
    base = select(AiUsageLog)
    filtered = _apply_log_filters(
        base,
        project_id=project_id,
        start_date=start_date,
        end_date=end_date,
        module=module,
        operation=operation,
        model=model,
        model_tier=model_tier,
        operation_key=operation_key,
        status=status,
    )

    count_stmt = select(func.count(AiUsageLog.id))
    count_stmt = _apply_log_filters(
        count_stmt,
        project_id=project_id,
        start_date=start_date,
        end_date=end_date,
        module=module,
        operation=operation,
        model=model,
        model_tier=model_tier,
        operation_key=operation_key,
        status=status,
    )
    total = int((await session.execute(count_stmt)).scalar_one())

    rows = (
        await session.execute(
            filtered.order_by(AiUsageLog.created_at.desc()).limit(limit).offset(offset)
        )
    ).scalars().all()
    return list(rows), total


async def get_usage_log(
    session: AsyncSession,
    project_id: UUID,
    log_id: UUID,
) -> AiUsageLog | None:
    return (
        await session.execute(
            select(AiUsageLog).where(
                AiUsageLog.id == log_id,
                AiUsageLog.project_id == project_id,
            )
        )
    ).scalar_one_or_none()


async def get_budget_status(session: AsyncSession, project_id: UUID) -> dict[str, Any]:
    today = utc_now_naive().date()
    daily_spent = await sum_project_spend(session, project_id, since=day_start_utc_naive(today))
    monthly_spent = await sum_project_spend(session, project_id, since=month_start_utc_naive(today))

    daily_limit = settings.ai_daily_budget_usd or 0
    monthly_limit = settings.ai_monthly_budget_usd or 0

    near_limit = False
    blocked = False
    if daily_limit > 0:
        if daily_spent >= Decimal(str(daily_limit)):
            blocked = True
        elif daily_spent >= Decimal(str(daily_limit)) * Decimal("0.8"):
            near_limit = True
    if monthly_limit > 0:
        if monthly_spent >= Decimal(str(monthly_limit)):
            blocked = True
        elif monthly_spent >= Decimal(str(monthly_limit)) * Decimal("0.8"):
            near_limit = True

    return {
        "dailySpent": float(daily_spent),
        "monthlySpent": float(monthly_spent),
        "dailyBudgetUsd": daily_limit or None,
        "monthlyBudgetUsd": monthly_limit or None,
        "nearLimit": near_limit,
        "blocked": blocked,
    }


async def estimate_operation_cost(
    session: AsyncSession,
    project_id: UUID,
    *,
    operation: str,
    count: int = 1,
) -> dict[str, Any]:
    since = utc_now_naive() - timedelta(days=7)
    stmt = (
        select(
            func.count(AiUsageLog.id),
            func.avg(AiUsageLog.estimated_total_cost),
        )
        .where(
            AiUsageLog.project_id == project_id,
            AiUsageLog.operation == operation,
            AiUsageLog.status == "success",
            AiUsageLog.created_at >= since,
            AiUsageLog.estimated_total_cost.isnot(None),
        )
    )
    row = (await session.execute(stmt)).one()
    request_count = int(row[0] or 0)
    avg_cost = Decimal(str(row[1])) if row[1] is not None else None

    if avg_cost is None or request_count == 0:
        return {
            "operation": operation,
            "count": count,
            "estimatedTotalCost": None,
            "avgCostPerRequest": None,
            "basedOnRequests": 0,
            "message": "Nessuno storico sufficiente per stimare il costo.",
        }

    estimated = avg_cost * count
    return {
        "operation": operation,
        "count": count,
        "estimatedTotalCost": float(estimated),
        "avgCostPerRequest": float(avg_cost),
        "basedOnRequests": request_count,
        "message": None,
    }


async def get_global_usage_summary(
    session: AsyncSession,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict[str, Any]:
    workspace = await get_default_workspace(session)
    project_ids = (
        await session.execute(select(Project.id).where(Project.workspace_id == workspace.id))
    ).scalars().all()

    merged: dict[str, Any] = {
        "totalEstimatedCost": 0.0,
        "totalRequests": 0,
        "successfulRequests": 0,
        "failedRequests": 0,
        "totalInputTokens": 0,
        "totalOutputTokens": 0,
        "totalCachedInputTokens": 0,
        "byModule": {},
        "byOperation": {},
        "byModel": {},
        "byTier": {},
        "byOperationKey": {},
        "byDay": {},
        "projectCount": len(project_ids),
        "routingInsights": {
            "cost_by_tier": {},
            "requests_by_tier": {},
            "premium_on_cheap_profile_count": 0,
            "explicit_override_count": 0,
            "unconfigured_model_warnings": [],
            "schema_fallback_retry_count": 0,
        },
    }

    for pid in project_ids:
        summary = await get_usage_summary(
            session, pid, start_date=start_date, end_date=end_date
        )
        merged["totalEstimatedCost"] += summary["totalEstimatedCost"]
        merged["totalRequests"] += summary["totalRequests"]
        merged["successfulRequests"] += summary["successfulRequests"]
        merged["failedRequests"] += summary["failedRequests"]
        merged["totalInputTokens"] += summary["totalInputTokens"]
        merged["totalOutputTokens"] += summary["totalOutputTokens"]
        merged["totalCachedInputTokens"] += summary["totalCachedInputTokens"]

        for bucket_name, items in (
            ("byModule", summary["byModule"]),
            ("byOperation", summary["byOperation"]),
            ("byModel", summary["byModel"]),
            ("byTier", summary["byTier"]),
            ("byOperationKey", summary.get("byOperationKey", [])),
            ("byDay", summary["byDay"]),
        ):
            bucket: dict = merged[bucket_name]
            for item in items:
                key = item.get("key") or item.get("date")
                if key not in bucket:
                    bucket[key] = {**item}
                else:
                    bucket[key]["requests"] += item["requests"]
                    bucket[key]["estimatedCost"] += item["estimatedCost"]
                    if "inputTokens" in item:
                        bucket[key]["inputTokens"] = bucket[key].get("inputTokens", 0) + item["inputTokens"]

        insights = summary.get("routingInsights") or {}
        merged_insights = merged["routingInsights"]
        for tier, cost in (insights.get("cost_by_tier") or {}).items():
            merged_insights["cost_by_tier"][tier] = merged_insights["cost_by_tier"].get(tier, 0.0) + cost
        for tier, count in (insights.get("requests_by_tier") or {}).items():
            merged_insights["requests_by_tier"][tier] = (
                merged_insights["requests_by_tier"].get(tier, 0) + count
            )
        merged_insights["premium_on_cheap_profile_count"] += insights.get(
            "premium_on_cheap_profile_count", 0
        )
        merged_insights["explicit_override_count"] += insights.get("explicit_override_count", 0)
        merged_insights["schema_fallback_retry_count"] += insights.get(
            "schema_fallback_retry_count", 0
        )
        for warning in insights.get("unconfigured_model_warnings") or []:
            if warning not in merged_insights["unconfigured_model_warnings"]:
                merged_insights["unconfigured_model_warnings"].append(warning)

    for bucket_name in ("byModule", "byOperation", "byModel", "byTier", "byOperationKey"):
        merged[bucket_name] = sorted(
            merged[bucket_name].values(),
            key=lambda x: x.get("estimatedCost", 0),
            reverse=True,
        )
    merged["byDay"] = sorted(merged["byDay"].values(), key=lambda x: x["date"])
    return merged
