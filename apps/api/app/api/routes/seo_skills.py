import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.seo_skills import (
    SeoSkillCatalogResponse,
    SeoSkillRunCreateRequest,
    SeoSkillRunDetailResponse,
    SeoSkillRunRead,
    SeoSkillRunResultRead,
    SeoSkillRunStartResponse,
)
from app.services.ai.claude_client import is_claude_configured
from app.services.ai.openai_client import is_openai_configured
from app.services.projects import get_project_in_default_workspace
from app.services.seo_skills.catalog_loader import (
    _build_counts,
    load_seo_skill_catalog,
)
from app.services.seo_skills.exceptions import (
    SeoSkillNotAvailableError,
    SeoSkillProviderError,
    SeoSkillRunError,
    SeoSkillRunValidationError,
)
from app.services.seo_skills.run_service import (
    get_seo_skill_run,
    list_seo_skill_runs,
    start_seo_skill_run,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["seo-skills"])


def _ensure_provider_configured(provider: str) -> None:
    normalized = (provider or "").strip().lower()
    if normalized == "claude" and not is_claude_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Claude provider is not configured",
        )
    if normalized == "openai" and not is_openai_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OpenAI provider is not configured",
        )


def _map_run_service_error(
    exc: Exception,
    *,
    project_id: UUID | None = None,
    run_id: UUID | None = None,
) -> HTTPException:
    if isinstance(exc, SeoSkillRunValidationError):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    if isinstance(exc, SeoSkillNotAvailableError):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    if isinstance(exc, SeoSkillProviderError):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    if isinstance(exc, ValueError):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    if isinstance(exc, SeoSkillRunError):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    logger.exception(
        "Unexpected SEO skill run error project_id=%s run_id=%s",
        project_id,
        run_id,
    )
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Unable to process SEO skill run request.",
    )


@router.get(
    "/{project_id}/seo-skills/catalog",
    response_model=SeoSkillCatalogResponse,
    response_model_by_alias=True,
)
async def get_seo_skill_catalog(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> SeoSkillCatalogResponse:
    await get_project_in_default_workspace(project_id, session)
    skills = load_seo_skill_catalog()
    return SeoSkillCatalogResponse(skills=skills, counts=_build_counts(skills))


@router.post(
    "/{project_id}/seo-skills/runs",
    response_model=SeoSkillRunStartResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
)
async def create_project_seo_skill_run(
    project_id: UUID,
    request: SeoSkillRunCreateRequest,
    session: AsyncSession = Depends(get_db),
) -> SeoSkillRunStartResponse:
    await get_project_in_default_workspace(project_id, session)
    _ensure_provider_configured(request.provider)

    try:
        run = await start_seo_skill_run(session, project_id, request)
    except HTTPException:
        raise
    except Exception as exc:
        raise _map_run_service_error(exc, project_id=project_id) from exc

    return SeoSkillRunStartResponse(run=SeoSkillRunRead.model_validate(run))


@router.get(
    "/{project_id}/seo-skills/runs",
    response_model=list[SeoSkillRunRead],
    response_model_by_alias=True,
)
async def list_project_seo_skill_runs(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[SeoSkillRunRead]:
    await get_project_in_default_workspace(project_id, session)
    runs = await list_seo_skill_runs(session, project_id, limit=limit)
    return [SeoSkillRunRead.model_validate(run) for run in runs]


@router.get(
    "/{project_id}/seo-skills/runs/{run_id}",
    response_model=SeoSkillRunDetailResponse,
    response_model_by_alias=True,
)
async def get_project_seo_skill_run(
    project_id: UUID,
    run_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> SeoSkillRunDetailResponse:
    await get_project_in_default_workspace(project_id, session)
    run = await get_seo_skill_run(session, project_id, run_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SEO skill run not found.",
        )
    return SeoSkillRunDetailResponse(
        run=SeoSkillRunRead.model_validate(run),
        results=[SeoSkillRunResultRead.model_validate(result) for result in run.results],
    )


@router.get(
    "/{project_id}/seo-skills/runs/{run_id}/results",
    response_model=list[SeoSkillRunResultRead],
    response_model_by_alias=True,
)
async def get_project_seo_skill_run_results(
    project_id: UUID,
    run_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> list[SeoSkillRunResultRead]:
    await get_project_in_default_workspace(project_id, session)
    run = await get_seo_skill_run(session, project_id, run_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SEO skill run not found.",
        )
    return [SeoSkillRunResultRead.model_validate(result) for result in run.results]
