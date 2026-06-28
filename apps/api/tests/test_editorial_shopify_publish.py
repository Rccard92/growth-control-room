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
    EditorialArticlePayload,
    EditorialPublishingUpdateRequest,
    normalize_editorial_article_payload,
)
from app.services.content.editorial_publishing_utils import (
    attach_publishing_sync_metadata,
    build_publishing_payload_from_article,
    enrich_article_with_hash,
    PUBLISHING_STALE_MESSAGE,
)
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


def _synced_article_and_publishing(*, blog_id: UUID | None = None) -> tuple[dict, dict]:
    article = enrich_article_with_hash(
        normalize_editorial_article_payload(_article_payload()),
        is_new_generation=False,
    )
    publishing = build_publishing_payload_from_article(article)
    if blog_id is not None:
        publishing = publishing.model_copy(update={"blog_id": str(blog_id)})
    publishing = attach_publishing_sync_metadata(publishing, article)
    return (
        article.model_dump(by_alias=True, mode="json"),
        publishing.model_dump(by_alias=True, mode="json"),
    )


def _article_node_with_seo_metafields(
    *,
    seo_title: str = "Olio EVO guida",
    meta_description: str = "Meta desc",
) -> dict:
    return {
        "id": "gid://shopify/Article/55",
        "handle": "guida-olio-evo",
        "title": "Guida olio EVO",
        "metafields": {
            "edges": [
                {
                    "node": {
                        "namespace": "global",
                        "key": "title_tag",
                        "value": seo_title,
                        "type": "single_line_text_field",
                    }
                },
                {
                    "node": {
                        "namespace": "global",
                        "key": "description_tag",
                        "value": meta_description,
                        "type": "multi_line_text_field",
                    }
                },
            ]
        },
    }


def _configure_mock_client_seo(mock_client: AsyncMock) -> None:
    mock_client.sync_article_seo_metafields = AsyncMock(
        return_value={"synced": True, "error": None, "userErrors": []}
    )
    mock_client.get_article_global_metafields = AsyncMock(
        return_value={"title_tag": "Olio EVO guida", "description_tag": "Meta desc"}
    )


def _sample_row(*, publishing_payload: dict | None = None) -> SimpleNamespace:
    article_payload, default_publishing = _synced_article_and_publishing()
    return SimpleNamespace(
        id=uuid4(),
        project_id=uuid4(),
        status="ready_to_publish",
        title="Guida",
        planned_date=date(2026, 6, 15),
        article_payload=article_payload,
        publishing_payload=publishing_payload if publishing_payload is not None else default_publishing,
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
    publishing = build_publishing_payload_from_article(
        normalize_editorial_article_payload(row.article_payload),
    )
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


def test_publish_stale_payload_returns_409() -> None:
    project_id = uuid4()
    item_id = uuid4()
    article_payload, publishing_payload = _synced_article_and_publishing()
    article_payload["title"] = "Titolo rigenerato"
    article_payload["articleHash"] = "different-hash"
    row = _sample_row(publishing_payload=publishing_payload)
    row.article_payload = article_payload

    async def run() -> None:
        mock_session = AsyncMock()
        with patch(
            "app.services.content.editorial_shopify_publish_service.get_editorial_item",
            new_callable=AsyncMock,
            return_value=row,
        ):
            with pytest.raises(HTTPException) as exc:
                await publish_editorial_to_shopify(
                    mock_session,
                    project_id,
                    item_id,
                    EditorialPublishShopifyRequest(mode="draft"),
                )
            assert exc.value.status_code == 409
            detail = exc.value.detail
            assert isinstance(detail, dict)
            assert detail["code"] == "publishing_stale"
            assert detail["message"] == PUBLISHING_STALE_MESSAGE

    asyncio.run(run())


def test_publish_missing_seo_returns_422() -> None:
    project_id = uuid4()
    item_id = uuid4()
    _, publishing_payload = _synced_article_and_publishing()
    publishing_payload = {**publishing_payload, "seoTitle": "", "metaDescription": ""}
    row = _sample_row(publishing_payload=publishing_payload)
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
                    return_value={"allowed": True},
                ):
                    with pytest.raises(HTTPException) as exc:
                        await publish_editorial_to_shopify(
                            mock_session,
                            project_id,
                            item_id,
                            EditorialPublishShopifyRequest(mode="draft"),
                        )
                    assert exc.value.status_code == 422
                    detail = exc.value.detail
                    assert isinstance(detail, dict)
                    assert detail["code"] == "seo_missing"
                    assert "SEO title e meta description" in detail["message"]

    asyncio.run(run())


def test_publish_missing_write_content_returns_403() -> None:
    project_id = uuid4()
    item_id = uuid4()
    blog_id = uuid4()
    _, publishing_payload = _synced_article_and_publishing(blog_id=blog_id)
    row = _sample_row(publishing_payload=publishing_payload)
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
                    mock_client.find_article_by_handle = AsyncMock(return_value=None)
                    mock_client.create_article = AsyncMock(
                        return_value={
                            "article": _article_node_with_seo_metafields(),
                            "userErrors": [],
                        }
                    )
                    _configure_mock_client_seo(mock_client)
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


def test_publish_update_when_gid_exists() -> None:
    project_id = uuid4()
    item_id = uuid4()
    blog_id = uuid4()
    _, publishing_payload = _synced_article_and_publishing(blog_id=blog_id)
    publishing_payload = {**publishing_payload, "author": "Redazione Test"}
    row = _sample_row(publishing_payload=publishing_payload)
    row.shopify_article_gid = "gid://shopify/Article/55"
    row.shopify_article_id = "55"
    row.publish_status = "draft_created"
    store = SimpleNamespace(
        id=uuid4(),
        shop_domain="shop.myshopify.com",
        shop_name="Solmielato",
        connection_status="connected",
    )
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
                    with patch(
                        "app.services.content.editorial_shopify_publish_service._project_brand_name",
                        new_callable=AsyncMock,
                        return_value="Solmielato",
                    ):
                        mock_client = AsyncMock()
                        mock_client.find_article_by_handle = AsyncMock(return_value=None)
                        mock_client.update_article = AsyncMock(
                            return_value={
                                "article": _article_node_with_seo_metafields(),
                                "userErrors": [],
                            }
                        )
                        mock_client.create_article = AsyncMock()
                        _configure_mock_client_seo(mock_client)
                        with patch(
                            "app.services.content.editorial_shopify_publish_service.get_shopify_client_for_store",
                            new_callable=AsyncMock,
                            return_value=mock_client,
                        ):
                            with patch(
                                "app.services.content.editorial_shopify_publish_service.get_editorial_item_read",
                                new_callable=AsyncMock,
                                return_value=ContentSeoEditorialItemRead.model_validate(row),
                            ):
                                await publish_editorial_to_shopify(
                                    mock_session,
                                    project_id,
                                    item_id,
                                    EditorialPublishShopifyRequest(mode="draft"),
                                )
                        mock_client.update_article.assert_awaited_once()
                        mock_client.create_article.assert_not_awaited()
                        assert row.shopify_article_gid == "gid://shopify/Article/55"
                        assert row.publishing_payload.get("shopifySeoSynced") is True

    asyncio.run(run())


def test_publish_user_errors_keeps_payload() -> None:
    project_id = uuid4()
    item_id = uuid4()
    blog_id = uuid4()
    _, original_payload = _synced_article_and_publishing(blog_id=blog_id)
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
                    mock_client.find_article_by_handle = AsyncMock(return_value=None)
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


def test_publish_empty_author_saved_payload_returns_422_before_shopify() -> None:
    project_id = uuid4()
    item_id = uuid4()
    publishing = build_publishing_payload_from_article(
        normalize_editorial_article_payload(_article_payload()),
    )
    publishing = attach_publishing_sync_metadata(
        publishing.model_copy(update={"author": "", "blog_id": str(uuid4())}),
        enrich_article_with_hash(
            normalize_editorial_article_payload(_article_payload()),
            is_new_generation=False,
        ),
    )
    row = _sample_row(publishing_payload=publishing.model_dump(by_alias=True))
    store = SimpleNamespace(
        id=uuid4(),
        shop_domain="shop.myshopify.com",
        shop_name="Solmielato",
        connection_status="connected",
    )

    async def run() -> None:
        mock_session = AsyncMock()
        mock_client = AsyncMock()
        mock_client.find_article_by_handle = AsyncMock(return_value=None)
        mock_client.create_article = AsyncMock()
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
                    with patch(
                        "app.services.content.editorial_shopify_publish_service._project_brand_name",
                        new_callable=AsyncMock,
                        return_value="Solmielato",
                    ):
                        with patch(
                            "app.services.content.editorial_shopify_publish_service.get_shopify_client_for_store",
                            new_callable=AsyncMock,
                            return_value=mock_client,
                        ):
                            with pytest.raises(HTTPException) as exc:
                                await publish_editorial_to_shopify(
                                    mock_session,
                                    project_id,
                                    item_id,
                                    EditorialPublishShopifyRequest(mode="draft"),
                                )
                            assert exc.value.status_code == 422
                            detail = exc.value.detail
                            assert isinstance(detail, dict)
                            assert "autore" in detail["message"].lower()
                            mock_client.create_article.assert_not_awaited()

    asyncio.run(run())


def test_publish_graphql_author_error_returns_422() -> None:
    from app.services.shopify.client import ShopifyAPIError

    project_id = uuid4()
    item_id = uuid4()
    blog_id = uuid4()
    _, publishing_payload = _synced_article_and_publishing(blog_id=blog_id)
    publishing_payload = {**publishing_payload, "author": "Redazione Test"}
    row = _sample_row(publishing_payload=publishing_payload)
    store = SimpleNamespace(
        id=uuid4(),
        shop_domain="shop.myshopify.com",
        shop_name="Solmielato",
        connection_status="connected",
    )
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
                    with patch(
                        "app.services.content.editorial_shopify_publish_service._project_brand_name",
                        new_callable=AsyncMock,
                        return_value="Solmielato",
                    ):
                        mock_client = AsyncMock()
                        mock_client.find_article_by_handle = AsyncMock(return_value=None)
                        mock_client.create_article = AsyncMock(
                            side_effect=ShopifyAPIError(
                                "Errore GraphQL Shopify: invalid value for author "
                                "(Expected value to not be null)"
                            )
                        )
                        with patch(
                            "app.services.content.editorial_shopify_publish_service.get_shopify_client_for_store",
                            new_callable=AsyncMock,
                            return_value=mock_client,
                        ):
                            with pytest.raises(HTTPException) as exc:
                                await publish_editorial_to_shopify(
                                    mock_session,
                                    project_id,
                                    item_id,
                                    EditorialPublishShopifyRequest(mode="draft"),
                                )
                            assert exc.value.status_code == 422
                            detail = exc.value.detail
                            assert isinstance(detail, dict)
                            assert "shopify" in detail["message"].lower()
                            assert row.publish_status == "publish_error"

    asyncio.run(run())


def test_publish_network_error_returns_502() -> None:
    from app.services.shopify.client import ShopifyAPIError

    project_id = uuid4()
    item_id = uuid4()
    blog_id = uuid4()
    _, publishing_payload = _synced_article_and_publishing(blog_id=blog_id)
    publishing_payload = {**publishing_payload, "author": "Redazione Test"}
    row = _sample_row(publishing_payload=publishing_payload)
    store = SimpleNamespace(
        id=uuid4(),
        shop_domain="shop.myshopify.com",
        shop_name="Solmielato",
        connection_status="connected",
    )
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
                    with patch(
                        "app.services.content.editorial_shopify_publish_service._project_brand_name",
                        new_callable=AsyncMock,
                        return_value="Solmielato",
                    ):
                        mock_client = AsyncMock()
                        mock_client.find_article_by_handle = AsyncMock(return_value=None)
                        mock_client.create_article = AsyncMock(
                            side_effect=ShopifyAPIError(
                                "Impossibile contattare Shopify. Verifica il dominio dello shop."
                            )
                        )
                        with patch(
                            "app.services.content.editorial_shopify_publish_service.get_shopify_client_for_store",
                            new_callable=AsyncMock,
                            return_value=mock_client,
                        ):
                            with pytest.raises(HTTPException) as exc:
                                await publish_editorial_to_shopify(
                                    mock_session,
                                    project_id,
                                    item_id,
                                    EditorialPublishShopifyRequest(mode="draft"),
                                )
                            assert exc.value.status_code == 502

    asyncio.run(run())


def test_publish_success_clears_last_publish_error() -> None:
    project_id = uuid4()
    item_id = uuid4()
    blog_id = uuid4()
    _, publishing_payload = _synced_article_and_publishing(blog_id=blog_id)
    row = _sample_row(publishing_payload=publishing_payload)
    row.last_publish_error = "Errore precedente stale"
    row.publish_status = "publish_error"
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
                    mock_client.find_article_by_handle = AsyncMock(return_value=None)
                    mock_client.create_article = AsyncMock(
                        return_value={
                            "article": _article_node_with_seo_metafields(),
                            "userErrors": [],
                        }
                    )
                    _configure_mock_client_seo(mock_client)
                    with patch(
                        "app.services.content.editorial_shopify_publish_service.get_shopify_client_for_store",
                        new_callable=AsyncMock,
                        return_value=mock_client,
                    ):
                        with patch(
                            "app.services.content.editorial_shopify_publish_service.get_editorial_item_read",
                            new_callable=AsyncMock,
                            return_value=ContentSeoEditorialItemRead.model_validate(row),
                        ):
                            await publish_editorial_to_shopify(
                                mock_session,
                                project_id,
                                item_id,
                                EditorialPublishShopifyRequest(mode="draft"),
                            )
                        assert row.last_publish_error is None
                        assert row.publish_status == "draft_created"

    asyncio.run(run())


def test_publish_metafields_sync_fail_marks_publish_error() -> None:
    from app.services.shopify.client import ShopifyAPIError

    project_id = uuid4()
    item_id = uuid4()
    blog_id = uuid4()
    _, publishing_payload = _synced_article_and_publishing(blog_id=blog_id)
    row = _sample_row(publishing_payload=publishing_payload)
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
                    mock_client.find_article_by_handle = AsyncMock(return_value=None)
                    mock_client.create_article = AsyncMock(
                        return_value={
                            "article": {"id": "gid://shopify/Article/55", "handle": "guida-olio-evo"},
                            "userErrors": [],
                        }
                    )
                    mock_client.sync_article_seo_metafields = AsyncMock(
                        return_value={"synced": False, "error": "metafieldsSet rejected", "userErrors": []}
                    )
                    mock_client.get_article_global_metafields = AsyncMock(
                        return_value={"title_tag": "", "description_tag": ""}
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
                        detail = exc.value.detail
                        assert isinstance(detail, dict)
                        assert detail["code"] == "shopify_metafields_error"
                        assert row.publish_status == "publish_error"
                        assert row.shopify_article_gid == "gid://shopify/Article/55"
                        assert "SEO Shopify non sincronizzata" in (row.last_publish_error or "")

    asyncio.run(run())


def test_publish_find_by_handle_seo_graphql_error_returns_structured_422() -> None:
    from app.services.shopify.client import ShopifyAPIError

    project_id = uuid4()
    item_id = uuid4()
    blog_id = uuid4()
    _, publishing_payload = _synced_article_and_publishing(blog_id=blog_id)
    row = _sample_row(publishing_payload=publishing_payload)
    row.last_publish_error = "Errore precedente"
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
                    mock_client.find_article_by_handle = AsyncMock(
                        side_effect=ShopifyAPIError(
                            "Errore GraphQL Shopify: Field `seo` doesn't exist on type `Article`"
                        )
                    )
                    with patch(
                        "app.services.content.editorial_shopify_publish_service.get_shopify_client_for_store",
                        new_callable=AsyncMock,
                        return_value=mock_client,
                    ):
                        with pytest.raises(HTTPException) as exc:
                            await publish_editorial_to_shopify(
                                mock_session,
                                project_id,
                                item_id,
                                EditorialPublishShopifyRequest(mode="draft"),
                            )
                        detail = exc.value.detail
                        assert isinstance(detail, dict)
                        assert detail["code"] == "shopify_article_seo_field_invalid"
                        assert row.last_publish_error != "Errore precedente"
                        mock_client.create_article.assert_not_awaited()

    asyncio.run(run())


def test_publish_schedule_success_sets_scheduled_status() -> None:
    project_id = uuid4()
    item_id = uuid4()
    blog_id = uuid4()
    _, publishing_payload = _synced_article_and_publishing(blog_id=blog_id)
    publishing_payload = {
        **publishing_payload,
        "mode": "schedule",
        "scheduledPublishSource": "ped_planned_date",
        "scheduledPublishTimezone": "Europe/Rome",
        "scheduledPublishTime": "09:00",
        "sourcePlannedDate": "2026-07-05",
        "scheduledPublishAt": "2026-07-05T09:00:00+02:00",
        "isPublished": False,
        "publishDate": "2026-07-05T09:00:00+02:00",
    }
    row = _sample_row(publishing_payload=publishing_payload)
    row.planned_date = date(2026, 7, 5)
    store = SimpleNamespace(
        id=uuid4(),
        shop_domain="shop.myshopify.com",
        shop_name="Solmielato",
        timezone="Europe/Rome",
        connection_status="connected",
    )
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
                    mock_client.find_article_by_handle = AsyncMock(return_value=None)
                    mock_client.create_article = AsyncMock(
                        return_value={
                            "article": _article_node_with_seo_metafields(),
                            "userErrors": [],
                        }
                    )
                    _configure_mock_client_seo(mock_client)
                    with patch(
                        "app.services.content.editorial_shopify_publish_service.get_shopify_client_for_store",
                        new_callable=AsyncMock,
                        return_value=mock_client,
                    ):
                        with patch(
                            "app.services.content.editorial_shopify_publish_service.get_editorial_item_read",
                            new_callable=AsyncMock,
                            return_value=ContentSeoEditorialItemRead.model_validate(row),
                        ):
                            await publish_editorial_to_shopify(
                                mock_session,
                                project_id,
                                item_id,
                                EditorialPublishShopifyRequest(mode="schedule"),
                            )
                        create_input = mock_client.create_article.await_args.args[0]
                        assert create_input["isPublished"] is False
                        assert create_input["publishDate"] == "2026-07-05T09:00:00+02:00"
                        assert "metafields" in create_input
                        assert row.publish_status == "scheduled"
                        assert row.publishing_payload["isPublished"] is False
                        assert row.last_publish_error is None

    asyncio.run(run())
