"""UTC naive datetime helpers for DB query filters."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone


def utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def to_utc_naive(value: datetime | date | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return datetime.combine(value, time.min)
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


def day_start_utc_naive(day: date) -> datetime:
    return datetime.combine(day, time.min)


def day_end_exclusive_utc_naive(day: date) -> datetime:
    return datetime.combine(day + timedelta(days=1), time.min)


def month_start_utc_naive(day: date) -> datetime:
    return datetime(day.year, day.month, 1)


def date_range_bounds_utc_naive(
    start_date: date | None,
    end_date: date | None,
) -> tuple[datetime | None, datetime | None]:
    start_inclusive = day_start_utc_naive(start_date) if start_date else None
    end_exclusive = day_end_exclusive_utc_naive(end_date) if end_date else None
    return start_inclusive, end_exclusive
