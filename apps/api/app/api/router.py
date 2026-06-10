from fastapi import APIRouter

from app.api.routes import health, shopify

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(shopify.router)
