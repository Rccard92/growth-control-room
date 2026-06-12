from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_seo import ShopifyCollection
from app.models.seo_optimizer import SeoEntityAnalysis
from app.models.shopify import ShopifyStore
from app.services.content.seo_scoring_constants import (
    COLLECTION_DESC_MIN,
    COLLECTION_WEIGHTS,
    HANDLE_MIN,
    META_DESC_MAX,
    META_DESC_MIN,
    SCORE_GOOD,
    SCORE_OPPORTUNITY,
    SCORE_WARNING,
    SEO_TITLE_MAX,
    SEO_TITLE_MIN,
    TITLE_MIN,
)


@dataclass
class CollectionAnalyzeResult:
    collections_analyzed: int = 0
    critical: int = 0
    warnings: int = 0
    opportunities: int = 0


def _text_len(value: str | None) -> int:
    return len((value or "").strip())


def _score_range(value_len: int, optimal_min: int, optimal_max: int) -> int:
    if value_len == 0:
        return 0
    if optimal_min <= value_len <= optimal_max:
        return 100
    if value_len < optimal_min:
        return max(20, int(100 * value_len / optimal_min))
    return max(40, 100 - int((value_len - optimal_max) / 2))


def _severity_from_score(score: int) -> str:
    if score >= SCORE_GOOD:
        return "good"
    if score >= SCORE_OPPORTUNITY:
        return "opportunity"
    if score >= SCORE_WARNING:
        return "warning"
    return "critical"


def _analyze_collection(collection: ShopifyCollection) -> dict:
    issues: list[dict] = []
    recommendations: list[dict] = []

    title_len = _text_len(collection.title)
    score_title = 100 if title_len >= TITLE_MIN else (50 if title_len > 0 else 0)
    if score_title < 100:
        issues.append(
            {
                "code": "weak_title",
                "severity": "warning",
                "message": "Titolo collection debole",
                "field": "title",
            }
        )

    handle = (collection.handle or "").strip()
    score_handle = 100 if len(handle) >= HANDLE_MIN else (50 if handle else 0)

    desc_len = _text_len(collection.description_text)
    score_description = (
        100
        if desc_len >= COLLECTION_DESC_MIN
        else max(0, int(100 * desc_len / COLLECTION_DESC_MIN))
        if desc_len
        else 0
    )
    if desc_len < COLLECTION_DESC_MIN:
        issues.append(
            {
                "code": "weak_description",
                "severity": "critical" if desc_len == 0 else "warning",
                "message": "Description collection insufficiente",
                "field": "description",
            }
        )
        recommendations.append({"action": "expand_description", "priority": "medium"})

    seo_title_len = _text_len(collection.seo_title)
    score_seo_title = _score_range(seo_title_len, SEO_TITLE_MIN, SEO_TITLE_MAX)
    if seo_title_len == 0:
        issues.append(
            {
                "code": "missing_seo_title",
                "severity": "warning",
                "message": "SEO title collection mancante",
                "field": "seo_title",
            }
        )

    meta_len = _text_len(collection.seo_description)
    score_meta = _score_range(meta_len, META_DESC_MIN, META_DESC_MAX)
    if meta_len == 0:
        issues.append(
            {
                "code": "missing_meta_description",
                "severity": "warning",
                "message": "Meta description collection mancante",
                "field": "seo_description",
            }
        )

    if collection.image_url and not (collection.image_alt or "").strip():
        score_image_alt = 0
        issues.append(
            {
                "code": "missing_image_alt",
                "severity": "opportunity",
                "message": "Immagine collection senza alt",
                "field": "image_alt",
            }
        )
    elif collection.image_url:
        score_image_alt = 100
    else:
        score_image_alt = 100

    weights = COLLECTION_WEIGHTS
    score_total = int(
        (
            score_title * weights["title"]
            + score_handle * weights["handle"]
            + score_description * weights["description"]
            + score_seo_title * weights["seo_title"]
            + score_meta * weights["meta_description"]
            + score_image_alt * weights["image_alt"]
        )
        / sum(weights.values())
    )

    if (collection.products_count or 0) >= 3 and desc_len < COLLECTION_DESC_MIN:
        recommendations.append(
            {
                "action": "pillar_collection_copy",
                "priority": "high",
                "reason": f"{collection.products_count} prodotti in collection",
            }
        )

    return {
        "score_total": score_total,
        "score_title": score_title,
        "score_seo_title": score_seo_title,
        "score_meta_description": score_meta,
        "score_description": score_description,
        "score_image_alt": score_image_alt,
        "score_handle": score_handle,
        "score_tags": 100,
        "severity": _severity_from_score(score_total),
        "issues": issues,
        "recommendations": recommendations,
    }


async def analyze_collections_for_store(
    store: ShopifyStore,
    session: AsyncSession,
) -> CollectionAnalyzeResult:
    collections = (
        await session.execute(
            select(ShopifyCollection).where(
                ShopifyCollection.shopify_store_id == store.id
            )
        )
    ).scalars().all()

    result = CollectionAnalyzeResult()
    now = datetime.now(UTC)

    for collection in collections:
        analysis = _analyze_collection(collection)

        existing = (
            await session.execute(
                select(SeoEntityAnalysis).where(
                    SeoEntityAnalysis.project_id == store.project_id,
                    SeoEntityAnalysis.shopify_store_id == store.id,
                    SeoEntityAnalysis.entity_type == "collection",
                    SeoEntityAnalysis.entity_id == collection.id,
                )
            )
        ).scalar_one_or_none()

        fields = {
            "entity_gid": collection.shopify_gid,
            "entity_title": collection.title,
            "last_analyzed_at": now,
            **analysis,
        }

        if existing is None:
            session.add(
                SeoEntityAnalysis(
                    project_id=store.project_id,
                    shopify_store_id=store.id,
                    entity_type="collection",
                    entity_id=collection.id,
                    **fields,
                )
            )
        else:
            for key, val in fields.items():
                setattr(existing, key, val)

        result.collections_analyzed += 1
        sev = analysis["severity"]
        if sev == "critical":
            result.critical += 1
        elif sev == "warning":
            result.warnings += 1
        elif sev == "opportunity":
            result.opportunities += 1

    await session.commit()
    return result
