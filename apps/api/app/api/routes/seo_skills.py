from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.seo_skills import SeoSkillCatalogResponse
from app.services.projects import get_project_in_default_workspace
from app.services.seo_skills.catalog_loader import (
    _build_counts,
    load_seo_skill_catalog,
)

router = APIRouter(prefix="/projects", tags=["seo-skills"])


@router.get(
    "/{project_id}/seo-skills/catalog",
    response_model=SeoSkillCatalogResponse,
    response_model_by_alias=True,
)
async def get_seo_skill_catalog(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> SeoSkillCatalogResponse:
    await get_project_in_default_workspace(project_id, session)
    skills = load_seo_skill_catalog()
    return SeoSkillCatalogResponse(skills=skills, counts=_build_counts(skills))
