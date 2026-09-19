from fastapi import APIRouter, Depends

from app.api.deps import require_user
from app.api.routes import (
    ai_model_settings,
    ai_usage,
    auth,
    brand_intelligence,
    content_seo,
    dataforseo,
    google_integrations,
    growth_audit,
    health,
    seo_skills,
    shopify,
    shopify_oauth,
)

# Reachable without a session: health, sign-in, and the provider OAuth callbacks,
# which are called by Shopify/Google and are authenticated by their signed state.
public_api_router = APIRouter()
public_api_router.include_router(health.router, tags=["health"])
public_api_router.include_router(auth.router)
public_api_router.include_router(shopify_oauth.router)
public_api_router.include_router(google_integrations.callback_router)

# Everything else requires a signed-in user.
api_router = APIRouter(dependencies=[Depends(require_user)])
api_router.include_router(shopify.router)
api_router.include_router(content_seo.router)
api_router.include_router(seo_skills.router)
api_router.include_router(growth_audit.router)
api_router.include_router(dataforseo.router)
api_router.include_router(brand_intelligence.router)
api_router.include_router(ai_usage.router)
api_router.include_router(ai_usage.global_router)
api_router.include_router(ai_model_settings.router)
api_router.include_router(ai_model_settings.global_router)
