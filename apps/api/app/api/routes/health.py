from fastapi import APIRouter

from connectors.registry import list_connectors
from skills.registry import list_skills

router = APIRouter()


@router.get("/health")
async def health_check() -> dict:
    return {
        "status": "ok",
        "service": "growth-control-room-api",
        "connectors_loaded": len(list_connectors()) > 0,
        "connectors_count": len(list_connectors()),
        "skills_loaded": True,
        "skills_count": len(list_skills()),
    }
