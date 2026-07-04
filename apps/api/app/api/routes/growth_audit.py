import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.growth_audit import (
    GrowthAuditEventRead,
    GrowthAuditEventsListResponse,
    GrowthAuditPageRead,
    GrowthAuditPagesListResponse,
    GrowthAuditRunCreateRequest,
    GrowthAuditRunDetailResponse,
    GrowthAuditRunRead,
    GrowthAuditRunsListResponse,
    GrowthAuditStartResponse,
)
from app.services.growth_audit.exceptions import (
    GrowthAuditError,
    GrowthAuditRunNotFoundError,
    GrowthAuditValidationError,
)
from app.services.growth_audit.run_service import (
    get_growth_audit_run_detail,
    list_growth_audit_events,
    list_growth_audit_pages,
    list_growth_audit_runs,
    start_growth_audit_run,
)
from app.services.projects import get_project_in_default_workspace

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["growth-audit"])


def _map_growth_audit_error(
    exc: Exception,
    *,
    project_id: UUID | None = None,
    run_id: UUID | None = None,
) -> HTTPException:
    if isinstance(exc, GrowthAuditValidationError):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    if isinstance(exc, GrowthAuditRunNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    if isinstance(exc, GrowthAuditError):
        logger.exception(
            "Growth Audit error project=%s run=%s",
            project_id,
            run_id,
        )
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Growth Audit operation failed",
        )
    logger.exception(
        "Unexpected Growth Audit error project=%s run=%s",
        project_id,
        run_id,
    )
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Unexpected error during Growth Audit operation",
    )


@router.post(
    "/{project_id}/growth-audit/runs",
    response_model=GrowthAuditStartResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_growth_audit_run_endpoint(
    project_id: UUID,
    request: GrowthAuditRunCreateRequest,
    session: AsyncSession = Depends(get_db),
) -> GrowthAuditStartResponse:
    await get_project_in_default_workspace(project_id, session)
    try:
        run = await start_growth_audit_run(session, project_id, request)
    except Exception as exc:
        raise _map_growth_audit_error(exc, project_id=project_id) from exc
    return GrowthAuditStartResponse(run=GrowthAuditRunRead.model_validate(run))


@router.get(
    "/{project_id}/growth-audit/runs",
    response_model=GrowthAuditRunsListResponse,
)
async def list_growth_audit_runs_endpoint(
    project_id: UUID,
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
) -> GrowthAuditRunsListResponse:
    await get_project_in_default_workspace(project_id, session)
    try:
        runs = await list_growth_audit_runs(session, project_id, limit=limit)
    except Exception as exc:
        raise _map_growth_audit_error(exc, project_id=project_id) from exc
    return GrowthAuditRunsListResponse(
        runs=[GrowthAuditRunRead.model_validate(run) for run in runs]
    )


@router.get(
    "/{project_id}/growth-audit/runs/{run_id}",
    response_model=GrowthAuditRunDetailResponse,
)
async def get_growth_audit_run_endpoint(
    project_id: UUID,
    run_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> GrowthAuditRunDetailResponse:
    await get_project_in_default_workspace(project_id, session)
    try:
        run, findings_count, tasks_count = await get_growth_audit_run_detail(
            session,
            project_id,
            run_id,
        )
    except Exception as exc:
        raise _map_growth_audit_error(
            exc,
            project_id=project_id,
            run_id=run_id,
        ) from exc

    events = sorted(run.events, key=lambda event: event.created_at)
    return GrowthAuditRunDetailResponse(
        run=GrowthAuditRunRead.model_validate(run),
        pages=[GrowthAuditPageRead.model_validate(page) for page in run.pages],
        events=[GrowthAuditEventRead.model_validate(event) for event in events],
        findings_count=findings_count,
        tasks_count=tasks_count,
    )


@router.get(
    "/{project_id}/growth-audit/runs/{run_id}/pages",
    response_model=GrowthAuditPagesListResponse,
)
async def list_growth_audit_pages_endpoint(
    project_id: UUID,
    run_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> GrowthAuditPagesListResponse:
    await get_project_in_default_workspace(project_id, session)
    try:
        pages = await list_growth_audit_pages(session, project_id, run_id)
    except Exception as exc:
        raise _map_growth_audit_error(
            exc,
            project_id=project_id,
            run_id=run_id,
        ) from exc
    return GrowthAuditPagesListResponse(
        pages=[GrowthAuditPageRead.model_validate(page) for page in pages]
    )


@router.get(
    "/{project_id}/growth-audit/runs/{run_id}/events",
    response_model=GrowthAuditEventsListResponse,
)
async def list_growth_audit_events_endpoint(
    project_id: UUID,
    run_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> GrowthAuditEventsListResponse:
    await get_project_in_default_workspace(project_id, session)
    try:
        events = await list_growth_audit_events(session, project_id, run_id)
    except Exception as exc:
        raise _map_growth_audit_error(
            exc,
            project_id=project_id,
            run_id=run_id,
        ) from exc
    return GrowthAuditEventsListResponse(
        events=[GrowthAuditEventRead.model_validate(event) for event in events]
    )
