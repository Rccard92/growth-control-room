"""Bulk cleanup must never remove anything that exists on Shopify."""

import asyncio
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.services.content import editorial_cleanup_service as svc
from app.services.content.editorial_cleanup_service import (
    preview_editorial_cleanup,
    run_editorial_cleanup,
)

OLD = datetime.now(UTC) - timedelta(days=90)
RECENT = datetime.now(UTC) - timedelta(days=2)


def _item(
    *,
    status: str,
    publish_status: str = "not_published",
    article_id: str | None = None,
    error: str | None = None,
    payload: dict | None = None,
    updated_at: datetime = OLD,
):
    return SimpleNamespace(
        id=uuid4(),
        title=f"Item {status}",
        status=status,
        publish_status=publish_status,
        planned_date=None,
        shopify_article_id=article_id,
        shopify_article_gid=f"gid://shopify/Article/{article_id}" if article_id else None,
        last_publish_error=error,
        article_payload=payload,
        updated_at=updated_at,
    )


def _session(rows):
    session = AsyncMock()
    session.execute = AsyncMock(
        return_value=SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: rows))
    )
    session.delete = AsyncMock()
    session.commit = AsyncMock()
    return session


def _preview(rows, **kwargs):
    return asyncio.run(preview_editorial_cleanup(_session(rows), uuid4(), **kwargs))


def test_failed_publish_is_a_candidate() -> None:
    result = _preview([_item(status="publish_error", error="Shopify ha rifiutato")])
    assert result["count"] == 1
    assert result["items"][0]["reason"] == "Pubblicazione fallita e mai completata"


def test_published_and_scheduled_items_are_never_touched() -> None:
    rows = [
        _item(status="published", publish_status="published", article_id="1"),
        _item(status="scheduled", article_id="2"),
    ]
    assert _preview(rows)["count"] == 0


def test_an_item_with_a_shopify_article_is_never_deleted() -> None:
    """Deleting the local row would orphan a real article on the blog."""
    rows = [_item(status="publish_error", article_id="99", error="errore parziale")]
    assert _preview(rows)["count"] == 0


def test_abandoned_draft_with_content_is_a_candidate() -> None:
    rows = [_item(status="draft_review", payload={"title": "Bozza"}, updated_at=OLD)]
    result = _preview(rows)
    assert result["count"] == 1
    assert result["items"][0]["reason"] == "Bozza scritta e mai pubblicata"


def test_a_recent_draft_is_left_alone() -> None:
    rows = [_item(status="draft_review", payload={"title": "Bozza"}, updated_at=RECENT)]
    assert _preview(rows)["count"] == 0


def test_an_empty_idea_is_not_deleted() -> None:
    assert _preview([_item(status="idea", payload=None)])["count"] == 0


def test_drafts_can_be_excluded() -> None:
    rows = [
        _item(status="draft_review", payload={"t": 1}, updated_at=OLD),
        _item(status="publish_error", error="ko"),
    ]
    assert _preview(rows, include_drafts=False)["count"] == 1


def test_preview_deletes_nothing() -> None:
    session = _session([_item(status="publish_error", error="ko")])
    asyncio.run(preview_editorial_cleanup(session, uuid4()))
    session.delete.assert_not_called()
    session.commit.assert_not_called()


def test_cleanup_requires_confirmation() -> None:
    session = _session([_item(status="publish_error", error="ko")])
    with pytest.raises(ValueError, match="Conferma richiesta"):
        asyncio.run(run_editorial_cleanup(session, uuid4(), confirm=False))
    session.delete.assert_not_called()


def test_cleanup_deletes_confirmed_candidates() -> None:
    rows = [_item(status="publish_error", error="ko"), _item(status="published", article_id="1")]
    session = _session(rows)
    result = asyncio.run(run_editorial_cleanup(session, uuid4(), confirm=True))
    assert result["count"] == 1
    assert session.delete.await_count == 1
    session.commit.assert_awaited_once()


def test_an_explicit_id_list_can_only_narrow_the_selection() -> None:
    keep = _item(status="publish_error", error="ko")
    other = _item(status="publish_error", error="ko")
    protected = _item(status="published", publish_status="published", article_id="7")
    session = _session([keep, other, protected])

    result = asyncio.run(
        run_editorial_cleanup(session, uuid4(), confirm=True, item_ids=[keep.id, protected.id])
    )

    assert result["count"] == 1
    assert result["items"][0]["id"] == str(keep.id)


def test_classifier_handles_naive_timestamps() -> None:
    row = _item(status="draft_review", payload={"t": 1}, updated_at=OLD.replace(tzinfo=None))
    assert svc._classify(row, cutoff=datetime.now(UTC), include_drafts=True)
