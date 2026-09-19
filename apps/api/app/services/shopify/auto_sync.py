"""Scheduled Shopify sync.

Until now every sync was a button click: the Solmielato store went 68 days
without one and the dashboard quietly reported 0,00 EUR for the last 30 days.

The loop runs inside the API process but takes a Postgres advisory lock, so with
several replicas exactly one of them syncs. It is deliberately simple: the sync is
idempotent (upsert by Shopify id), so a container restart mid-run costs nothing —
the next tick redoes the work.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.db.session import get_session_factory
from app.models.integration import Integration
from app.models.shopify import ShopifyStore
from app.services.shopify.connect import get_shopify_client_for_store
from app.services.shopify.sync import sync_shopify_store

logger = logging.getLogger(__name__)

# Arbitrary but fixed: identifies this job among Postgres advisory locks.
ADVISORY_LOCK_KEY = 815_243_001

# Keep a strong reference: a bare asyncio task can be garbage collected mid-run.
_task: asyncio.Task | None = None


async def _try_advisory_lock(session: AsyncSession) -> bool:
    result = await session.execute(
        text("SELECT pg_try_advisory_lock(:key)"), {"key": ADVISORY_LOCK_KEY}
    )
    return bool(result.scalar())


async def _release_advisory_lock(session: AsyncSession) -> None:
    await session.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": ADVISORY_LOCK_KEY})


async def _stores_due(session: AsyncSession, max_age: timedelta) -> list[ShopifyStore]:
    rows = (
        (
            await session.execute(
                select(ShopifyStore)
                .where(ShopifyStore.connection_status == "connected")
                .options(
                    selectinload(ShopifyStore.integration).selectinload(Integration.credential)
                )
            )
        )
        .scalars()
        .all()
    )

    now = datetime.now(UTC)
    due: list[ShopifyStore] = []
    for store in rows:
        last = store.last_sync_at
        if last is None:
            due.append(store)
            continue
        if last.tzinfo is None:
            last = last.replace(tzinfo=UTC)
        if now - last >= max_age:
            due.append(store)
    return due


async def sync_due_stores(*, max_age: timedelta | None = None) -> dict[str, int]:
    """Sync every connected store whose data is older than `max_age`."""
    max_age = max_age or timedelta(minutes=settings.shopify_auto_sync_max_age_minutes)
    session_factory = get_session_factory()
    summary = {"checked": 0, "synced": 0, "failed": 0, "skipped_locked": 0}

    async with session_factory() as session:
        if not await _try_advisory_lock(session):
            # Another replica is already running this tick.
            summary["skipped_locked"] = 1
            return summary
        try:
            stores = await _stores_due(session, max_age)
            summary["checked"] = len(stores)
            for store in stores:
                try:
                    client = await get_shopify_client_for_store(store)
                    result = await sync_shopify_store(store, client, session)
                    await session.commit()
                    summary["synced"] += 1
                    logger.info(
                        "Auto-sync Shopify riuscito store=%s prodotti=%s ordini=%s",
                        store.shop_domain,
                        result.get("products_synced"),
                        result.get("orders_synced"),
                    )
                except Exception as exc:
                    await session.rollback()
                    summary["failed"] += 1
                    logger.exception(
                        "Auto-sync Shopify fallito store=%s: %s", store.shop_domain, exc
                    )
        finally:
            await _release_advisory_lock(session)
            await session.commit()

    return summary


async def _run_forever() -> None:
    interval = timedelta(minutes=settings.shopify_auto_sync_interval_minutes)
    logger.info(
        "Auto-sync Shopify attivo: ogni %s minuti, store più vecchi di %s minuti",
        settings.shopify_auto_sync_interval_minutes,
        settings.shopify_auto_sync_max_age_minutes,
    )
    # Let the app finish booting before the first run.
    await asyncio.sleep(settings.shopify_auto_sync_startup_delay_seconds)
    while True:
        try:
            await sync_due_stores()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Auto-sync Shopify: ciclo fallito, riprovo al prossimo giro")
        await asyncio.sleep(interval.total_seconds())


def start_auto_sync() -> None:
    global _task
    if not settings.shopify_auto_sync_enabled:
        logger.info("Auto-sync Shopify disattivato (SHOPIFY_AUTO_SYNC_ENABLED=false)")
        return
    if _task is not None and not _task.done():
        return
    _task = asyncio.create_task(_run_forever(), name="shopify-auto-sync")


async def stop_auto_sync() -> None:
    global _task
    if _task is None:
        return
    _task.cancel()
    try:
        await _task
    except asyncio.CancelledError:
        pass
    except Exception:
        logger.exception("Auto-sync Shopify: errore durante l'arresto")
    _task = None
