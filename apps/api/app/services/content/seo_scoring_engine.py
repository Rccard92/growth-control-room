from typing import Any

from app.models.seo_optimizer import SeoEntityAnalysis
from app.services.content.seo_scoring_constants import (
    COLLECTION_DESC_MIN,
    COLLECTION_WEIGHTS,
    HANDLE_MIN,
    META_DESC_MAX,
    META_DESC_MIN,
    PRODUCT_DESC_MIN,
    PRODUCT_WEIGHTS,
    SCORE_GOOD,
    SCORE_OPPORTUNITY,
    SCORE_WARNING,
    SEO_TITLE_MAX,
    SEO_TITLE_MIN,
    TITLE_MIN,
)
from app.services.content.seo_skill_loader import load_seo_skill_context

PRODUCT_BREAKDOWN_KEYS = (
    ("title", "score_title", "title", PRODUCT_WEIGHTS["title"]),
    ("seoTitle", "score_seo_title", "seo_title", PRODUCT_WEIGHTS["seo_title"]),
    ("metaDescription", "score_meta_description", "seo_description", PRODUCT_WEIGHTS["meta_description"]),
    ("description", "score_description", "description", PRODUCT_WEIGHTS["description"]),
    ("handle", "score_handle", "handle", PRODUCT_WEIGHTS["handle"]),
    ("imageAlt", "score_image_alt", "media_images", PRODUCT_WEIGHTS["image_alt"]),
)

COLLECTION_BREAKDOWN_KEYS = (
    ("title", "score_title", "title", COLLECTION_WEIGHTS["title"]),
    ("seoTitle", "score_seo_title", "seo_title", COLLECTION_WEIGHTS["seo_title"]),
    ("metaDescription", "score_meta_description", "seo_description", COLLECTION_WEIGHTS["meta_description"]),
    ("description", "score_description", "description", COLLECTION_WEIGHTS["description"]),
    ("handle", "score_handle", "handle", COLLECTION_WEIGHTS["handle"]),
    ("imageAlt", "score_image_alt", "image_alt", COLLECTION_WEIGHTS["image_alt"]),
)

ISSUE_FIELD_ALIASES: dict[str, str] = {
    "title": "title",
    "seo_title": "seoTitle",
    "seo_description": "metaDescription",
    "description": "description",
    "handle": "handle",
    "media_images": "imageAlt",
    "image_alt": "imageAlt",
    "product_type": "title",
}


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


def severity_from_score(score: int, boost: bool = False) -> str:
    if score >= SCORE_GOOD:
        base = "good"
    elif score >= SCORE_OPPORTUNITY:
        base = "opportunity"
    elif score >= SCORE_WARNING:
        base = "warning"
    else:
        base = "critical"
    if boost and base in ("opportunity", "good"):
        return "warning"
    if boost and base == "warning":
        return "critical"
    return base


def weighted_points(component_score: int, max_points: int) -> int:
    return round(component_score * max_points / 100)


def build_score_breakdown(
    *,
    entity_type: str,
    component_scores: dict[str, int],
    issues: list[dict[str, Any]] | None,
) -> dict[str, dict[str, Any]]:
    keys = PRODUCT_BREAKDOWN_KEYS if entity_type == "product" else COLLECTION_BREAKDOWN_KEYS
    issues_by_key: dict[str, list[dict[str, Any]]] = {k: [] for k, _, _, _ in keys}
    for issue in issues or []:
        raw_field = str(issue.get("field", ""))
        breakdown_key = ISSUE_FIELD_ALIASES.get(raw_field)
        if breakdown_key and breakdown_key in issues_by_key:
            issues_by_key[breakdown_key].append(issue)

    breakdown: dict[str, dict[str, Any]] = {}
    for key, score_attr, _, max_points in keys:
        comp_score = component_scores.get(score_attr, 0)
        breakdown[key] = {
            "score": weighted_points(comp_score, max_points),
            "max": max_points,
            "issues": issues_by_key[key],
        }
    return breakdown


def rebuild_score_breakdown_from_analysis(analysis: SeoEntityAnalysis) -> dict[str, dict[str, Any]]:
    if analysis.score_breakdown:
        return analysis.score_breakdown
    component_scores = {
        "score_title": analysis.score_title,
        "score_seo_title": analysis.score_seo_title,
        "score_meta_description": analysis.score_meta_description,
        "score_description": analysis.score_description,
        "score_handle": analysis.score_handle,
        "score_image_alt": analysis.score_image_alt,
        "score_tags": analysis.score_tags,
    }
    return build_score_breakdown(
        entity_type=analysis.entity_type,
        component_scores=component_scores,
        issues=analysis.issues,
    )


def compute_total_from_breakdown(breakdown: dict[str, dict[str, Any]]) -> int:
    return sum(item.get("score", 0) for item in breakdown.values())


def score_product(
    *,
    title: str | None,
    seo_title: str | None,
    seo_description: str | None,
    description_text: str | None,
    handle: str | None,
    media_images: list[dict[str, Any]] | None,
    featured_image_url: str | None,
    product_type: str | None,
    is_best_seller: bool = False,
) -> dict[str, Any]:
    load_seo_skill_context()
    issues: list[dict[str, Any]] = []
    recommendations: list[dict[str, Any]] = []

    title_len = _text_len(title)
    score_title = 100 if title_len >= TITLE_MIN else (50 if title_len > 0 else 0)
    if score_title < 100:
        issues.append(
            {
                "code": "weak_title",
                "severity": "warning",
                "message": "Titolo prodotto assente o troppo corto",
                "field": "title",
            }
        )

    seo_title_len = _text_len(seo_title)
    score_seo_title = _score_range(seo_title_len, SEO_TITLE_MIN, SEO_TITLE_MAX)
    if seo_title_len == 0:
        issues.append(
            {
                "code": "missing_seo_title",
                "severity": "critical",
                "message": "SEO title mancante",
                "field": "seo_title",
            }
        )
        recommendations.append({"action": "add_seo_title", "priority": "high"})

    meta_len = _text_len(seo_description)
    score_meta = _score_range(meta_len, META_DESC_MIN, META_DESC_MAX)
    if meta_len == 0:
        issues.append(
            {
                "code": "missing_meta_description",
                "severity": "critical",
                "message": "Meta description mancante",
                "field": "seo_description",
            }
        )

    desc_len = _text_len(description_text)
    if desc_len == 0:
        score_description = 0
        issues.append(
            {
                "code": "missing_description",
                "severity": "warning",
                "message": "Descrizione prodotto assente",
                "field": "description",
            }
        )
    else:
        score_description = (
            100 if desc_len >= PRODUCT_DESC_MIN else max(20, int(100 * desc_len / PRODUCT_DESC_MIN))
        )
        if score_description < 100:
            issues.append(
                {
                    "code": "weak_description",
                    "severity": "warning",
                    "message": "Descrizione prodotto debole o troppo corta",
                    "field": "description",
                }
            )

    handle_val = (handle or "").strip()
    score_handle = (
        100
        if len(handle_val) >= HANDLE_MIN and ("-" in handle_val or len(handle_val) >= 5)
        else (60 if len(handle_val) >= HANDLE_MIN else 0)
    )
    if score_handle < 60:
        issues.append(
            {
                "code": "weak_handle",
                "severity": "warning",
                "message": "Handle non ottimale",
                "field": "handle",
            }
        )

    media = media_images or []
    if not media and featured_image_url:
        media = [{"altText": None}]
    if not media:
        score_image_alt = 100
    else:
        with_alt = sum(1 for m in media if (m.get("altText") or m.get("alt") or "").strip())
        score_image_alt = int(100 * with_alt / len(media)) if media else 100
        if score_image_alt < 100:
            issues.append(
                {
                    "code": "missing_image_alt",
                    "severity": "opportunity",
                    "message": "Immagini senza alt text",
                    "field": "media_images",
                }
            )

    component_scores = {
        "score_title": score_title,
        "score_seo_title": score_seo_title,
        "score_meta_description": score_meta,
        "score_description": score_description,
        "score_handle": score_handle,
        "score_image_alt": score_image_alt,
        "score_tags": 100,
    }
    score_breakdown = build_score_breakdown(
        entity_type="product",
        component_scores=component_scores,
        issues=issues,
    )
    score_total = compute_total_from_breakdown(score_breakdown)
    boost = is_best_seller and score_total < 60
    severity = severity_from_score(score_total, boost=boost)

    return {
        "score_total": score_total,
        **component_scores,
        "score_breakdown": score_breakdown,
        "severity": severity,
        "issues": issues,
        "recommendations": recommendations,
    }


def score_collection(
    *,
    title: str | None,
    seo_title: str | None,
    seo_description: str | None,
    description_text: str | None,
    handle: str | None,
    image_url: str | None,
    image_alt: str | None,
    products_count: int | None,
) -> dict[str, Any]:
    load_seo_skill_context()
    issues: list[dict[str, Any]] = []
    recommendations: list[dict[str, Any]] = []

    title_len = _text_len(title)
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

    handle_val = (handle or "").strip()
    score_handle = 100 if len(handle_val) >= HANDLE_MIN else (50 if handle_val else 0)

    desc_len = _text_len(description_text)
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

    seo_title_len = _text_len(seo_title)
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

    meta_len = _text_len(seo_description)
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

    if image_url and not (image_alt or "").strip():
        score_image_alt = 0
        issues.append(
            {
                "code": "missing_image_alt",
                "severity": "opportunity",
                "message": "Immagine collection senza alt",
                "field": "image_alt",
            }
        )
    elif image_url:
        score_image_alt = 100
    else:
        score_image_alt = 100

    if (products_count or 0) >= 3 and desc_len < COLLECTION_DESC_MIN:
        recommendations.append(
            {
                "action": "pillar_collection_copy",
                "priority": "high",
                "reason": f"{products_count} prodotti in collection",
            }
        )

    component_scores = {
        "score_title": score_title,
        "score_seo_title": score_seo_title,
        "score_meta_description": score_meta,
        "score_description": score_description,
        "score_handle": score_handle,
        "score_image_alt": score_image_alt,
    }
    score_breakdown = build_score_breakdown(
        entity_type="collection",
        component_scores=component_scores,
        issues=issues,
    )
    score_total = compute_total_from_breakdown(score_breakdown)

    return {
        "score_total": score_total,
        **component_scores,
        "score_tags": 100,
        "score_breakdown": score_breakdown,
        "severity": severity_from_score(score_total),
        "issues": issues,
        "recommendations": recommendations,
    }
