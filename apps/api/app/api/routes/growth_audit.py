import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.growth_audit import (
    GrowthAuditEventRead,
    GrowthAuditEventsListResponse,
    GrowthAuditFindingRead,
    GrowthAuditFindingsListResponse,
    GrowthAuditPageAiAnalysisRequest,
    GrowthAuditPageAiAnalysisResponse,
    GrowthAuditPagePerformanceAnalysisRequest,
    GrowthAuditPagePerformanceAnalysisResponse,
    GrowthAuditPageRead,
    GrowthAuditPageRescanRequest,
    GrowthAuditPageRescanResponse,
    GrowthAuditPageResultRead,
    GrowthAuditPageResultsListResponse,
    GrowthAuditPagesListResponse,
    GrowthAuditRunCreateRequest,
    GrowthAuditRunDetailResponse,
    GrowthAuditRunRead,
    GrowthAuditRunsListResponse,
    GrowthAuditStartResponse,
    GrowthAuditTaskRead,
    GrowthAuditTasksListResponse,
)
from app.services.google.exceptions import GoogleApiRequestError, GoogleIntegrationNotConfiguredError
from app.services.growth_audit.exceptions import (
    GrowthAuditError,
    GrowthAuditRunNotFoundError,
    GrowthAuditValidationError,
)
from app.services.growth_audit.page_ai_analysis import (
    analyze_growth_audit_page_with_ai,
    list_growth_audit_page_results,
)
from app.services.growth_audit.page_performance_analysis import (
    analyze_growth_audit_page_performance,
)
from app.services.growth_audit.run_service import (
    get_growth_audit_run_detail,
    list_growth_audit_events,
    list_growth_audit_findings,
    list_growth_audit_pages,
    list_growth_audit_runs,
    list_growth_audit_tasks,
    rescan_growth_audit_page,
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
    if isinstance(exc, GoogleIntegrationNotConfiguredError):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    if isinstance(exc, GoogleApiRequestError):
        return HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
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


@router.get(
    "/{project_id}/growth-audit/runs/{run_id}/findings",
    response_model=GrowthAuditFindingsListResponse,
)
async def list_growth_audit_findings_endpoint(
    project_id: UUID,
    run_id: UUID,
    page_id: UUID | None = Query(default=None, alias="pageId"),
    severity: str | None = Query(default=None),
    category: str | None = Query(default=None),
    status: str | None = Query(default=None),
    session: AsyncSession = Depends(get_db),
) -> GrowthAuditFindingsListResponse:
    await get_project_in_default_workspace(project_id, session)
    try:
        findings = await list_growth_audit_findings(
            session,
            project_id,
            run_id,
            page_id=page_id,
            severity=severity,
            category=category,
            status=status,
        )
    except Exception as exc:
        raise _map_growth_audit_error(
            exc,
            project_id=project_id,
            run_id=run_id,
        ) from exc
    return GrowthAuditFindingsListResponse(
        findings=[GrowthAuditFindingRead.model_validate(f) for f in findings]
    )


@router.get(
    "/{project_id}/growth-audit/runs/{run_id}/tasks",
    response_model=GrowthAuditTasksListResponse,
)
async def list_growth_audit_tasks_endpoint(
    project_id: UUID,
    run_id: UUID,
    page_id: UUID | None = Query(default=None, alias="pageId"),
    priority: str | None = Query(default=None),
    owner_type: str | None = Query(default=None, alias="ownerType"),
    status: str | None = Query(default=None),
    session: AsyncSession = Depends(get_db),
) -> GrowthAuditTasksListResponse:
    await get_project_in_default_workspace(project_id, session)
    try:
        tasks = await list_growth_audit_tasks(
            session,
            project_id,
            run_id,
            page_id=page_id,
            priority=priority,
            owner_type=owner_type,
            status=status,
        )
    except Exception as exc:
        raise _map_growth_audit_error(
            exc,
            project_id=project_id,
            run_id=run_id,
        ) from exc
    return GrowthAuditTasksListResponse(
        tasks=[GrowthAuditTaskRead.model_validate(t) for t in tasks]
    )


@router.post(
    "/{project_id}/growth-audit/runs/{run_id}/pages/{page_id}/rescan",
    response_model=GrowthAuditPageRescanResponse,
    status_code=status.HTTP_200_OK,
)
async def rescan_growth_audit_page_endpoint(
    project_id: UUID,
    run_id: UUID,
    page_id: UUID,
    request: GrowthAuditPageRescanRequest,
    session: AsyncSession = Depends(get_db),
) -> GrowthAuditPageRescanResponse:
    await get_project_in_default_workspace(project_id, session)
    try:
        run, page, findings_count, tasks_count = await rescan_growth_audit_page(
            session,
            project_id=project_id,
            run_id=run_id,
            page_id=page_id,
            clear_previous_open_items=request.clear_previous_open_items,
            note=request.note,
        )
    except Exception as exc:
        raise _map_growth_audit_error(
            exc,
            project_id=project_id,
            run_id=run_id,
        ) from exc

    message = (
        f"Pagina riscansionata. Score aggiornato: {page.score}."
        if page.status == "analyzed"
        else f"Riscansione fallita: {page.error_message or 'errore sconosciuto'}"
    )
    return GrowthAuditPageRescanResponse(
        run=GrowthAuditRunRead.model_validate(run),
        page=GrowthAuditPageRead.model_validate(page),
        findings_count=findings_count,
        tasks_count=tasks_count,
        message=message,
    )


@router.post(
    "/{project_id}/growth-audit/runs/{run_id}/pages/{page_id}/ai-analysis",
    response_model=GrowthAuditPageAiAnalysisResponse,
    status_code=status.HTTP_200_OK,
)
async def analyze_growth_audit_page_ai_endpoint(
    project_id: UUID,
    run_id: UUID,
    page_id: UUID,
    request: GrowthAuditPageAiAnalysisRequest,
    session: AsyncSession = Depends(get_db),
) -> GrowthAuditPageAiAnalysisResponse:
    await get_project_in_default_workspace(project_id, session)
    try:
        run, page, result, findings_count, tasks_count = await analyze_growth_audit_page_with_ai(
            session,
            project_id=project_id,
            run_id=run_id,
            page_id=page_id,
            provider=request.provider,
            depth=request.depth,
            include_seo=request.include_seo,
            include_geo=request.include_geo,
            include_cro=request.include_cro,
            include_ads_readiness=request.include_ads_readiness,
            note=request.note,
        )
    except Exception as exc:
        raise _map_growth_audit_error(
            exc,
            project_id=project_id,
            run_id=run_id,
        ) from exc

    message = (
        f"Analisi AI completata. Score AI: {result.score}."
        if result.status == "completed"
        else f"Analisi AI fallita: {result.error_message or 'errore sconosciuto'}"
    )
    return GrowthAuditPageAiAnalysisResponse(
        run=GrowthAuditRunRead.model_validate(run),
        page=GrowthAuditPageRead.model_validate(page),
        result=GrowthAuditPageResultRead.model_validate(result),
        findings_count=findings_count,
        tasks_count=tasks_count,
        message=message,
    )


@router.post(
    "/{project_id}/growth-audit/runs/{run_id}/pages/{page_id}/performance-analysis",
    response_model=GrowthAuditPagePerformanceAnalysisResponse,
    status_code=status.HTTP_200_OK,
)
async def analyze_growth_audit_page_performance_endpoint(
    project_id: UUID,
    run_id: UUID,
    page_id: UUID,
    request: GrowthAuditPagePerformanceAnalysisRequest,
    session: AsyncSession = Depends(get_db),
) -> GrowthAuditPagePerformanceAnalysisResponse:
    await get_project_in_default_workspace(project_id, session)
    try:
        run, page, result, findings_count, tasks_count = await analyze_growth_audit_page_performance(
            session,
            project_id=project_id,
            run_id=run_id,
            page_id=page_id,
            strategy=request.strategy,
        )
    except Exception as exc:
        raise _map_growth_audit_error(
            exc,
            project_id=project_id,
            run_id=run_id,
        ) from exc

    message = (
        f"Analisi performance completata. Score: {result.score}."
        if result.status == "completed"
        else f"Analisi performance fallita: {result.error_message or 'errore sconosciuto'}"
    )
    return GrowthAuditPagePerformanceAnalysisResponse(
        run=GrowthAuditRunRead.model_validate(run),
        page=GrowthAuditPageRead.model_validate(page),
        result=GrowthAuditPageResultRead.model_validate(result),
        findings_count=findings_count,
        tasks_count=tasks_count,
        message=message,
    )


@router.get(
    "/{project_id}/growth-audit/runs/{run_id}/pages/{page_id}/results",
    response_model=GrowthAuditPageResultsListResponse,
)
async def list_growth_audit_page_results_endpoint(
    project_id: UUID,
    run_id: UUID,
    page_id: UUID,
    result_type: str | None = Query(default=None, alias="resultType"),
    session: AsyncSession = Depends(get_db),
) -> GrowthAuditPageResultsListResponse:
    await get_project_in_default_workspace(project_id, session)
    try:
        results = await list_growth_audit_page_results(
            session,
            project_id=project_id,
            run_id=run_id,
            page_id=page_id,
            result_type=result_type,
        )
    except Exception as exc:
        raise _map_growth_audit_error(
            exc,
            project_id=project_id,
            run_id=run_id,
        ) from exc
    return GrowthAuditPageResultsListResponse(
        results=[GrowthAuditPageResultRead.model_validate(r) for r in results]
    )
