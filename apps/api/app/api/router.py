from fastapi import APIRouter

from app.api.routes import health, projects, shopify

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(projects.router)
api_router.include_router(shopify.router)
