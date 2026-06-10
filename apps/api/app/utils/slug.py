import re
import unicodedata


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_text.lower()).strip("-")
    return slug or "project"


async def unique_project_slug(session, workspace_id, name: str) -> str:
    from sqlalchemy import select

    from app.models.project import Project

    base = slugify(name)
    candidate = base
    suffix = 1

    while True:
        result = await session.execute(
            select(Project.id).where(
                Project.workspace_id == workspace_id,
                Project.slug == candidate,
            )
        )
        if result.scalar_one_or_none() is None:
            return candidate
        suffix += 1
        candidate = f"{base}-{suffix}"
