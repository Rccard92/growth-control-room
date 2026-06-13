"""Brand Knowledge Score computation — v0.3.0 profile-centric."""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brand_intelligence import BrandProfile

SECTION_LABELS = {
    "brandProfile": "Brand Profile",
}


@dataclass
class BrandKnowledgeScore:
    overall_score: int
    status: str
    section_scores: dict[str, int]
    missing_required: list[str]
    recommendations: list[str]


def _has_text(value: str | None) -> bool:
    return bool(value and value.strip())


def _has_list(value: list | None) -> bool:
    return bool(value and len(value) > 0)


def profile_has_minimum(profile: BrandProfile | None) -> bool:
    if not profile:
        return False
    has_identity = _has_text(profile.brand_name) and (
        _has_text(profile.short_description) or _has_text(profile.story)
    )
    return has_identity


def profile_is_complete(profile: BrandProfile | None) -> bool:
    if not profile_has_minimum(profile):
        return False
    assert profile is not None
    return bool(
        _has_text(profile.website_url)
        and (_has_text(profile.mission) or _has_list(profile.values))
        and _has_text(profile.ai_summary or profile.short_description)
    )


def profile_missing_context(profile: BrandProfile | None) -> list[str]:
    if not profile:
        return ["brand_name", "short_description", "website_url"]
    missing: list[str] = []
    if not _has_text(profile.brand_name):
        missing.append("brand_name")
    if not _has_text(profile.short_description) and not _has_text(profile.story):
        missing.append("short_description")
    if not _has_text(profile.website_url):
        missing.append("website_url")
    if not _has_text(profile.mission):
        missing.append("mission")
    if not _has_list(profile.values):
        missing.append("values")
    return missing


def _score_brand_profile(profile: BrandProfile | None) -> tuple[int, list[str], list[str]]:
    missing: list[str] = []
    recs: list[str] = []
    if not profile:
        return 0, ["brand_name", "short_description", "website_url"], [
            "Crea il Brand Profile con nome, sito e descrizione."
        ]

    points = 0
    if _has_text(profile.brand_name):
        points += 20
    else:
        missing.append("brand_name")

    if _has_text(profile.website_url):
        points += 15
    else:
        missing.append("website_url")

    if _has_text(profile.short_description) or _has_text(profile.story):
        points += 20
    else:
        missing.append("short_description")

    if _has_text(profile.mission):
        points += 10
    if _has_list(profile.values):
        points += 10
    if _has_list(profile.differentiators):
        points += 10
    if _has_text(profile.origin_notes) or _has_text(profile.production_notes):
        points += 5
    if _has_text(profile.tone_notes):
        points += 5
    if _has_text(profile.ai_summary):
        points += 5

    if points < 60:
        recs.append("Completa il Brand Profile: usa Recupera informazioni o compila manualmente.")
    elif points < 80:
        recs.append("Arricchisci missione, valori e note tono/clienti per un profilo più completo.")

    return min(points, 100), missing, recs


def _overall_status(score: int) -> str:
    if score >= 80:
        return "ready"
    if score >= 50:
        return "developing"
    return "incomplete"


async def compute_brand_knowledge_score(
    session: AsyncSession,
    project_id: UUID,
) -> BrandKnowledgeScore:
    profile = (
        await session.execute(select(BrandProfile).where(BrandProfile.project_id == project_id))
    ).scalar_one_or_none()

    section_score, missing, recs = _score_brand_profile(profile)
    section_scores = {"brandProfile": section_score}

    return BrandKnowledgeScore(
        overall_score=section_score,
        status=_overall_status(section_score),
        section_scores=section_scores,
        missing_required=missing,
        recommendations=recs[:6],
    )


def score_to_response(score: BrandKnowledgeScore) -> dict:
    return {
        "overall_score": score.overall_score,
        "status": score.status,
        "section_scores": score.section_scores,
        "missing_required": score.missing_required,
        "recommendations": score.recommendations,
    }
