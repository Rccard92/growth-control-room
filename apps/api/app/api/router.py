from fastapi import APIRouter

from app.api.routes import health, shopify, shopify_oauth

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(shopify.router)
api_router.include_router(shopify_oauth.router)
