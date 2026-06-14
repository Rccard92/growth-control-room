"""AI model settings persistence, seeding and resolution helpers."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.datetime import utc_now_naive
from app.models.ai_model_setting import AiModelSetting
from app.models.ai_usage_log import AiUsageLog
from app.services.ai.operation_registry import (
    AI_OPERATIONS,
    AiOperationDefinition,
    get_operation,
    list_operations,
    recommended_model_from_env,
    resolve_registry_model,
    tier_cost_profile_label,
)
from app.services.ai.model_policy import AiModelTier, AiResolvedModel, infer_tier_from_model
from app.services.ai.model_request_params import (
    KNOWN_SUPPORTED_MODELS,
    build_openai_request_params,
    infer_model_family,
    is_known_supported_model,
)
from app.services.ai.pricing import OPENAI_MODEL_PRICING, estimate_usage_cost


def _default_model_for_operation(op: AiOperationDefinition) -> str:
    from app.services.ai.model_policy import AiModelTier, tier_to_model_name

    model = resolve_registry_model(op)
    if model:
        return model
    tier = AiModelTier(op.recommended_tier)
    tier_model = tier_to_model_name(tier)
    if tier_model:
        return tier_model
    if settings.openai_model_fallback:
        return settings.openai_model_fallback.strip()
    return settings.openai_model


def _setting_from_registry(
    op: AiOperationDefinition,
    *,
    project_id: UUID | None,
    source: str = "default",
) -> AiModelSetting:
    model = _default_model_for_operation(op)
    fallback = recommended_model_from_env("OPENAI_MODEL_FALLBACK") or settings.openai_model
    return AiModelSetting(
        project_id=project_id,
        operation_key=op.operation_key,
        module=op.module,
        operation=op.operation,
        context_profile=op.context_profile,
        enabled=op.enabled and op.status == "implemented",
        model=model,
        model_tier=op.recommended_tier,
        max_output_tokens=op.recommended_max_output_tokens,
        temperature=Decimal(str(op.recommended_temperature)),
        fallback_model=fallback,
        allow_fallback=True,
        source=source,
    )


async def seed_default_settings(
    session: AsyncSession,
    project_id: UUID | None = None,
    *,
    source: str = "env_seed",
) -> int:
    created = 0
    for op in list_operations(include_planned=True):
        existing = await session.execute(
            select(AiModelSetting).where(
                AiModelSetting.project_id == project_id,
                AiModelSetting.operation_key == op.operation_key,
            )
        )
        if existing.scalar_one_or_none() is not None:
            continue
        row = _setting_from_registry(op, project_id=project_id, source=source)
        session.add(row)
        created += 1
    if created:
        await session.flush()
    return created


async def get_setting_row(
    session: AsyncSession,
    project_id: UUID | None,
    operation_key: str,
) -> AiModelSetting | None:
    result = await session.execute(
        select(AiModelSetting).where(
            AiModelSetting.project_id == project_id,
            AiModelSetting.operation_key == operation_key,
        )
    )
    return result.scalar_one_or_none()


async def get_effective_setting_with_source(
    session: AsyncSession,
    project_id: UUID,
    operation_key: str,
) -> tuple[AiModelSetting | None, str | None]:
    project_row = await get_setting_row(session, project_id, operation_key)
    if project_row is not None and project_row.enabled:
        return project_row, "project_setting"
    global_row = await get_setting_row(session, None, operation_key)
    if global_row is not None and global_row.enabled:
        return global_row, "global_setting"
    return None, None


async def get_effective_setting(
    session: AsyncSession,
    project_id: UUID,
    operation_key: str,
) -> AiModelSetting | None:
    project_row = await get_setting_row(session, project_id, operation_key)
    if project_row is not None and project_row.enabled:
        return project_row
    global_row = await get_setting_row(session, None, operation_key)
    if global_row is not None and global_row.enabled:
        return global_row
    return project_row or global_row


def compute_guardrail_warnings(
    op: AiOperationDefinition | None,
    *,
    model_tier: str,
    model_name: str | None,
) -> list[str]:
    warnings: list[str] = []
    if op is None:
        return warnings
    if op.status == "planned":
        warnings.append("Operazione pianificata — nessun modello attivo.")
        return warnings
    if op.status == "non_ai":
        warnings.append("Operazione non AI — nessun modello configurato.")
        return warnings
    cheap_tiers = {"cheap"}
    premium_tiers = {"premium", "reasoning"}
    if op.quality_level == "critical" and model_tier in cheap_tiers:
        warnings.append(
            f"ATTENZIONE: operation critica '{op.operation_key}' usa tier cheap."
        )
    elif op.recommended_tier in cheap_tiers and model_tier in premium_tiers:
        warnings.append(
            f"Operation '{op.operation_key}' usa tier premium su task economico consigliato."
        )
    return warnings


def _is_model_priced(model_name: str | None) -> bool:
    if not model_name or not str(model_name).strip():
        return True
    return estimate_usage_cost(str(model_name).strip(), input_tokens=1, output_tokens=1) is not None


def _collect_unpriced_models(items: list[dict[str, Any]]) -> list[str]:
    unpriced: set[str] = set()
    for item in items:
        model = item.get("model")
        if model and not _is_model_priced(model):
            unpriced.add(str(model).strip())
    return sorted(unpriced)


async def get_available_models(session: AsyncSession) -> dict[str, Any]:
    env_models: dict[str, str | None] = {
        "cheap": settings.openai_model_cheap or settings.openai_model,
        "standard": settings.openai_model_standard or settings.openai_model,
        "premium": settings.openai_model_premium or "gpt-4o",
        "reasoning": settings.openai_model_reasoning,
        "fallback": (
            settings.openai_model_fallback
            or settings.openai_model_standard
            or settings.openai_model
        ),
        "legacy": settings.openai_model,
    }
    pricing_models = list(OPENAI_MODEL_PRICING.keys())
    log_models = (
        await session.execute(select(AiUsageLog.model).distinct().limit(50))
    ).scalars().all()
    all_names: set[str] = set(KNOWN_SUPPORTED_MODELS)
    for op in list_operations(include_planned=True):
        if op.gcr_recommended_model:
            all_names.add(op.gcr_recommended_model.strip())
    for name in list(env_models.values()) + pricing_models + list(log_models):
        if name and str(name).strip():
            all_names.add(str(name).strip())
    models = []
    for name in sorted(all_names):
        models.append(
            {
                "name": name,
                "pricing_configured": estimate_usage_cost(name, input_tokens=1, output_tokens=1)
                is not None,
                "family": infer_model_family(name),
                "known_supported": is_known_supported_model(name),
                "source": (
                    "env"
                    if name in {v for v in env_models.values() if v}
                    else "pricing"
                    if name in pricing_models
                    else "registry"
                    if name in {op.gcr_recommended_model for op in list_operations(include_planned=True)}
                    else "logs"
                ),
            }
        )
    warnings = [
        f"Tier {tier} senza modello env"
        for tier, val in env_models.items()
        if tier not in ("legacy",) and not val
    ]
    return {
        "env_models": env_models,
        "models": models,
        "warnings": warnings,
    }


async def _usage_stats_for_operation(
    session: AsyncSession,
    project_id: UUID,
    operation_key: str,
) -> dict[str, Any]:
    since = utc_now_naive() - timedelta(days=30)
    stmt = select(
        func.count(AiUsageLog.id),
        func.avg(AiUsageLog.estimated_total_cost),
        func.max(AiUsageLog.created_at),
    ).where(
        AiUsageLog.project_id == project_id,
        AiUsageLog.operation_key == operation_key,
        AiUsageLog.created_at >= since,
    )
    row = (await session.execute(stmt)).one()
    count = int(row[0] or 0)
    avg = float(row[1]) if row[1] is not None else None
    last_at = row[2]
    return {
        "recent_request_count": count,
        "avg_cost_recent": avg,
        "last_request_at": last_at.isoformat() if last_at else None,
    }


async def list_settings_for_project(
    session: AsyncSession,
    project_id: UUID,
) -> dict[str, Any]:
    await seed_default_settings(session, project_id=None, source="env_seed")
    await seed_default_settings(session, project_id=project_id, source="env_seed")
    await session.flush()

    project_rows = {
        r.operation_key: r
        for r in (
            await session.execute(
                select(AiModelSetting).where(AiModelSetting.project_id == project_id)
            )
        ).scalars().all()
    }
    global_rows = {
        r.operation_key: r
        for r in (
            await session.execute(
                select(AiModelSetting).where(AiModelSetting.project_id.is_(None))
            )
        ).scalars().all()
    }

    items: list[dict[str, Any]] = []
    missing: list[str] = []
    for op in list_operations(include_planned=True):
        registry = op
        effective = project_rows.get(op.operation_key) or global_rows.get(op.operation_key)
        if effective is None:
            missing.append(op.operation_key)
            effective = _setting_from_registry(op, project_id=project_id)
        stats = (
            await _usage_stats_for_operation(session, project_id, op.operation_key)
            if op.status == "implemented"
            else {"recent_request_count": 0, "avg_cost_recent": None, "last_request_at": None}
        )
        source = "registry_default"
        if op.operation_key in project_rows:
            source = project_rows[op.operation_key].source or "manual"
        elif op.operation_key in global_rows:
            source = global_rows[op.operation_key].source or "default"

        is_operational = op.status == "implemented"
        display_model = effective.model if is_operational else None
        display_enabled = effective.enabled if is_operational else False
        display_tier = effective.model_tier if is_operational else op.recommended_tier

        warnings = compute_guardrail_warnings(
            registry,
            model_tier=display_tier,
            model_name=display_model,
        )
        recent_error = (
            await _recent_error_for_operation(
                session, project_id, op.operation_key, display_model
            )
            if is_operational
            else None
        )
        if recent_error:
            warnings = [*warnings, recent_error]
        items.append(
            {
                "operation_key": op.operation_key,
                "label": op.label,
                "status": op.status,
                "enabled": display_enabled,
                "module": op.module,
                "context_profile": op.context_profile,
                "recommended_tier": op.recommended_tier,
                "recommended_model": _default_model_for_operation(op),
                "recommended_max_output_tokens": op.recommended_max_output_tokens,
                "recommended_temperature": op.recommended_temperature,
                "recommended_use": op.recommended_use,
                "quality_level": op.quality_level,
                "cost_sensitivity": op.cost_sensitivity,
                "description": op.description,
                "warning_notes": op.warning_notes,
                "model": display_model,
                "model_tier": display_tier,
                "max_output_tokens": effective.max_output_tokens if is_operational else None,
                "temperature": float(effective.temperature) if is_operational and effective.temperature else None,
                "fallback_model": effective.fallback_model if is_operational else None,
                "allow_fallback": effective.allow_fallback if is_operational else True,
                "reasoning_effort": effective.reasoning_effort if is_operational else None,
                "notes": effective.notes,
                "source": source,
                "has_project_override": op.operation_key in project_rows,
                "guardrail_warnings": warnings,
                "ui_category": op.ui_category,
                "gcr_recommended_model": op.gcr_recommended_model,
                "gcr_recommendation_reason": op.gcr_recommendation_reason,
                "cost_profile_label": tier_cost_profile_label(display_tier),
                **stats,
            }
        )

    unpriced_models = _collect_unpriced_models(items)
    available = await get_available_models(session)
    return {
        "items": items,
        "registry_count": len(AI_OPERATIONS),
        "missing_settings": missing,
        "unpriced_models": unpriced_models,
        "available_models": available,
    }


async def update_project_setting(
    session: AsyncSession,
    project_id: UUID,
    operation_key: str,
    *,
    model: str | None = None,
    model_tier: str | None = None,
    max_output_tokens: int | None = None,
    temperature: float | None = None,
    fallback_model: str | None = None,
    allow_fallback: bool | None = None,
    enabled: bool | None = None,
    notes: str | None = None,
    reasoning_effort: str | None = None,
) -> AiModelSetting:
    op = get_operation(operation_key)
    if op is None:
        raise ValueError(f"operation_key sconosciuta: {operation_key}")

    row = await get_setting_row(session, project_id, operation_key)
    if row is None:
        row = _setting_from_registry(op, project_id=project_id, source="manual")
        session.add(row)
    if model is not None:
        row.model = model.strip()
    if model_tier is not None:
        row.model_tier = model_tier
    if max_output_tokens is not None:
        row.max_output_tokens = max_output_tokens
    if temperature is not None:
        row.temperature = Decimal(str(temperature))
    if fallback_model is not None:
        row.fallback_model = fallback_model.strip() or None
    if allow_fallback is not None:
        row.allow_fallback = allow_fallback
    if enabled is not None:
        row.enabled = enabled
    if notes is not None:
        row.notes = notes
    if reasoning_effort is not None:
        row.reasoning_effort = reasoning_effort
    row.source = "manual"
    await session.flush()
    return row


async def reset_project_setting(
    session: AsyncSession,
    project_id: UUID,
    operation_key: str,
) -> None:
    op = get_operation(operation_key)
    if op is None:
        raise ValueError(f"operation_key sconosciuta: {operation_key}")
    row = await get_setting_row(session, project_id, operation_key)
    if row is not None:
        await session.delete(row)
        await session.flush()
    await seed_default_settings(session, project_id=project_id, source="env_seed")


async def apply_gcr_recommendations(
    session: AsyncSession,
    project_id: UUID,
) -> int:
    updated = 0
    for op in list_operations(include_planned=False):
        if op.status != "implemented":
            continue
        row = await get_setting_row(session, project_id, op.operation_key)
        if row is None:
            row = _setting_from_registry(op, project_id=project_id, source="manual")
            session.add(row)
        row.model = op.gcr_recommended_model
        row.source = "manual"
        updated += 1
    if updated:
        await session.flush()
    return updated


async def _recent_error_for_operation(
    session: AsyncSession,
    project_id: UUID,
    operation_key: str,
    model_name: str | None,
) -> str | None:
    if not model_name:
        return None
    since = utc_now_naive() - timedelta(days=7)
    row = (
        await session.execute(
            select(AiUsageLog.error_message, AiUsageLog.error_type)
            .where(
                AiUsageLog.project_id == project_id,
                AiUsageLog.operation_key == operation_key,
                AiUsageLog.model == model_name,
                AiUsageLog.status == "error",
                AiUsageLog.created_at >= since,
            )
            .order_by(AiUsageLog.created_at.desc())
            .limit(1)
        )
    ).first()
    if not row:
        return None
    try:
        message, error_type = row
    except (TypeError, ValueError):
        return None
    if not message:
        return None
    prefix = f"Ultimo errore AI ({error_type}): " if error_type else "Ultimo errore AI: "
    return prefix + str(message)[:200]


async def validate_model_for_operation(
    session: AsyncSession,
    project_id: UUID,
    *,
    model: str,
    operation_key: str,
    run_probe: bool = True,
) -> dict[str, Any]:
    from app.services.ai.ai_client import (
        AiRequestMetadata,
        OpenAINotConfiguredError,
        OpenAIRequestError,
        is_openai_configured,
        probe_resolved_model,
    )

    model_name = model.strip()
    if not model_name:
        raise ValueError("model richiesto")

    op = get_operation(operation_key)
    if op is None:
        raise ValueError(f"operation_key sconosciuta: {operation_key}")

    warnings: list[str] = []
    if not is_known_supported_model(model_name):
        warnings.append("Modello non verificato nel catalogo GCR.")
    if not _is_model_priced(model_name):
        warnings.append("Pricing non configurato per questo modello.")

    tier = infer_tier_from_model(model_name).value
    resolved = AiResolvedModel(
        model=model_name,
        tier=tier,
        max_output_tokens=min(op.recommended_max_output_tokens, 32),
        temperature=op.recommended_temperature,
        operation_key=operation_key,
        policy_source="validate_probe",
    )
    try:
        build_openai_request_params(
            resolved,
            system_prompt="probe",
            user_prompt="ping",
            structured_json=True,
            timeout=20.0,
        )
        compatible = True
    except Exception as exc:
        compatible = False
        warnings.append(f"Parametri non compatibili: {exc}")

    probe_status = "skipped"
    probe_message: str | None = None
    if run_probe:
        if not is_openai_configured():
            probe_status = "skipped"
            probe_message = "OPENAI_API_KEY non configurata — validazione locale sola."
        else:
            metadata = AiRequestMetadata(
                project_id=project_id,
                module="ai_model_settings",
                operation="validate_model",
                operation_key=operation_key,
                context_profile=op.context_profile,
            )
            try:
                await probe_resolved_model(resolved=resolved, metadata=metadata)
                probe_status = "ok"
                probe_message = "Modello risponde correttamente."
            except OpenAINotConfiguredError:
                probe_status = "skipped"
                probe_message = "OPENAI_API_KEY non configurata."
            except OpenAIRequestError as exc:
                probe_status = "error"
                probe_message = exc.message
                compatible = False

    return {
        "valid": compatible and probe_status != "error",
        "warnings": warnings,
        "compatible": compatible,
        "probe_status": probe_status,
        "probe_message": probe_message,
        "family": infer_model_family(model_name),
        "known_supported": is_known_supported_model(model_name),
    }


async def reset_all_to_railway(
    session: AsyncSession,
    project_id: UUID,
) -> int:
    rows = (
        await session.execute(
            select(AiModelSetting).where(AiModelSetting.project_id == project_id)
        )
    ).scalars().all()
    for row in rows:
        await session.delete(row)
    if rows:
        await session.flush()
    return await seed_default_settings(session, project_id=project_id, source="env_seed")
