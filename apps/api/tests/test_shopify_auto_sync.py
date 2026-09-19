"""Scheduled Shopify sync: locking, selection and failure isolation."""

import asyncio
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.services.shopify import auto_sync
from app.services.shopify.auto_sync import sync_due_stores


def _store(name: str, last_sync_at: datetime | None):
    return SimpleNamespace(
        shop_domain=name,
        last_sync_at=last_sync_at,
        connection_status="connected",
    )


def _session(*, lock_acquired: bool = True):
    session = AsyncMock()
    session.execute = AsyncMock(return_value=SimpleNamespace(scalar=lambda: lock_acquired))
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


def _factory(session):
    def _make():
        ctx = AsyncMock()
        ctx.__aenter__ = AsyncMock(return_value=session)
        ctx.__aexit__ = AsyncMock(return_value=False)
        return ctx

    return _make


def test_only_stale_stores_are_synced() -> None:
    now = datetime.now(UTC)
    fresh = _store("fresh.myshopify.com", now - timedelta(minutes=5))
    stale = _store("stale.myshopify.com", now - timedelta(days=60))
    never = _store("never.myshopify.com", None)
    session = _session()
    sync = AsyncMock(return_value={"products_synced": 1, "orders_synced": 2})

    with (
        patch.object(auto_sync, "get_session_factory", new=lambda: _factory(session)),
        patch.object(auto_sync, "_stores_due", new=AsyncMock(return_value=[stale, never])),
        patch.object(auto_sync, "get_shopify_client_for_store", new=AsyncMock()),
        patch.object(auto_sync, "sync_shopify_store", new=sync),
    ):
        summary = asyncio.run(sync_due_stores(max_age=timedelta(hours=12)))

    assert summary == {"checked": 2, "synced": 2, "failed": 0, "skipped_locked": 0}
    assert sync.await_count == 2
    assert fresh.shop_domain not in [c.args[0].shop_domain for c in sync.await_args_list]


def test_a_second_replica_skips_the_tick() -> None:
    session = _session(lock_acquired=False)
    sync = AsyncMock()

    with (
        patch.object(auto_sync, "get_session_factory", new=lambda: _factory(session)),
        patch.object(auto_sync, "sync_shopify_store", new=sync),
    ):
        summary = asyncio.run(sync_due_stores())

    assert summary["skipped_locked"] == 1
    sync.assert_not_called()


def test_one_failing_store_does_not_stop_the_others() -> None:
    a, b = _store("a.myshopify.com", None), _store("b.myshopify.com", None)
    session = _session()
    sync = AsyncMock(side_effect=[RuntimeError("Shopify giu'"), {"products_synced": 3}])

    with (
        patch.object(auto_sync, "get_session_factory", new=lambda: _factory(session)),
        patch.object(auto_sync, "_stores_due", new=AsyncMock(return_value=[a, b])),
        patch.object(auto_sync, "get_shopify_client_for_store", new=AsyncMock()),
        patch.object(auto_sync, "sync_shopify_store", new=sync),
    ):
        summary = asyncio.run(sync_due_stores())

    assert summary["synced"] == 1
    assert summary["failed"] == 1
    session.rollback.assert_awaited()


def test_the_lock_is_released_even_when_a_store_fails() -> None:
    session = _session()
    with (
        patch.object(auto_sync, "get_session_factory", new=lambda: _factory(session)),
        patch.object(auto_sync, "_stores_due", new=AsyncMock(side_effect=RuntimeError("db giu'"))),
    ):
        try:
            asyncio.run(sync_due_stores())
        except RuntimeError:
            pass

    statements = [str(call.args[0]) for call in session.execute.await_args_list]
    assert any("pg_advisory_unlock" in s for s in statements)


def test_scheduler_is_disabled_by_configuration() -> None:
    with patch.object(auto_sync.settings, "shopify_auto_sync_enabled", False):
        auto_sync.start_auto_sync()
    assert auto_sync._task is None
