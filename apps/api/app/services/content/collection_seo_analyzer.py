from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_seo import ShopifyCollection
from app.models.seo_optimizer import SeoEntityAnalysis
from app.models.shopify import ShopifyStore
from app.services.content.seo_scoring_engine import score_collection
from app.services.content.seo_skill_loader import (
    load_seo_skill_context,
    skill_recommendation_metadata,
)


@dataclass
class CollectionAnalyzeResult:
    collections_analyzed: int = 0
    critical: int = 0
    warnings: int = 0
    opportunities: int = 0


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

    load_seo_skill_context()
    skill_meta = skill_recommendation_metadata()

    result = CollectionAnalyzeResult()
    now = datetime.now(UTC)

    for collection in collections:
        analysis = score_collection(
            title=collection.title,
            seo_title=collection.seo_title,
            seo_description=collection.seo_description,
            description_text=collection.description_text,
            handle=collection.handle,
            image_url=collection.image_url,
            image_alt=collection.image_alt,
            products_count=collection.products_count,
        )

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

        recommendations = list(analysis.get("recommendations") or [])
        recommendations.append(skill_meta)

        fields = {
            "entity_gid": collection.shopify_gid,
            "entity_title": collection.title,
            "last_analyzed_at": now,
            **{k: v for k, v in analysis.items() if k != "recommendations"},
            "recommendations": recommendations,
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
