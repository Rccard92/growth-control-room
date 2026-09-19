"""Tell "no sales" apart from "no data".

Order metrics are computed from what the local sync holds. If the selected period
is not covered by the last sync, every order KPI comes out as a legitimate-looking
0,00 EUR. That is the difference between "you sold nothing" and "we do not know",
and the dashboard has to say which one it is.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

# read_orders without read_all_orders only exposes the last 60 days, so anything
# older than that can never be synced and is not a staleness problem to fix.
SHOPIFY_ORDER_HISTORY_DAYS = 60
STALE_SYNC_AFTER = timedelta(hours=24)
# A sync is never instantaneous, so the newest hours of a period are always
# slightly behind. Only a gap beyond this counts as missing data.
COVERAGE_GRACE = timedelta(hours=24)


@dataclass(frozen=True)
class OrderDataCoverage:
    """How much of the selected period the synced orders actually cover."""

    status: str  # covered | partial | uncovered | never_synced
    last_sync_at: datetime | None
    covered_until: datetime | None
    period_start: datetime
    period_end: datetime
    is_stale: bool
    message: str | None

    @property
    def order_metrics_reliable(self) -> bool:
        return self.status == "covered"

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "orderMetricsReliable": self.order_metrics_reliable,
            "isStale": self.is_stale,
            "lastSyncAt": self.last_sync_at.isoformat() if self.last_sync_at else None,
            "coveredUntil": self.covered_until.isoformat() if self.covered_until else None,
            "message": self.message,
        }


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def _days_ago(value: datetime, now: datetime) -> int:
    return max(0, (now - value).days)


def evaluate_order_data_coverage(
    *,
    last_sync_at: datetime | None,
    period_start: datetime,
    period_end: datetime,
    now: datetime | None = None,
) -> OrderDataCoverage:
    now = now or datetime.now(UTC)
    last_sync = _aware(last_sync_at)
    period_start = _aware(period_start)  # type: ignore[assignment]
    period_end = _aware(period_end)  # type: ignore[assignment]

    if last_sync is None:
        return OrderDataCoverage(
            status="never_synced",
            last_sync_at=None,
            covered_until=None,
            period_start=period_start,
            period_end=period_end,
            is_stale=True,
            message=(
                "Nessuna sincronizzazione Shopify eseguita: i dati di vendita non sono "
                "disponibili. Esegui 'Sincronizza dati'."
            ),
        )

    is_stale = now - last_sync > STALE_SYNC_AFTER
    # Orders are synced up to the moment of the last sync, nothing after it.
    covered_until = min(last_sync, period_end)
    effective_end = min(period_end, now)

    if effective_end - last_sync <= COVERAGE_GRACE:
        return OrderDataCoverage(
            status="covered",
            last_sync_at=last_sync,
            covered_until=covered_until,
            period_start=period_start,
            period_end=period_end,
            is_stale=is_stale,
            message=None,
        )

    if last_sync <= period_start:
        return OrderDataCoverage(
            status="uncovered",
            last_sync_at=last_sync,
            covered_until=None,
            period_start=period_start,
            period_end=period_end,
            is_stale=is_stale,
            message=(
                f"L'ultimo sync Shopify risale a {_days_ago(last_sync, now)} giorni fa, "
                "prima dell'inizio del periodo selezionato: i dati di vendita del periodo "
                "non sono disponibili. I valori a zero non indicano assenza di vendite. "
                "Esegui 'Sincronizza dati'."
            ),
        )

    missing_days = max(1, (effective_end - last_sync).days)
    return OrderDataCoverage(
        status="partial",
        last_sync_at=last_sync,
        covered_until=covered_until,
        period_start=period_start,
        period_end=period_end,
        is_stale=is_stale,
        message=(
            f"Ultimo sync Shopify {_days_ago(last_sync, now)} giorni fa: mancano gli ultimi "
            f"{missing_days} giorni del periodo. I dati di vendita sono incompleti."
        ),
    )


def coverage_alert(coverage: OrderDataCoverage) -> dict[str, Any] | None:
    """The dashboard alert for a period the sync does not cover."""
    if coverage.status == "covered" and not coverage.is_stale:
        return None

    if coverage.status == "never_synced":
        return {
            "id": "sync-never",
            "severity": "critical",
            "title": "Nessun dato di vendita",
            "description": coverage.message,
            "entity_type": "sync",
            "entity_id": None,
            "action_label": "Sincronizza",
        }

    if coverage.status == "uncovered":
        return {
            "id": "sync-uncovered",
            "severity": "critical",
            "title": "Dati di vendita non disponibili per il periodo",
            "description": coverage.message,
            "entity_type": "sync",
            "entity_id": None,
            "action_label": "Sincronizza",
        }

    if coverage.status == "partial":
        return {
            "id": "sync-partial",
            "severity": "critical",
            "title": "Dati di vendita incompleti",
            "description": coverage.message,
            "entity_type": "sync",
            "entity_id": None,
            "action_label": "Sincronizza",
        }

    return {
        "id": "sync-stale",
        "severity": "warning",
        "title": "Dati non aggiornati",
        "description": "Ultimo sync oltre 24 ore fa. I dati potrebbero non essere aggiornati.",
        "entity_type": "sync",
        "entity_id": None,
        "action_label": "Sincronizza",
    }
