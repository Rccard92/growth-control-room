"""Tests for collection analyze when DB has no synced collections."""

import asyncio
import os
from unittest.mock import MagicMock
from uuid import uuid4

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

from app.services.content.collection_seo_analyzer import analyze_collections_for_store


class _FakeScalars:
    def all(self):
        return []


class _FakeResult:
    def scalars(self):
        return _FakeScalars()


class _FakeSession:
    async def execute(self, _stmt):
        return _FakeResult()

    async def commit(self):
        pass


def test_analyze_collections_empty_returns_message() -> None:
    store = MagicMock()
    store.id = uuid4()
    store.project_id = uuid4()

    result = asyncio.run(analyze_collections_for_store(store, _FakeSession()))

    assert result.collections_analyzed == 0
    assert result.message is not None
    assert "Nessuna collection sincronizzata" in result.message
