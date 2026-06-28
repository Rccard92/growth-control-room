"""Editorial Shopify publish service tests."""

import asyncio
import os
from datetime import UTC, date, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

from app.schemas.content_seo_editorial import EditorialPublishShopifyRequest
from app.schemas.content_seo_editorial import (
    ContentSeoEditorialItemRead,
    EditorialPublishingUpdateRequest,
)
from app.services.content.editorial_publishing_utils import build_publishing_payload_from_article
from app.services.content.editorial_publishing_service import update_editorial_publishing
from app.services.content.editorial_shopify_publish_service import publish_editorial_to_shopify


def _article_payload() -> dict:
    return {
        "title": "Guida olio EVO",
        "handle": "guida-olio-evo",
        "excerpt": "Tutto sull'olio.",
        "bodyHtml": "<h2>Intro</h2><p>Testo utile.</p>",
        "seoTitle": "Olio EVO guida",
        "metaDescription": "Meta desc",
        "tags": ["olio"],
        "authorName": "Davide",
    }


def _sample_row(*, publishing_payload: dict | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid4(),
        project_id=uuid4(),
        status="ready_to_publish",
        title="Guida",
        planned_date=date(2026, 6, 15),
        article_payload=_article_payload(),
        publishing_payload=publishing_payload,
        shopify_blog_id=None,
        shopify_article_id=None,
        shopify_article_gid=None,
        shopify_article_admin_url=None,
        shopify_article_public_url=None,
        shopify_status=None,
        publish_status="not_published",
        publish_mode=None,
        scheduled_publish_at=None,
        published_at=None,
        last_publish_error=None,
        brief_payload=None,
        content_type="educational_article",
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
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def test_save_publishing_payload() -> None:
    project_id = uuid4()
    item_id = uuid4()
    row = _sample_row()
    publishing = build_publishing_payload_from_article(row.article_payload)
    publishing = publishing.model_copy(update={"blog_id": str(uuid4())})

    async def run() -> None:
        mock_session = AsyncMock()
        with patch(
            "app.services.content.editorial_publishing_service.get_editorial_item",
            new_callable=AsyncMock,
            return_value=row,
        ):
            updated = await update_editorial_publishing(
                mock_session,
                project_id,
                item_id,
                EditorialPublishingUpdateRequest(
                    publishingPayload=publishing.model_dump(by_alias=True),
                    publishMode="draft",
                ),
            )
            mock_session.refresh.assert_awaited_once_with(row)
            assert updated.publishing_payload is not None
            assert updated.publish_mode == "draft"

    asyncio.run(run())


def test_save_publishing_payload_missing_body_returns_422() -> None:
    project_id = uuid4()
    item_id = uuid4()
    row = _sample_row()

    async def run() -> None:
        mock_session = AsyncMock()
        with patch(
            "app.services.content.editorial_publishing_service.get_editorial_item",
            new_callable=AsyncMock,
            return_value=row,
        ):
            with pytest.raises(HTTPException) as exc:
                await update_editorial_publishing(
                    mock_session,
                    project_id,
                    item_id,
                    EditorialPublishingUpdateRequest(
                        publishingPayload={"title": "Solo titolo", "bodyHtml": ""},
                    ),
                )
            assert exc.value.status_code == 422

    asyncio.run(run())


def test_publish_missing_write_content_returns_403() -> None:
    project_id = uuid4()
    item_id = uuid4()
    row = _sample_row()
    store = SimpleNamespace(id=uuid4(), shop_domain="shop.myshopify.com", connection_status="connected")

    async def run() -> None:
        mock_session = AsyncMock()
        with patch(
            "app.services.content.editorial_shopify_publish_service.get_editorial_item",
            new_callable=AsyncMock,
            return_value=row,
        ):
            with patch(
                "app.services.content.editorial_shopify_publish_service.get_shopify_store_for_project",
                new_callable=AsyncMock,
                return_value=store,
            ):
                with patch(
                    "app.services.content.editorial_shopify_publish_service.can_publish_with_write_content",
                    new_callable=AsyncMock,
                    return_value={
                        "allowed": False,
                        "message": "Serve il permesso Shopify write_content. Riconnetti Shopify con gli scope aggiornati.",
                    },
                ):
                    with pytest.raises(HTTPException) as exc:
                        await publish_editorial_to_shopify(
                            mock_session,
                            project_id,
                            item_id,
                            EditorialPublishShopifyRequest(mode="draft"),
                        )
                    assert exc.value.status_code == 403
                    assert "write_content" in str(exc.value.detail)

    asyncio.run(run())


def test_publish_success_draft_sets_gid() -> None:
    project_id = uuid4()
    item_id = uuid4()
    blog_id = uuid4()
    publishing = build_publishing_payload_from_article(_article_payload())
    publishing = publishing.model_copy(update={"blog_id": str(blog_id)})
    row = _sample_row(publishing_payload=publishing.model_dump(by_alias=True))
    store = SimpleNamespace(id=uuid4(), shop_domain="shop.myshopify.com", connection_status="connected")
    blog_row = SimpleNamespace(
        id=blog_id,
        shopify_gid="gid://shopify/Blog/10",
        handle="news",
    )

    async def run() -> None:
        mock_session = AsyncMock()

        async def fake_execute(stmt):  # noqa: ANN001
            class Result:
                def scalar_one_or_none(self_inner):  # noqa: ANN001
                    return blog_row

            return Result()

        mock_session.execute = fake_execute

        with patch(
            "app.services.content.editorial_shopify_publish_service.get_editorial_item",
            new_callable=AsyncMock,
            return_value=row,
        ):
            with patch(
                "app.services.content.editorial_shopify_publish_service.get_shopify_store_for_project",
                new_callable=AsyncMock,
                return_value=store,
            ):
                with patch(
                    "app.services.content.editorial_shopify_publish_service.can_publish_with_write_content",
                    new_callable=AsyncMock,
                    return_value={"allowed": True},
                ):
                    mock_client = AsyncMock()
                    mock_client.create_article = AsyncMock(
                        return_value={
                            "article": {
                                "id": "gid://shopify/Article/55",
                                "handle": "guida-olio-evo",
                                "title": "Guida olio EVO",
                            },
                            "userErrors": [],
                        }
                    )
                    with patch(
                        "app.services.content.editorial_shopify_publish_service.get_shopify_client_for_store",
                        new_callable=AsyncMock,
                        return_value=mock_client,
                    ):
                        async def fake_read(
                            session: AsyncMock,  # noqa: ARG001
                            pid: UUID,  # noqa: ARG001
                            iid: UUID,  # noqa: ARG001
                        ) -> ContentSeoEditorialItemRead:
                            return ContentSeoEditorialItemRead.model_validate(row)

                        with patch(
                            "app.services.content.editorial_shopify_publish_service.get_editorial_item_read",
                            side_effect=fake_read,
                        ) as mock_read:
                            result = await publish_editorial_to_shopify(
                                mock_session,
                                project_id,
                                item_id,
                                EditorialPublishShopifyRequest(mode="draft"),
                            )
                            mock_read.assert_awaited_once_with(
                                mock_session, project_id, item_id
                            )
                        assert row.publish_status == "draft_created"
                        assert row.shopify_article_gid == "gid://shopify/Article/55"
                        assert row.shopify_article_id == "55"
                        assert result.item.shopify_article_gid == "gid://shopify/Article/55"

    asyncio.run(run())


def test_publish_user_errors_keeps_payload() -> None:
    project_id = uuid4()
    item_id = uuid4()
    blog_id = uuid4()
    publishing = build_publishing_payload_from_article(_article_payload())
    publishing = publishing.model_copy(update={"blog_id": str(blog_id)})
    original_payload = publishing.model_dump(by_alias=True)
    row = _sample_row(publishing_payload=original_payload)
    store = SimpleNamespace(id=uuid4(), shop_domain="shop.myshopify.com", connection_status="connected")
    blog_row = SimpleNamespace(id=blog_id, shopify_gid="gid://shopify/Blog/10", handle="news")

    async def run() -> None:
        mock_session = AsyncMock()

        async def fake_execute(stmt):  # noqa: ANN001
            class Result:
                def scalar_one_or_none(self_inner):  # noqa: ANN001
                    return blog_row

            return Result()

        mock_session.execute = fake_execute

        with patch(
            "app.services.content.editorial_shopify_publish_service.get_editorial_item",
            new_callable=AsyncMock,
            return_value=row,
        ):
            with patch(
                "app.services.content.editorial_shopify_publish_service.get_shopify_store_for_project",
                new_callable=AsyncMock,
                return_value=store,
            ):
                with patch(
                    "app.services.content.editorial_shopify_publish_service.can_publish_with_write_content",
                    new_callable=AsyncMock,
                    return_value={"allowed": True},
                ):
                    mock_client = AsyncMock()
                    mock_client.create_article = AsyncMock(
                        return_value={
                            "article": None,
                            "userErrors": [{"field": ["title"], "message": "Title is invalid"}],
                        }
                    )
                    with patch(
                        "app.services.content.editorial_shopify_publish_service.get_shopify_client_for_store",
                        new_callable=AsyncMock,
                        return_value=mock_client,
                    ):
                        with patch(
                            "app.services.content.editorial_shopify_publish_service.get_editorial_item_read",
                            new_callable=AsyncMock,
                        ) as mock_read:
                            with pytest.raises(HTTPException) as exc:
                                await publish_editorial_to_shopify(
                                    mock_session,
                                    project_id,
                                    item_id,
                                    EditorialPublishShopifyRequest(mode="draft"),
                                )
                            mock_read.assert_not_awaited()
                        assert exc.value.status_code == 422
                        assert row.publish_status == "publish_error"
                        assert row.publishing_payload == original_payload

    asyncio.run(run())
