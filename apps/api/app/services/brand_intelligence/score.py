"""Brand Knowledge Score computation."""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brand_intelligence import (
    BrandAiGuardrail,
    BrandAsset,
    BrandAudienceInsight,
    BrandClaimRule,
    BrandContentPillar,
    BrandProductKnowledge,
    BrandProfile,
    BrandSeoStrategy,
    BrandVoice,
)

SECTION_WEIGHTS = {
    "brandProfile": 0.15,
    "voiceTone": 0.10,
    "productsCategories": 0.15,
    "audience": 0.10,
    "claimsCompliance": 0.15,
    "seoStrategy": 0.10,
    "contentPillars": 0.10,
    "aiGuardrails": 0.15,
    "assets": 0.10,
}

SECTION_LABELS = {
    "brandProfile": "Brand Profile",
    "voiceTone": "Voice & Tone",
    "productsCategories": "Products & Categories",
    "audience": "Audience",
    "claimsCompliance": "Claims & Compliance",
    "seoStrategy": "SEO Strategy",
    "contentPillars": "Content Pillars",
    "aiGuardrails": "AI Guardrails",
    "assets": "Assets",
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


def _score_brand_profile(profile: BrandProfile | None) -> tuple[int, list[str], list[str]]:
    missing: list[str] = []
    recs: list[str] = []
    if not profile:
        return 0, ["brand_name", "short_description", "website_url_or_industry"], [
            "Compila il profilo brand con nome, descrizione e sito o settore."
        ]

    points = 0
    if _has_text(profile.brand_name):
        points += 35
    else:
        missing.append("brand_name")

    if _has_text(profile.short_description) or _has_text(profile.story):
        points += 30
    else:
        missing.append("short_description")

    if _has_text(profile.website_url) or _has_text(profile.industry):
        points += 35
    else:
        missing.append("website_url_or_industry")

    if points < 100:
        recs.append("Completa nome brand, descrizione breve e URL sito o settore.")
    return min(points, 100), missing, recs


def _score_voice(voice: BrandVoice | None) -> tuple[int, list[str], list[str]]:
    missing: list[str] = []
    recs: list[str] = []
    if not voice:
        return 0, ["tone"], ["Definisci il tono di voce del brand."]

    points = 0
    if _has_text(voice.tone):
        points += 50
    else:
        missing.append("tone")

    if (
        _has_text(voice.style_notes)
        or _has_list(voice.words_to_use)
        or _has_list(voice.words_to_avoid)
    ):
        points += 50
    else:
        recs.append("Aggiungi note di stile o parole da usare/evitare.")

    if points < 100 and "tone" not in missing:
        recs.append("Arricchisci voice & tone con esempi e parole chiave.")
    return min(points, 100), missing, recs


def _score_products(products: list[BrandProductKnowledge]) -> tuple[int, list[str], list[str]]:
    missing: list[str] = []
    recs: list[str] = []
    valid = [p for p in products if _has_text(p.name) and _has_text(p.description)]
    if not valid:
        return 0, ["product_or_category_knowledge"], [
            "Aggiungi almeno un prodotto o categoria con nome e descrizione."
        ]
    score = min(100, 40 + len(valid) * 20)
    if len(valid) < 2:
        recs.append("Aggiungi più prodotti/categorie per arricchire la knowledge base.")
    return score, missing, recs


def _score_audience(audience: list[BrandAudienceInsight]) -> tuple[int, list[str], list[str]]:
    if not audience:
        return 0, [], ["Definisci almeno un segmento audience con nome."]
    valid = [a for a in audience if _has_text(a.segment_name)]
    if not valid:
        return 20, [], ["Completa il nome del segmento audience."]
    return min(100, 50 + len(valid) * 25), [], []


def _score_claims(claims: list[BrandClaimRule]) -> tuple[int, list[str], list[str]]:
    missing: list[str] = []
    recs: list[str] = []
    forbidden_or_caution = [
        c for c in claims if c.rule_type in ("forbidden", "caution")
    ]
    if not forbidden_or_caution:
        return 0, ["claim_forbidden_or_caution"], [
            "Aggiungi almeno un claim vietato o da usare con cautela."
        ]
    score = min(100, 50 + len(forbidden_or_caution) * 15)
    if len(claims) < 2:
        recs.append("Aggiungi più regole su claim consentiti e disclaimer.")
    return score, missing, recs


def _score_seo(seo: BrandSeoStrategy | None) -> tuple[int, list[str], list[str]]:
    if not seo or not _has_list(seo.primary_keywords):
        return 0, [], ["Definisci keyword principali nella strategia SEO."]
    points = 60
    if _has_list(seo.secondary_keywords):
        points += 20
    if _has_list(seo.priority_pages):
        points += 20
    return min(points, 100), [], []


def _score_pillars(pillars: list[BrandContentPillar]) -> tuple[int, list[str], list[str]]:
    valid = [p for p in pillars if _has_text(p.name)]
    if not valid:
        return 0, [], ["Crea almeno un content pillar."]
    return min(100, 50 + len(valid) * 25), [], []


def _score_guardrails(guardrails: list[BrandAiGuardrail]) -> tuple[int, list[str], list[str]]:
    missing: list[str] = []
    must_not = [g for g in guardrails if g.rule_type == "must_not"]
    if not must_not:
        return 0, ["must_not_guardrail"], [
            "Aggiungi almeno una regola AI must_not (cosa l'AI non deve fare)."
        ]
    return min(100, 50 + len(must_not) * 20 + len(guardrails) * 5), missing, []


def _score_assets(assets: list[BrandAsset]) -> tuple[int, list[str], list[str]]:
    if not assets:
        return 0, [], ["Opzionale: aggiungi asset brand (logo, colori, font)."]
    return min(100, 40 + len(assets) * 15), [], []


def _overall_status(score: int) -> str:
    if score >= 80:
        return "ready"
    if score >= 60:
        return "developing"
    return "incomplete"


async def compute_brand_knowledge_score(
    session: AsyncSession,
    project_id: UUID,
) -> BrandKnowledgeScore:
    profile = (
        await session.execute(select(BrandProfile).where(BrandProfile.project_id == project_id))
    ).scalar_one_or_none()
    voice = (
        await session.execute(select(BrandVoice).where(BrandVoice.project_id == project_id))
    ).scalar_one_or_none()
    products = list(
        (
            await session.execute(
                select(BrandProductKnowledge).where(
                    BrandProductKnowledge.project_id == project_id
                )
            )
        ).scalars().all()
    )
    audience = list(
        (
            await session.execute(
                select(BrandAudienceInsight).where(
                    BrandAudienceInsight.project_id == project_id
                )
            )
        ).scalars().all()
    )
    claims = list(
        (
            await session.execute(
                select(BrandClaimRule).where(BrandClaimRule.project_id == project_id)
            )
        ).scalars().all()
    )
    seo = (
        await session.execute(
            select(BrandSeoStrategy).where(BrandSeoStrategy.project_id == project_id)
        )
    ).scalar_one_or_none()
    pillars = list(
        (
            await session.execute(
                select(BrandContentPillar).where(
                    BrandContentPillar.project_id == project_id
                )
            )
        ).scalars().all()
    )
    guardrails = list(
        (
            await session.execute(
                select(BrandAiGuardrail).where(
                    BrandAiGuardrail.project_id == project_id
                )
            )
        ).scalars().all()
    )
    assets = list(
        (
            await session.execute(
                select(BrandAsset).where(BrandAsset.project_id == project_id)
            )
        ).scalars().all()
    )

    scorers = {
        "brandProfile": _score_brand_profile(profile),
        "voiceTone": _score_voice(voice),
        "productsCategories": _score_products(products),
        "audience": _score_audience(audience),
        "claimsCompliance": _score_claims(claims),
        "seoStrategy": _score_seo(seo),
        "contentPillars": _score_pillars(pillars),
        "aiGuardrails": _score_guardrails(guardrails),
        "assets": _score_assets(assets),
    }

    section_scores = {k: v[0] for k, v in scorers.items()}
    missing_required: list[str] = []
    recommendations: list[str] = []
    for _key, (_score, missing, recs) in scorers.items():
        missing_required.extend(missing)
        recommendations.extend(recs)

    weighted = sum(
        section_scores[key] * SECTION_WEIGHTS[key] for key in SECTION_WEIGHTS
    )
    overall = round(weighted)

    return BrandKnowledgeScore(
        overall_score=overall,
        status=_overall_status(overall),
        section_scores=section_scores,
        missing_required=list(dict.fromkeys(missing_required)),
        recommendations=list(dict.fromkeys(recommendations))[:8],
    )


def score_to_response(score: BrandKnowledgeScore) -> dict:
    return {
        "overall_score": score.overall_score,
        "status": score.status,
        "section_scores": score.section_scores,
        "missing_required": score.missing_required,
        "recommendations": score.recommendations,
    }
