from fastapi import APIRouter

from app.api.routes import brand_intelligence, content_seo, health, shopify, shopify_oauth

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(shopify.router)
api_router.include_router(shopify_oauth.router)
api_router.include_router(content_seo.router)
api_router.include_router(brand_intelligence.router)
