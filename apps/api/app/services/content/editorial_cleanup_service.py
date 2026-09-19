"""Bulk cleanup of editorial items that never made it to Shopify.

Deleting content is irreversible, so this is a two-step operation: `preview`
lists exactly what would go, `cleanup` removes it only when the caller confirms.

An item is a candidate when it is NOT published, has NO article on Shopify, and
either carries a publish error or is an abandoned draft. An item that already has
a `shopify_article_id` is never a candidate: deleting the local row would leave an
orphaned article on the blog with nothing pointing at it.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_seo_editorial import ContentSeoEditorialItem

logger = logging.getLogger(__name__)

#: Never touched: the item is live, scheduled on Shopify, or being worked on.
PROTECTED_STATUSES = frozenset({"published", "scheduled"})

#: States that mean "tried to publish and failed".
ERROR_STATUSES = frozenset({"publish_error"})

#: States that mean "written but never taken further".
DRAFT_STATUSES = frozenset({"draft_pending", "draft_review", "ready_to_publish"})

DEFAULT_ABANDONED_AFTER_DAYS = 30


@dataclass(frozen=True)
class CleanupCandidate:
    item: ContentSeoEditorialItem
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.item.id),
            "title": self.item.title,
            "status": self.item.status,
            "publishStatus": self.item.publish_status,
            "plannedDate": self.item.planned_date.isoformat() if self.item.planned_date else None,
            "lastPublishError": self.item.last_publish_error,
            "updatedAt": self.item.updated_at.isoformat() if self.item.updated_at else None,
            "reason": self.reason,
        }


def _classify(
    item: ContentSeoEditorialItem,
    *,
    cutoff: datetime,
    include_drafts: bool,
) -> str | None:
    """Return why the item is a candidate, or None to keep it."""
    if item.status in PROTECTED_STATUSES:
        return None
    if item.publish_status == "published":
        return None
    # A Shopify article exists: removing the local row would orphan it.
    if (item.shopify_article_id or item.shopify_article_gid) is not None:
        return None

    if item.status in ERROR_STATUSES or item.last_publish_error:
        return "Pubblicazione fallita e mai completata"

    if not include_drafts:
        return None

    if item.status in DRAFT_STATUSES and item.article_payload:
        updated = item.updated_at
        if updated is not None and updated.tzinfo is None:
            updated = updated.replace(tzinfo=UTC)
        if updated is not None and updated < cutoff:
            return "Bozza scritta e mai pubblicata"

    return None


async def find_cleanup_candidates(
    session: AsyncSession,
    project_id: UUID,
    *,
    include_drafts: bool = True,
    abandoned_after_days: int = DEFAULT_ABANDONED_AFTER_DAYS,
) -> list[CleanupCandidate]:
    cutoff = datetime.now(UTC) - timedelta(days=abandoned_after_days)
    rows = (
        (
            await session.execute(
                select(ContentSeoEditorialItem)
                .where(
                    ContentSeoEditorialItem.project_id == project_id,
                    ContentSeoEditorialItem.status.notin_(sorted(PROTECTED_STATUSES)),
                    or_(
                        ContentSeoEditorialItem.shopify_article_id.is_(None),
                        ContentSeoEditorialItem.shopify_article_gid.is_(None),
                    ),
                )
                .order_by(ContentSeoEditorialItem.planned_date.asc())
            )
        )
        .scalars()
        .all()
    )

    candidates: list[CleanupCandidate] = []
    for row in rows:
        reason = _classify(row, cutoff=cutoff, include_drafts=include_drafts)
        if reason:
            candidates.append(CleanupCandidate(item=row, reason=reason))
    return candidates


async def preview_editorial_cleanup(
    session: AsyncSession,
    project_id: UUID,
    *,
    include_drafts: bool = True,
    abandoned_after_days: int = DEFAULT_ABANDONED_AFTER_DAYS,
) -> dict[str, Any]:
    candidates = await find_cleanup_candidates(
        session,
        project_id,
        include_drafts=include_drafts,
        abandoned_after_days=abandoned_after_days,
    )
    return {
        "count": len(candidates),
        "items": [c.to_dict() for c in candidates],
        "message": (
            f"{len(candidates)} item verrebbero eliminati. Nessuna modifica effettuata."
            if candidates
            else "Nessun item da eliminare."
        ),
    }


async def run_editorial_cleanup(
    session: AsyncSession,
    project_id: UUID,
    *,
    confirm: bool,
    item_ids: list[UUID] | None = None,
    include_drafts: bool = True,
    abandoned_after_days: int = DEFAULT_ABANDONED_AFTER_DAYS,
) -> dict[str, Any]:
    if not confirm:
        raise ValueError("Conferma richiesta: imposta confirm=true per eliminare.")

    candidates = await find_cleanup_candidates(
        session,
        project_id,
        include_drafts=include_drafts,
        abandoned_after_days=abandoned_after_days,
    )
    if item_ids is not None:
        # An explicit list can only narrow the candidates, never widen them.
        wanted = set(item_ids)
        candidates = [c for c in candidates if c.item.id in wanted]

    deleted = [c.to_dict() for c in candidates]
    for candidate in candidates:
        await session.delete(candidate.item)
    await session.commit()

    logger.info("Editorial cleanup project=%s eliminati=%s", project_id, len(deleted))
    return {
        "count": len(deleted),
        "items": deleted,
        "message": f"{len(deleted)} item editoriali eliminati.",
    }
