"""Brand Knowledge Score computation — v0.3.1 modular."""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brand_intelligence import (
    BrandEditorialGuidelines,
    BrandFaqObjections,
    BrandIdentity,
    BrandProductKnowledgeGeneral,
    BrandProductKnowledgeItem,
    BrandProfile,
    BrandSafeClaims,
    BrandVisualIdentity,
)
from app.services.brand_intelligence.faq_objections_service import (
    faq_objections_completion,
    faq_objections_missing_fields,
)
from app.services.brand_intelligence.editorial_guidelines_service import (
    editorial_guidelines_completion,
    editorial_guidelines_missing_fields,
)
from app.services.brand_intelligence.identity_service import (
    identity_completion,
    identity_missing_fields,
)
from app.services.brand_intelligence.product_knowledge_general_service import general_has_content
from app.services.brand_intelligence.safe_claims_service import (
    safe_claims_completion,
    safe_claims_missing_fields,
)
from app.services.brand_intelligence.visual_identity_service import (
    visual_completion,
    visual_missing_fields,
)

SECTION_LABELS = {
    "brandProfile": "Brand Profile",
    "brandIdentity": "Brand Identity",
    "visualIdentity": "Visual Identity",
    "safeClaims": "Safe Claims & Red Flags",
    "productKnowledge": "Product Knowledge",
    "faqObjections": "FAQ & Objections",
    "editorialGuidelines": "Editorial Guidelines",
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
    return _has_text(profile.brand_name) and (
        _has_text(profile.short_description) or _has_text(profile.story)
    )


def profile_is_complete(profile: BrandProfile | None) -> bool:
    if not profile_has_minimum(profile):
        return False
    assert profile is not None
    return bool(
        _has_text(profile.website_url)
        and (_has_text(profile.mission) or _has_list(profile.values))
        and _has_text(profile.ai_summary or profile.short_description)
    )


def profile_missing_fields(profile: BrandProfile | None) -> list[str]:
    if not profile:
        return ["brand_name", "short_description", "website_url"]
    missing: list[str] = []
    if not _has_text(profile.brand_name):
        missing.append("brand_name")
    if not _has_text(profile.short_description) and not _has_text(profile.story):
        missing.append("short_description")
    if not _has_text(profile.website_url):
        missing.append("website_url")
    return missing


def profile_missing_context(profile: BrandProfile | None) -> list[str]:
    return [f"brand_profile.{f}" for f in profile_missing_fields(profile)]


def identity_missing_context(identity: BrandIdentity | None) -> list[str]:
    return [f"brand_identity.{f}" for f in identity_missing_fields(identity)]


def visual_missing_context(visual: BrandVisualIdentity | None) -> list[str]:
    return [f"visual_identity.{f}" for f in visual_missing_fields(visual)]


def safe_claims_missing_context(safe_claims: BrandSafeClaims | None) -> list[str]:
    return [f"safe_claims.{f}" for f in safe_claims_missing_fields(safe_claims)]


def product_knowledge_module_completion(
    general: BrandProductKnowledgeGeneral | None,
    items_count: int,
) -> str:
    has_general = general_has_content(general)
    has_items = items_count > 0
    if has_general and has_items:
        return "complete"
    if has_general or has_items:
        return "partial"
    return "empty"


def product_knowledge_missing_fields(
    general: BrandProductKnowledgeGeneral | None,
    items_count: int,
) -> list[str]:
    missing: list[str] = []
    if not general_has_content(general):
        missing.append("general_knowledge")
    if items_count == 0:
        missing.append("specific_products")
    return missing


def _completion_to_score(status: str) -> int:
    if status == "complete":
        return 100
    if status == "partial":
        return 55
    return 0


def _score_brand_profile(profile: BrandProfile | None) -> tuple[int, list[str], list[str]]:
    missing: list[str] = []
    recs: list[str] = []
    if not profile:
        return 0, ["brand_name"], ["Crea il Brand Profile con nome, sito e descrizione."]

    points = 0
    if _has_text(profile.brand_name):
        points += 25
    else:
        missing.append("brand_name")
    if _has_text(profile.website_url):
        points += 20
    else:
        missing.append("website_url")
    if _has_text(profile.short_description) or _has_text(profile.story):
        points += 25
    else:
        missing.append("short_description")
    if _has_text(profile.mission):
        points += 15
    if _has_list(profile.values):
        points += 15

    if points < 50:
        recs.append("Completa il Brand Profile con nome, sito e descrizione.")
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
    identity = (
        await session.execute(select(BrandIdentity).where(BrandIdentity.project_id == project_id))
    ).scalar_one_or_none()
    visual = (
        await session.execute(
            select(BrandVisualIdentity).where(BrandVisualIdentity.project_id == project_id)
        )
    ).scalar_one_or_none()
    safe_claims = (
        await session.execute(
            select(BrandSafeClaims).where(BrandSafeClaims.project_id == project_id)
        )
    ).scalar_one_or_none()
    pk_general = (
        await session.execute(
            select(BrandProductKnowledgeGeneral).where(
                BrandProductKnowledgeGeneral.project_id == project_id
            )
        )
    ).scalar_one_or_none()
    pk_items_count = (
        await session.execute(
            select(func.count()).select_from(BrandProductKnowledgeItem).where(
                BrandProductKnowledgeItem.project_id == project_id
            )
        )
    ).scalar_one()
    faq_objections = (
        await session.execute(
            select(BrandFaqObjections).where(BrandFaqObjections.project_id == project_id)
        )
    ).scalar_one_or_none()
    editorial_guidelines = (
        await session.execute(
            select(BrandEditorialGuidelines).where(
                BrandEditorialGuidelines.project_id == project_id
            )
        )
    ).scalar_one_or_none()
    items_count = int(pk_items_count or 0)

    profile_score, profile_missing, profile_recs = _score_brand_profile(profile)
    identity_status = identity_completion(identity)
    visual_status = visual_completion(visual)
    safe_claims_status = safe_claims_completion(safe_claims)
    pk_status = product_knowledge_module_completion(pk_general, items_count)
    faq_status = faq_objections_completion(faq_objections)
    eg_status = editorial_guidelines_completion(editorial_guidelines)

    section_scores = {
        "brandProfile": profile_score,
        "brandIdentity": _completion_to_score(identity_status),
        "visualIdentity": _completion_to_score(visual_status),
        "safeClaims": _completion_to_score(safe_claims_status),
        "productKnowledge": _completion_to_score(pk_status),
        "faqObjections": _completion_to_score(faq_status),
        "editorialGuidelines": _completion_to_score(eg_status),
    }
    overall = round(sum(section_scores.values()) / len(section_scores))

    missing_required = (
        profile_missing
        + identity_missing_fields(identity)
        + visual_missing_fields(visual)
        + safe_claims_missing_fields(safe_claims)
        + product_knowledge_missing_fields(pk_general, items_count)
        + faq_objections_missing_fields(faq_objections)
        + editorial_guidelines_missing_fields(editorial_guidelines)
    )
    recs = list(profile_recs)
    if identity_status == "empty":
        recs.append("Compila la Brand Identity con posizionamento e valori.")
    if visual_status == "empty":
        recs.append("Definisci la Visual Identity con logo e palette colori.")
    if safe_claims_status == "empty":
        recs.append("Compila Safe Claims con claim consentiti e vietati.")
    if pk_status == "empty":
        recs.append("Compila Product Knowledge generale e aggiungi almeno un prodotto Shopify.")
    if faq_status == "empty":
        recs.append("Compila FAQ & Objections con domande frequenti e obiezioni clienti.")
    if eg_status == "empty":
        recs.append("Compila Editorial Guidelines con filosofia contenuti e persone del brand.")

    return BrandKnowledgeScore(
        overall_score=overall,
        status=_overall_status(overall),
        section_scores=section_scores,
        missing_required=missing_required,
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
