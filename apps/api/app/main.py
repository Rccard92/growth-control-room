from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.api.routes import debug, projects
from app.core.config import settings
from app.db.session import close_db, init_db


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
app.include_router(debug.router, prefix="/api")
app.include_router(api_router, prefix="/api")


@app.get("/health")
async def root_health() -> dict[str, str]:
    return {"status": "ok", "service": "growth-control-room-api"}
