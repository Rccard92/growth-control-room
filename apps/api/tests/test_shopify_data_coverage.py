"""A zero that means "no data" must not look like a zero that means "no sales"."""

from datetime import UTC, datetime, timedelta

from app.services.shopify.data_coverage import (
    coverage_alert,
    evaluate_order_data_coverage,
)

NOW = datetime(2026, 9, 19, 12, 0, tzinfo=UTC)
PERIOD_START = NOW - timedelta(days=30)


def _coverage(last_sync_at):
    return evaluate_order_data_coverage(
        last_sync_at=last_sync_at,
        period_start=PERIOD_START,
        period_end=NOW,
        now=NOW,
    )


def test_recent_sync_covers_the_period() -> None:
    coverage = _coverage(NOW - timedelta(hours=2))
    assert coverage.status == "covered"
    assert coverage.order_metrics_reliable
    assert coverage.is_stale is False
    assert coverage_alert(coverage) is None


def test_sync_older_than_the_period_makes_order_metrics_unusable() -> None:
    """The real Solmielato case: synced 13 July, dashboard showing the last 30 days."""
    coverage = _coverage(datetime(2026, 7, 13, 14, 50, tzinfo=UTC))

    assert coverage.status == "uncovered"
    assert coverage.order_metrics_reliable is False
    assert "non sono disponibili" in coverage.message
    alert = coverage_alert(coverage)
    assert alert["severity"] == "critical"


def test_a_sync_a_few_hours_behind_still_counts_as_covered() -> None:
    """Being slightly behind is normal operation, not missing data."""
    coverage = _coverage(NOW - timedelta(hours=20))
    assert coverage.status == "covered"
    assert coverage.order_metrics_reliable


def test_sync_inside_the_period_is_partial() -> None:
    coverage = _coverage(NOW - timedelta(days=10))
    assert coverage.status == "partial"
    assert coverage.order_metrics_reliable is False
    assert "incompleti" in coverage.message
    assert coverage_alert(coverage)["severity"] == "critical"


def test_never_synced_is_reported_as_missing_data() -> None:
    coverage = _coverage(None)
    assert coverage.status == "never_synced"
    assert coverage.order_metrics_reliable is False
    assert coverage_alert(coverage)["severity"] == "critical"


def test_a_covered_but_day_old_sync_is_only_a_warning() -> None:
    coverage = evaluate_order_data_coverage(
        last_sync_at=NOW - timedelta(hours=30),
        period_start=PERIOD_START,
        period_end=NOW - timedelta(hours=31),
        now=NOW,
    )
    assert coverage.order_metrics_reliable
    assert coverage.is_stale
    assert coverage_alert(coverage)["severity"] == "warning"


def test_naive_timestamps_are_treated_as_utc() -> None:
    coverage = evaluate_order_data_coverage(
        last_sync_at=datetime(2026, 7, 13, 14, 50),
        period_start=PERIOD_START,
        period_end=NOW,
        now=NOW,
    )
    assert coverage.status == "uncovered"


def test_serialization_carries_the_reliability_flag() -> None:
    payload = _coverage(datetime(2026, 7, 13, tzinfo=UTC)).to_dict()
    assert payload["orderMetricsReliable"] is False
    assert payload["status"] == "uncovered"
    assert payload["lastSyncAt"].startswith("2026-07-13")
