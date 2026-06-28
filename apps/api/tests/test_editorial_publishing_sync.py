"""Tests for editorial publishing sync and hash utilities."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.schemas.content_seo_editorial import EditorialArticlePayload
from app.services.content.editorial_publishing_service import sync_publishing_from_article
from app.services.content.editorial_publishing_utils import (
    attach_publishing_sync_metadata,
    compute_editorial_article_hash,
    enrich_article_with_hash,
)


def _sample_article() -> EditorialArticlePayload:
    return EditorialArticlePayload(
        title="Guida miele",
        handle="guida-miele",
        excerpt="Intro",
        body_html="<p>Test</p>",
        seo_title="Guida miele SEO",
        meta_description="Meta",
        tags=["miele", "bio"],
        author_name="Davide",
    )


def test_compute_editorial_article_hash_deterministic() -> None:
    article = _sample_article()
    h1 = compute_editorial_article_hash(article)
    h2 = compute_editorial_article_hash(article)
    assert h1 == h2
    assert len(h1) == 64


def test_enrich_article_with_hash_sets_fields() -> None:
    article = enrich_article_with_hash(_sample_article(), is_new_generation=True)
    assert article.article_hash
    assert article.generated_at
    assert article.updated_at


def test_attach_publishing_sync_metadata() -> None:
    from app.schemas.content_seo_editorial import EditorialPublishingPayload

    article = enrich_article_with_hash(_sample_article(), is_new_generation=True)
    publishing = EditorialPublishingPayload(title="Old")
    synced = attach_publishing_sync_metadata(publishing, article)
    assert synced.source_article_hash == article.article_hash
    assert synced.synced_from_article_at


def test_sync_publishing_from_article_preserves_blog() -> None:
    project_id = uuid4()
    item_id = uuid4()
    article = enrich_article_with_hash(_sample_article(), is_new_generation=True)
    row = SimpleNamespace(
        id=item_id,
        project_id=project_id,
        article_payload=article.model_dump(by_alias=True, mode="json"),
        publishing_payload={
            "title": "Old title",
            "handle": "old",
            "bodyHtml": "<p>Old</p>",
            "excerpt": "",
            "seoTitle": "",
            "metaDescription": "",
            "author": "Redazione",
            "blogId": "blog-uuid",
            "blogGid": "gid://shopify/Blog/1",
            "tags": [],
            "mode": "draft",
            "isPublished": False,
            "imageUrl": "https://example.com/img.jpg",
        },
    )
    mock_session = AsyncMock()

    async def run() -> None:
        with (
            patch(
                "app.services.content.editorial_publishing_service.get_editorial_item",
                new=AsyncMock(return_value=row),
            ),
            patch(
                "app.services.content.editorial_publishing_service.get_shopify_store_for_project",
                new=AsyncMock(return_value=SimpleNamespace(shop_name="Shop")),
            ),
            patch(
                "app.services.content.editorial_publishing_service._brand_name",
                new=AsyncMock(return_value="Brand"),
            ),
        ):
            result = await sync_publishing_from_article(mock_session, project_id, item_id)
        assert result.publishing_payload["title"] == "Guida miele"
        assert result.publishing_payload["bodyHtml"] == "<p>Test</p>"
        assert result.publishing_payload["blogId"] == "blog-uuid"
        assert result.publishing_payload["imageUrl"] == "https://example.com/img.jpg"
        assert result.publishing_payload["sourceArticleHash"] == article.article_hash

    asyncio.run(run())
