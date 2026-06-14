"""AI model settings API routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.ai_model_settings import (
    AiAvailableModelItem,
    AiAvailableModelsResponse,
    AiModelSettingItemResponse,
    AiModelSettingMutationResponse,
    AiModelSettingsListResponse,
    AiModelSettingUpdateRequest,
)
from app.services.ai.model_settings_service import (
    get_available_models,
    list_settings_for_project,
    reset_project_setting,
    seed_default_settings,
    update_project_setting,
)
from app.services.projects import get_project_in_default_workspace

router = APIRouter(prefix="/projects", tags=["ai-model-settings"])
global_router = APIRouter(tags=["ai-model-settings"])


def _to_list_response(data: dict) -> AiModelSettingsListResponse:
    available = data["availableModels"]
    return AiModelSettingsListResponse(
        items=[AiModelSettingItemResponse.model_validate(item) for item in data["items"]],
        registry_count=data["registryCount"],
        missing_settings=data["missingSettings"],
        available_models=AiAvailableModelsResponse(
            env_models=available["envModels"],
            models=[AiAvailableModelItem.model_validate(m) for m in available["models"]],
            warnings=available["warnings"],
        ),
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
    return AiModelSettingMutationResponse(
        operation_key=operation_key,
        model="",
        model_tier="",
        source="env_seed",
        message="Ripristinato al consigliato registry/env.",
    )


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
    return AiAvailableModelsResponse(
        env_models=data["envModels"],
        models=[AiAvailableModelItem.model_validate(m) for m in data["models"]],
        warnings=data["warnings"],
    )
