"""Tests for async-safe editorial item read serialization."""

import asyncio
import os
from datetime import UTC, date, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

from app.schemas.content_seo_editorial import ContentSeoEditorialItemRead
from app.services.content.editorial_item_service import get_editorial_item_read


def _sample_row() -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid4(),
        project_id=uuid4(),
        title="Guida",
        content_type="educational_article",
        planned_date=date(2026, 6, 15),
        status="ready_to_publish",
        objective=None,
        primary_keyword=None,
        secondary_keywords=None,
        target_audience=None,
        search_intent=None,
        commercial_intensity=None,
        linked_shopify_product_id=None,
        linked_shopify_product_gid=None,
        linked_shopify_product_title=None,
        linked_shopify_product_handle=None,
        linked_collection_id=None,
        linked_collection_title=None,
        notes=None,
        brief_payload=None,
        article_payload={"title": "Guida"},
        publishing_payload={"title": "Guida", "bodyHtml": "<p>Ok</p>"},
        shopify_blog_id="10",
        shopify_article_id=None,
        shopify_article_gid=None,
        shopify_article_admin_url=None,
        shopify_article_public_url=None,
        shopify_status=None,
        publish_status="not_published",
        publish_mode="draft",
        scheduled_publish_at=None,
        published_at=None,
        last_publish_error=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def test_get_editorial_item_read_refreshes_before_validate() -> None:
    project_id = uuid4()
    item_id = uuid4()
    row = _sample_row()

    async def run() -> None:
        mock_session = AsyncMock()
        with patch(
            "app.services.content.editorial_item_service.get_editorial_item",
            new_callable=AsyncMock,
            return_value=row,
        ):
            result = await get_editorial_item_read(mock_session, project_id, item_id)
            mock_session.refresh.assert_awaited_once_with(row)
            assert isinstance(result, ContentSeoEditorialItemRead)
            assert result.publishing_payload is not None
            assert result.updated_at is not None
            assert result.publish_status == "not_published"
            assert result.shopify_blog_id == "10"

    asyncio.run(run())


def test_get_editorial_item_read_avoids_stale_updated_at_without_refresh() -> None:
    """Regression: without refresh, expired updated_at would trigger MissingGreenlet."""
    project_id = uuid4()
    item_id = uuid4()
    row = _sample_row()
    refreshed_at = datetime(2026, 6, 13, 12, 0, tzinfo=UTC)
    row.updated_at = refreshed_at

    async def run() -> None:
        mock_session = AsyncMock()

        async def refresh_side_effect(target: object) -> None:
            if target is row:
                row.updated_at = refreshed_at

        mock_session.refresh = AsyncMock(side_effect=refresh_side_effect)

        with patch(
            "app.services.content.editorial_item_service.get_editorial_item",
            new_callable=AsyncMock,
            return_value=row,
        ):
            result = await get_editorial_item_read(mock_session, project_id, item_id)
            assert result.updated_at == refreshed_at

    asyncio.run(run())
