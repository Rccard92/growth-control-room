"""Editorial Guidelines service tests."""

import asyncio
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.schemas.brand_editorial_guidelines import BrandEditorialGuidelinesUpdate
from app.services.brand_intelligence.editorial_guidelines_service import (
    DEFAULT_BRAND_PEOPLE,
    editorial_guidelines_completion,
    editorial_guidelines_missing_fields,
    get_editorial_guidelines,
    upsert_editorial_guidelines,
)


def test_editorial_guidelines_completion_empty() -> None:
    assert editorial_guidelines_completion(None) == "empty"


def test_editorial_guidelines_completion_partial() -> None:
    row = type(
        "Row",
        (),
        {
            "content_philosophy": "Scriviamo per aiutare",
            "reading_style": None,
            "default_article_length": None,
            "brand_people": DEFAULT_BRAND_PEOPLE,
            "community_cta_rules": None,
            "article_dos": None,
            "article_length_policy": None,
            "storytelling_rules": None,
            "author_voice_rules": None,
            "article_donts": None,
        },
    )()
    assert editorial_guidelines_completion(row) == "partial"


def test_editorial_guidelines_completion_complete() -> None:
    row = type(
        "Row",
        (),
        {
            "content_philosophy": "Filosofia",
            "reading_style": "Diretto",
            "default_article_length": "medio",
            "brand_people": DEFAULT_BRAND_PEOPLE,
            "community_cta_rules": ["Commenta sotto"],
            "article_dos": ["Essere concreti"],
            "article_length_policy": None,
            "storytelling_rules": None,
            "author_voice_rules": None,
            "article_donts": None,
        },
    )()
    assert editorial_guidelines_completion(row) == "complete"


def test_editorial_guidelines_missing_fields_none() -> None:
    missing = editorial_guidelines_missing_fields(None)
    assert "content_philosophy" in missing
    assert "default_article_length" in missing


def test_get_editorial_guidelines_prefills_brand_people() -> None:
    project_id = uuid4()
    mock_session = AsyncMock()
    created = type(
        "Row",
        (),
        {
            "project_id": project_id,
            "brand_people": DEFAULT_BRAND_PEOPLE,
            "default_article_length": "medio",
            "content_philosophy": None,
            "reading_style": None,
            "article_length_policy": None,
            "storytelling_rules": None,
            "author_voice_rules": None,
            "community_cta_rules": None,
            "article_dos": None,
            "article_donts": None,
        },
    )()

    async def run() -> None:
        with patch(
            "app.services.brand_intelligence.editorial_guidelines_service._get_or_create_editorial_guidelines",
            new_callable=AsyncMock,
            return_value=created,
        ):
            result = await get_editorial_guidelines(mock_session, project_id)
        assert result.brand_people == DEFAULT_BRAND_PEOPLE

    asyncio.run(run())


def test_upsert_editorial_guidelines_updates_fields() -> None:
    project_id = uuid4()
    mock_session = AsyncMock()
    row = type(
        "Row",
        (),
        {
            "project_id": project_id,
            "brand_people": DEFAULT_BRAND_PEOPLE,
            "default_article_length": "medio",
            "content_philosophy": None,
            "reading_style": None,
            "article_length_policy": None,
            "storytelling_rules": None,
            "author_voice_rules": None,
            "community_cta_rules": None,
            "article_dos": None,
            "article_donts": None,
        },
    )()
    payload = BrandEditorialGuidelinesUpdate(
        contentPhilosophy="Valore reale per il cliente",
        readingStyle="Morbido e concreto",
        defaultArticleLength="breve",
    )

    async def run() -> None:
        with patch(
            "app.services.brand_intelligence.editorial_guidelines_service._get_or_create_editorial_guidelines",
            new_callable=AsyncMock,
            return_value=row,
        ):
            result = await upsert_editorial_guidelines(mock_session, project_id, payload)
        assert result.content_philosophy == "Valore reale per il cliente"
        assert result.reading_style == "Morbido e concreto"
        assert result.default_article_length == "breve"

    asyncio.run(run())
