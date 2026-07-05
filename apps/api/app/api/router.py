from fastapi import APIRouter

from app.api.routes import (
    ai_model_settings,
    ai_usage,
    brand_intelligence,
    content_seo,
    google_integrations,
    growth_audit,
    health,
    seo_skills,
    shopify,
    shopify_oauth,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(shopify.router)
api_router.include_router(shopify_oauth.router)
api_router.include_router(google_integrations.callback_router)
api_router.include_router(content_seo.router)
api_router.include_router(seo_skills.router)
api_router.include_router(growth_audit.router)
api_router.include_router(brand_intelligence.router)
api_router.include_router(ai_usage.router)
api_router.include_router(ai_usage.global_router)
api_router.include_router(ai_model_settings.router)
api_router.include_router(ai_model_settings.global_router)
