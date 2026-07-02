"""SEO skills route registration tests."""

import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

from app.api.routes import seo_skills


def test_seo_skills_catalog_route_registered() -> None:
    paths = {route.path for route in seo_skills.router.routes}
    assert "/projects/{project_id}/seo-skills/catalog" in paths
