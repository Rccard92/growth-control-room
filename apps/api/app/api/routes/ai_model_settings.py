"""AI model settings API routes."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.ai_model_settings import (
    AiAvailableModelItem,
    AiAvailableModelsResponse,
    AiBulkActionResponse,
    AiModelSettingItemResponse,
    AiModelSettingMutationResponse,
    AiModelSettingsListResponse,
    AiModelSettingUpdateRequest,
    AiModelValidateRequest,
    AiModelValidateResponse,
)
from app.services.ai.model_settings_service import (
    apply_gcr_recommendations,
    get_available_models,
    get_setting_row,
    list_settings_for_project,
    reset_all_to_railway,
    reset_project_setting,
    seed_default_settings,
    update_project_setting,
    validate_model_for_operation,
)
from app.services.ai.operation_registry import get_operation, tier_cost_profile_label
from app.services.projects import get_project_in_default_workspace

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["ai-model-settings"])
global_router = APIRouter(tags=["ai-model-settings"])

_ITEM_CAMEL_TO_SNAKE: dict[str, str] = {
    "operationKey": "operation_key",
    "contextProfile": "context_profile",
    "recommendedTier": "recommended_tier",
    "recommendedModel": "recommended_model",
    "recommendedMaxOutputTokens": "recommended_max_output_tokens",
    "recommendedTemperature": "recommended_temperature",
    "recommendedUse": "recommended_use",
    "qualityLevel": "quality_level",
    "costSensitivity": "cost_sensitivity",
    "warningNotes": "warning_notes",
    "modelTier": "model_tier",
    "maxOutputTokens": "max_output_tokens",
    "fallbackModel": "fallback_model",
    "allowFallback": "allow_fallback",
    "reasoningEffort": "reasoning_effort",
    "hasProjectOverride": "has_project_override",
    "guardrailWarnings": "guardrail_warnings",
    "recentRequestCount": "recent_request_count",
    "avgCostRecent": "avg_cost_recent",
    "lastRequestAt": "last_request_at",
    "uiCategory": "ui_category",
    "gcrRecommendedModel": "gcr_recommended_model",
    "gcrRecommendationReason": "gcr_recommendation_reason",
    "costProfileLabel": "cost_profile_label",
}

_AVAILABLE_CAMEL_TO_SNAKE: dict[str, str] = {
    "envModels": "env_models",
    "pricingConfigured": "pricing_configured",
    "knownSupported": "known_supported",
}

_TOP_CAMEL_TO_SNAKE: dict[str, str] = {
    "registryCount": "registry_count",
    "missingSettings": "missing_settings",
    "unpricedModels": "unpriced_models",
    "availableModels": "available_models",
}


def _normalize_keys(data: dict[str, Any], mapping: dict[str, str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in data.items():
        out[mapping.get(key, key)] = value
    return out


def _normalize_setting_item(item: dict[str, Any]) -> dict[str, Any]:
    return _normalize_keys(item, _ITEM_CAMEL_TO_SNAKE)


def _normalize_available_model(item: dict[str, Any]) -> dict[str, Any]:
    return _normalize_keys(item, _AVAILABLE_CAMEL_TO_SNAKE)


def _normalize_available_models(data: dict[str, Any]) -> dict[str, Any]:
    normalized = _normalize_keys(data, _TOP_CAMEL_TO_SNAKE)
    if "models" in normalized:
        normalized["models"] = [
            _normalize_available_model(m) for m in normalized["models"]
        ]
    return normalized


def _fallback_setting_item(operation_key: str) -> AiModelSettingItemResponse:
    op = get_operation(operation_key)
    if op is None:
        return AiModelSettingItemResponse(
            operation_key=operation_key,
            label=operation_key,
            status="planned",
            enabled=False,
            module="unknown",
            context_profile="generic",
            recommended_tier="standard",
            recommended_model=None,
            recommended_max_output_tokens=2000,
            recommended_temperature=0.45,
            recommended_use="N/D",
            quality_level="medium",
            cost_sensitivity="medium",
            description="",
            model=None,
            model_tier="standard",
            allow_fallback=True,
            source="registry_default",
            has_project_override=False,
            guardrail_warnings=["Item incompleto — fallback sicuro applicato."],
            recent_request_count=0,
            ui_category="brand_intelligence",
            gcr_recommended_model="gpt-5.4",
            gcr_recommendation_reason="",
            cost_profile_label="profilo costo: bilanciato",
        )
    return AiModelSettingItemResponse(
        operation_key=op.operation_key,
        label=op.label,
        status=op.status,
        enabled=op.status == "implemented" and op.enabled,
        module=op.module,
        context_profile=op.context_profile,
        recommended_tier=op.recommended_tier,
        recommended_model=None,
        recommended_max_output_tokens=op.recommended_max_output_tokens,
        recommended_temperature=op.recommended_temperature,
        recommended_use=op.recommended_use,
        quality_level=op.quality_level,
        cost_sensitivity=op.cost_sensitivity,
        description=op.description,
        warning_notes=op.warning_notes,
        model=op.gcr_recommended_model if op.status == "implemented" else None,
        model_tier=op.recommended_tier,
        allow_fallback=True,
        source="registry_default",
        has_project_override=False,
        guardrail_warnings=(
            ["Operazione pianificata — nessun modello attivo."]
            if op.status == "planned"
            else ["Operazione non AI — nessun modello configurato."]
            if op.status == "non_ai"
            else []
        ),
        recent_request_count=0,
        ui_category=op.ui_category,
        gcr_recommended_model=op.gcr_recommended_model,
        gcr_recommendation_reason=op.gcr_recommendation_reason,
        cost_profile_label=tier_cost_profile_label(op.recommended_tier),
    )


def _to_list_response(data: dict) -> AiModelSettingsListResponse:
    registry_count = data.get("registry_count", data.get("registryCount", 0))
    missing_settings = data.get("missing_settings", data.get("missingSettings", []))
    unpriced_models = data.get("unpriced_models", data.get("unpricedModels", []))
    available_raw = data.get("available_models", data.get("availableModels", {}))
    available = _normalize_available_models(available_raw)

    items: list[AiModelSettingItemResponse] = []
    response_warnings: list[str] = []

    for raw in data.get("items", []):
        normalized = _normalize_setting_item(raw)
        operation_key = normalized.get("operation_key", "unknown")
        op = get_operation(operation_key)
        if op is not None:
            normalized.setdefault("ui_category", op.ui_category)
            normalized.setdefault("gcr_recommended_model", op.gcr_recommended_model)
            normalized.setdefault("gcr_recommendation_reason", op.gcr_recommendation_reason)
            normalized.setdefault(
                "cost_profile_label",
                tier_cost_profile_label(normalized.get("model_tier", op.recommended_tier)),
            )
        try:
            items.append(AiModelSettingItemResponse.model_validate(normalized))
        except ValidationError as exc:
            logger.warning(
                "Validazione model setting fallita per operation_key=%s: %s",
                operation_key,
                exc,
            )
            response_warnings.append(
                f"Impostazione '{operation_key}' incompleta — mostrato fallback sicuro."
            )
            items.append(_fallback_setting_item(operation_key))

    available_response = AiAvailableModelsResponse(
        env_models=available.get("env_models", available.get("envModels", {})),
        models=[
            AiAvailableModelItem.model_validate(_normalize_available_model(m))
            for m in available.get("models", [])
        ],
        warnings=list(available.get("warnings", [])) + response_warnings,
    )

    return AiModelSettingsListResponse(
        items=items,
        registry_count=registry_count,
        missing_settings=missing_settings,
        unpriced_models=unpriced_models,
        available_models=available_response,
    )


@router.get(
    "/{project_id}/ai-model-settings",
    response_model=AiModelSettingsListResponse,
    response_model_by_alias=True,
)
async def get_project_ai_model_settings(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> AiModelSettingsListResponse:
    await get_project_in_default_workspace(project_id, session)
    data = await list_settings_for_project(session, project_id)
    return _to_list_response(data)


@router.put(
    "/{project_id}/ai-model-settings/{operation_key}",
    response_model=AiModelSettingMutationResponse,
    response_model_by_alias=True,
)
async def update_project_ai_model_setting(
    project_id: UUID,
    operation_key: str,
    body: AiModelSettingUpdateRequest,
    session: AsyncSession = Depends(get_db),
) -> AiModelSettingMutationResponse:
    await get_project_in_default_workspace(project_id, session)
    try:
        row = await update_project_setting(
            session,
            project_id,
            operation_key,
            model=body.model,
            model_tier=body.model_tier,
            max_output_tokens=body.max_output_tokens,
            temperature=body.temperature,
            fallback_model=body.fallback_model,
            allow_fallback=body.allow_fallback,
            enabled=body.enabled,
            notes=body.notes,
            reasoning_effort=body.reasoning_effort,
        )
        await session.commit()
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return AiModelSettingMutationResponse(
        operation_key=operation_key,
        model=row.model,
        model_tier=row.model_tier,
        source=row.source,
        message="Impostazione salvata.",
    )


@router.post(
    "/{project_id}/ai-model-settings/{operation_key}/reset",
    response_model=AiModelSettingMutationResponse,
    response_model_by_alias=True,
)
async def reset_project_ai_model_setting(
    project_id: UUID,
    operation_key: str,
    session: AsyncSession = Depends(get_db),
) -> AiModelSettingMutationResponse:
    await get_project_in_default_workspace(project_id, session)
    try:
        await reset_project_setting(session, project_id, operation_key)
        await session.commit()
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    row = await get_setting_row(session, project_id, operation_key)
    if row is None:
        row = await get_setting_row(session, None, operation_key)
    return AiModelSettingMutationResponse(
        operation_key=operation_key,
        model=row.model if row else "",
        model_tier=row.model_tier if row else "",
        source=row.source if row else "env_seed",
        message="Ripristinato al consigliato registry/env.",
    )


@router.post(
    "/{project_id}/ai-model-settings/apply-gcr-recommendations",
    response_model=AiBulkActionResponse,
    response_model_by_alias=True,
)
async def apply_project_gcr_recommendations(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> AiBulkActionResponse:
    await get_project_in_default_workspace(project_id, session)
    updated = await apply_gcr_recommendations(session, project_id)
    await session.commit()
    return AiBulkActionResponse(
        updated_count=updated,
        message=f"Applicati consigli GCR su {updated} funzioni AI attive.",
    )


@router.post(
    "/{project_id}/ai-model-settings/reset-railway",
    response_model=AiBulkActionResponse,
    response_model_by_alias=True,
)
async def reset_project_models_from_railway(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> AiBulkActionResponse:
    await get_project_in_default_workspace(project_id, session)
    updated = await reset_all_to_railway(session, project_id)
    await session.commit()
    return AiBulkActionResponse(
        updated_count=updated,
        message=f"Ripristinati {updated} modelli da registry/env Railway.",
    )


@router.post(
    "/{project_id}/ai-model-settings/validate-model",
    response_model=AiModelValidateResponse,
    response_model_by_alias=True,
)
async def validate_project_ai_model(
    project_id: UUID,
    body: AiModelValidateRequest,
    session: AsyncSession = Depends(get_db),
) -> AiModelValidateResponse:
    await get_project_in_default_workspace(project_id, session)
    try:
        data = await validate_model_for_operation(
            session,
            project_id,
            model=body.model,
            operation_key=body.operation_key,
            run_probe=body.run_probe,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return AiModelValidateResponse.model_validate(data)


@router.post(
    "/{project_id}/ai-model-settings/seed-defaults",
    response_model=dict,
)
async def seed_project_ai_model_defaults(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> dict:
    await get_project_in_default_workspace(project_id, session)
    global_created = await seed_default_settings(session, project_id=None, source="env_seed")
    project_created = await seed_default_settings(session, project_id=project_id, source="env_seed")
    await session.commit()
    return {
        "globalCreated": global_created,
        "projectCreated": project_created,
    }


@global_router.get(
    "/ai-model-settings/available-models",
    response_model=AiAvailableModelsResponse,
    response_model_by_alias=True,
)
async def get_ai_available_models(
    session: AsyncSession = Depends(get_db),
) -> AiAvailableModelsResponse:
    data = await get_available_models(session)
    normalized = _normalize_available_models(data)
    return AiAvailableModelsResponse(
        env_models=normalized["env_models"],
        models=[
            AiAvailableModelItem.model_validate(_normalize_available_model(m))
            for m in normalized["models"]
        ],
        warnings=normalized["warnings"],
    )
