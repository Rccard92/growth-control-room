from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.api.routes import debug, google_integrations, projects
from app.api.validation_helpers import is_json_string_body_validation_error
from app.core.config import settings
from app.db.session import close_db, init_db
from app.services.ai.exceptions import AiBudgetExceededError, AiSingleRequestBlockedError
from app.services.dataforseo.exceptions import (
    DataForSeoBudgetExceededError,
    DataForSeoRealCallsDisabledError,
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title="Growth Control Room API",
    description="API per la piattaforma multi-brand e-commerce/marketing",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router, prefix="/api")
app.include_router(google_integrations.router, prefix="/api")
app.include_router(debug.router, prefix="/api")
app.include_router(api_router, prefix="/api")


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = exc.errors()
    if is_json_string_body_validation_error(errors):
        return JSONResponse(
            status_code=422,
            content={"detail": "Request body must be a JSON object, not a JSON string."},
        )
    return JSONResponse(status_code=422, content={"detail": errors})


@app.exception_handler(AiBudgetExceededError)
async def ai_budget_exceeded_handler(_request: Request, exc: AiBudgetExceededError) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"detail": exc.message},
    )


@app.exception_handler(AiSingleRequestBlockedError)
async def ai_single_request_blocked_handler(
    _request: Request, exc: AiSingleRequestBlockedError
) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"detail": exc.message},
    )


@app.exception_handler(DataForSeoRealCallsDisabledError)
async def dataforseo_real_calls_disabled_handler(
    _request: Request, exc: DataForSeoRealCallsDisabledError
) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={"detail": exc.message},
    )


@app.exception_handler(DataForSeoBudgetExceededError)
async def dataforseo_budget_exceeded_handler(
    _request: Request, exc: DataForSeoBudgetExceededError
) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"detail": exc.message},
    )


@app.get("/health")
async def root_health() -> dict[str, str]:
    return {"status": "ok", "service": "growth-control-room-api"}
