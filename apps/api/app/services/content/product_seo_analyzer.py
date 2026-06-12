from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.seo_optimizer import SeoEntityAnalysis
from app.models.shopify import ShopifyProduct, ShopifyStore
from app.services.content.seo_scoring_constants import (
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
from app.services.shopify.analytics import compute_best_sellers, product_lookup


@dataclass
class ProductAnalyzeResult:
    products_analyzed: int = 0
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


def _severity_from_score(score: int, boost: bool = False) -> str:
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


def _analyze_product(
    product: ShopifyProduct,
    *,
    is_best_seller: bool,
) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    recommendations: list[dict[str, Any]] = []

    title_len = _text_len(product.title)
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

    seo_title_len = _text_len(product.seo_title)
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

    meta_len = _text_len(product.seo_description)
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

    desc_text = product.description_text
    if desc_text is None and product.raw_payload:
        desc_text = (product.raw_payload or {}).get("descriptionHtml") or ""
        desc_text = desc_text if isinstance(desc_text, str) else None
    desc_len = _text_len(desc_text)
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
        score_description = 100 if desc_len >= PRODUCT_DESC_MIN else max(20, int(100 * desc_len / PRODUCT_DESC_MIN))

    handle = (product.handle or "").strip()
    score_handle = 100 if len(handle) >= HANDLE_MIN and "-" in handle or len(handle) >= 5 else (
        60 if len(handle) >= HANDLE_MIN else 0
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

    media = product.media_images or []
    if not media and product.featured_image_url:
        media = [{"altText": None}]
    if not media:
        score_image_alt = 100
    else:
        with_alt = sum(1 for m in media if (m.get("altText") or "").strip())
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

    tags = product.tags or []
    score_tags = 100 if 1 <= len(tags) <= 10 else (40 if len(tags) == 0 else 70)
    if len(tags) == 0:
        issues.append(
            {
                "code": "missing_tags",
                "severity": "info",
                "message": "Nessun tag prodotto",
                "field": "tags",
            }
        )

    if not (product.product_type or "").strip():
        issues.append(
            {
                "code": "missing_product_type",
                "severity": "info",
                "message": "Product type non impostato",
                "field": "product_type",
            }
        )

    weights = PRODUCT_WEIGHTS
    score_total = int(
        (
            score_title * weights["title"]
            + score_seo_title * weights["seo_title"]
            + score_meta * weights["meta_description"]
            + score_description * weights["description"]
            + score_handle * weights["handle"]
            + score_image_alt * weights["image_alt"]
            + score_tags * weights["tags"]
        )
        / sum(weights.values())
    )

    boost = is_best_seller and score_total < 60
    severity = _severity_from_score(score_total, boost=boost)

    return {
        "score_total": score_total,
        "score_title": score_title,
        "score_seo_title": score_seo_title,
        "score_meta_description": score_meta,
        "score_description": score_description,
        "score_image_alt": score_image_alt,
        "score_handle": score_handle,
        "score_tags": score_tags,
        "severity": severity,
        "issues": issues,
        "recommendations": recommendations,
    }


async def analyze_products_for_store(
    store: ShopifyStore,
    session: AsyncSession,
) -> ProductAnalyzeResult:
    products = (
        await session.execute(
            select(ShopifyProduct).where(ShopifyProduct.shopify_store_id == store.id)
        )
    ).scalars().all()

    products_by_gid = product_lookup(list(products))
    best_sellers = await compute_best_sellers(
        session,
        store.id,
        products_by_gid,
        limit=20,
    )
    best_titles = {item.get("product_title") for item in best_sellers}

    result = ProductAnalyzeResult()
    now = datetime.now(UTC)

    for product in products:
        if (product.status or "").upper() != "ACTIVE":
            continue

        analysis = _analyze_product(
            product,
            is_best_seller=product.title in best_titles,
        )

        existing = (
            await session.execute(
                select(SeoEntityAnalysis).where(
                    SeoEntityAnalysis.project_id == store.project_id,
                    SeoEntityAnalysis.shopify_store_id == store.id,
                    SeoEntityAnalysis.entity_type == "product",
                    SeoEntityAnalysis.entity_id == product.id,
                )
            )
        ).scalar_one_or_none()

        fields = {
            "entity_gid": product.shopify_gid,
            "entity_title": product.title,
            "last_analyzed_at": now,
            **analysis,
        }

        if existing is None:
            session.add(
                SeoEntityAnalysis(
                    project_id=store.project_id,
                    shopify_store_id=store.id,
                    entity_type="product",
                    entity_id=product.id,
                    **fields,
                )
            )
        else:
            for key, val in fields.items():
                setattr(existing, key, val)

        result.products_analyzed += 1
        sev = analysis["severity"]
        if sev == "critical":
            result.critical += 1
        elif sev == "warning":
            result.warnings += 1
        elif sev == "opportunity":
            result.opportunities += 1

    await session.commit()
    return result
