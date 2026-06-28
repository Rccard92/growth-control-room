"""Tests for editorial image service provider size and pipeline."""

import asyncio
import io
from datetime import UTC, date, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from PIL import Image

from app.schemas.content_seo_editorial import EditorialArticlePayload, normalize_editorial_article_payload
from app.services.ai.ai_client import AiRequestMetadata, GenerateImageResult, OpenAIRequestError
from app.services.content.editorial_image_processing import (
    EDITORIAL_IMAGE_FINAL_SIZE,
    EDITORIAL_IMAGE_PROVIDER_SIZE,
)
from app.services.content.editorial_image_service import (
    IMAGE_SIZE_USER_MESSAGE,
    _generate_editorial_image_bytes,
    _persist_generated_image,
    _user_friendly_image_error,
)


def _sample_row(*, article_payload: dict) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid4(),
        project_id=uuid4(),
        title="Yogurt con frutta, noci e miele",
        brief_payload=None,
        article_payload=article_payload,
        image_payload=None,
        publishing_payload=None,
    )


def _article_payload_dict() -> dict:
    return EditorialArticlePayload(
        title="Yogurt con frutta, noci e miele: una ricetta semplice per ogni giorno",
        handle="yogurt-frutta",
        excerpt="Ricetta semplice",
        body_html="<p>Test</p>",
        article_hash="hash-123",
    ).model_dump(by_alias=True, mode="json")


def test_user_friendly_image_error_invalid_size() -> None:
    exc = OpenAIRequestError("Invalid size '1792x1024'. Supported sizes are 1536x1024.")
    assert _user_friendly_image_error(exc) == IMAGE_SIZE_USER_MESSAGE


def test_generate_editorial_image_bytes_uses_provider_size() -> None:
    metadata = AiRequestMetadata(
        project_id=uuid4(),
        module="content_seo",
        operation="generate_editorial_image",
        operation_key="editorial_image_generation",
        entity_type="editorial_item",
        entity_id=str(uuid4()),
    )
    fake_bytes = b"fake"

    async def run() -> None:
        with patch(
            "app.services.content.editorial_image_service.generate_image",
            new_callable=AsyncMock,
            return_value=GenerateImageResult(image_bytes=fake_bytes, model="gpt-image-1"),
        ) as mock_generate:
            result = await _generate_editorial_image_bytes("prompt", metadata=metadata)
            mock_generate.assert_awaited_once()
            assert mock_generate.await_args.kwargs["size"] == EDITORIAL_IMAGE_PROVIDER_SIZE
            assert mock_generate.await_args.kwargs["size"] != "1792x1024"
            assert result.image_bytes == fake_bytes

    asyncio.run(run())


def test_generate_editorial_image_bytes_fallback_to_auto() -> None:
    metadata = AiRequestMetadata(
        project_id=uuid4(),
        module="content_seo",
        operation="generate_editorial_image",
        operation_key="editorial_image_generation",
        entity_type="editorial_item",
        entity_id=str(uuid4()),
    )
    fake_bytes = b"fake-auto"
    side_effects = [
        OpenAIRequestError("Invalid size '1536x1024'."),
        GenerateImageResult(image_bytes=fake_bytes, model="gpt-image-1"),
    ]

    async def run() -> None:
        with patch(
            "app.services.content.editorial_image_service.generate_image",
            new_callable=AsyncMock,
            side_effect=side_effects,
        ) as mock_generate:
            result = await _generate_editorial_image_bytes("prompt", metadata=metadata)
            assert mock_generate.await_count == 2
            assert mock_generate.await_args_list[0].kwargs["size"] == EDITORIAL_IMAGE_PROVIDER_SIZE
            assert mock_generate.await_args_list[1].kwargs["size"] == "auto"
            assert result.image_bytes == fake_bytes

    asyncio.run(run())


def test_persist_generated_image_metadata(tmp_path, monkeypatch) -> None:
    project_id = uuid4()
    item_id = uuid4()
    row = _sample_row(article_payload=_article_payload_dict())
    article = normalize_editorial_article_payload(row.article_payload)

    img = Image.new("RGB", (1536, 1024), color="blue")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    provider_bytes = buffer.getvalue()

    monkeypatch.setattr(
        "app.services.content.editorial_image_storage.settings.editorial_images_dir",
        str(tmp_path),
    )
    monkeypatch.setattr(
        "app.services.content.editorial_image_storage.settings.editorial_image_storage_provider",
        "local",
    )

    async def run() -> None:
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        payload = await _persist_generated_image(
            mock_session,
            row,
            project_id=project_id,
            item_id=item_id,
            article=article,
            image_prompt="A yogurt bowl",
            image_bytes=provider_bytes,
            image_model="gpt-image-1",
            log_id="log-1",
            estimated_cost=0.04,
            prompt_snapshot=None,
            revision_note=None,
            warnings=[],
        )
        assert payload.image_width == 1600
        assert payload.image_height == 900
        assert payload.image_provider_size == EDITORIAL_IMAGE_PROVIDER_SIZE
        assert payload.image_final_size == EDITORIAL_IMAGE_FINAL_SIZE
        assert payload.image_alt == article.title
        assert payload.image_filename is not None
        assert payload.image_filename.endswith(".jpg")
        assert "yogurt-con-frutta" in payload.image_filename

    asyncio.run(run())
