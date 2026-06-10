from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import HTTPException
from sqlalchemy import func

from app.models.shopify import ShopifyOrder, ShopifyStore

VALID_RANGES = frozenset(
    {
        "today",
        "yesterday",
        "last_7_days",
        "last_30_days",
        "month_to_date",
        "previous_month",
        "custom",
    }
)

DEFAULT_RANGE = "last_30_days"

RANGE_LABELS: dict[str, str] = {
    "today": "Oggi",
    "yesterday": "Ieri",
    "last_7_days": "Ultimi 7 giorni",
    "last_30_days": "Ultimi 30 giorni",
    "month_to_date": "Mese corrente",
    "previous_month": "Mese precedente",
    "custom": "Personalizzato",
}


@dataclass(frozen=True)
class ResolvedPeriod:
    range: str
    start_date: date
    end_date: date
    timezone: str
    label: str
    start_at: datetime
    end_at_exclusive: datetime

    def to_dict(self) -> dict[str, str | date]:
        return {
            "range": self.range,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "timezone": self.timezone,
            "label": self.label,
        }


def order_effective_at_column():
    return func.coalesce(
        ShopifyOrder.processed_at,
        ShopifyOrder.created_at_shopify,
        ShopifyOrder.created_at,
    )


def order_effective_at(order: ShopifyOrder) -> datetime | None:
    return order.processed_at or order.created_at_shopify or order.created_at


def order_in_period(order: ShopifyOrder, period: ResolvedPeriod) -> bool:
    dt = order_effective_at(order)
    if dt is None:
        return False
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return period.start_at <= dt < period.end_at_exclusive


def _store_timezone(store: ShopifyStore) -> tuple[ZoneInfo, str]:
    tz_name = (store.timezone or "UTC").strip() or "UTC"
    try:
        tz = ZoneInfo(tz_name)
        return tz, tz_name
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC"), "UTC"


def _local_now(tz: ZoneInfo) -> datetime:
    return datetime.now(tz)


def _date_bounds_to_utc(
    start_date: date,
    end_date: date,
    tz: ZoneInfo,
) -> tuple[datetime, datetime]:
    start_local = datetime.combine(start_date, datetime.min.time(), tzinfo=tz)
    end_exclusive_local = datetime.combine(
        end_date + timedelta(days=1),
        datetime.min.time(),
        tzinfo=tz,
    )
    return start_local.astimezone(UTC), end_exclusive_local.astimezone(UTC)


def _format_custom_label(start_date: date, end_date: date) -> str:
    return (
        f"Personalizzato: {start_date.strftime('%d/%m/%Y')} – "
        f"{end_date.strftime('%d/%m/%Y')}"
    )


def resolve_shopify_period(
    store: ShopifyStore,
    range_key: str | None,
    start_date: date | None,
    end_date: date | None,
) -> ResolvedPeriod:
    key = (range_key or DEFAULT_RANGE).strip().lower()
    if key not in VALID_RANGES:
        raise HTTPException(status_code=422, detail=f"range non valido: {range_key}")

    tz, tz_name = _store_timezone(store)
    today = _local_now(tz).date()

    if key == "custom":
        if start_date is None or end_date is None:
            raise HTTPException(
                status_code=422,
                detail="start_date e end_date sono obbligatori per range=custom",
            )
        if start_date > end_date:
            raise HTTPException(
                status_code=422,
                detail="start_date deve essere <= end_date",
            )
        period_start = start_date
        period_end = end_date
        label = _format_custom_label(period_start, period_end)
    elif key == "today":
        period_start = period_end = today
        label = RANGE_LABELS[key]
    elif key == "yesterday":
        period_start = period_end = today - timedelta(days=1)
        label = RANGE_LABELS[key]
    elif key == "last_7_days":
        period_end = today
        period_start = today - timedelta(days=6)
        label = RANGE_LABELS[key]
    elif key == "last_30_days":
        period_end = today
        period_start = today - timedelta(days=29)
        label = RANGE_LABELS[key]
    elif key == "month_to_date":
        period_start = today.replace(day=1)
        period_end = today
        label = RANGE_LABELS[key]
    elif key == "previous_month":
        first_this_month = today.replace(day=1)
        period_end = first_this_month - timedelta(days=1)
        period_start = period_end.replace(day=1)
        label = RANGE_LABELS[key]
    else:
        raise HTTPException(status_code=422, detail="range non supportato")

    start_at, end_at_exclusive = _date_bounds_to_utc(period_start, period_end, tz)
    return ResolvedPeriod(
        range=key,
        start_date=period_start,
        end_date=period_end,
        timezone=tz_name,
        label=label,
        start_at=start_at,
        end_at_exclusive=end_at_exclusive,
    )


def period_length_days(start_date: date, end_date: date) -> int:
    return (end_date - start_date).days + 1


def _previous_period_label(prev_start: date, prev_end: date, current: ResolvedPeriod) -> str:
    if prev_start == prev_end:
        return f"Periodo precedente: {prev_start.strftime('%d/%m/%Y')}"
    if current.range in RANGE_LABELS and current.range not in {"custom", "month_to_date"}:
        base = RANGE_LABELS[current.range]
        return f"Periodo precedente: {base}"
    return f"Periodo precedente: {_format_custom_label(prev_start, prev_end)}"


def compute_previous_period(current: ResolvedPeriod, tz: ZoneInfo) -> ResolvedPeriod:
    length = period_length_days(current.start_date, current.end_date)

    if current.range in {"today", "yesterday"}:
        prev_end = current.start_date - timedelta(days=1)
        prev_start = prev_end
    elif current.range in {"last_7_days", "last_30_days", "custom"}:
        prev_end = current.start_date - timedelta(days=1)
        prev_start = prev_end - timedelta(days=length - 1)
    elif current.range == "month_to_date":
        first_of_current_month = current.start_date
        last_day_prev_month = first_of_current_month - timedelta(days=1)
        first_of_prev_month = last_day_prev_month.replace(day=1)
        prev_start = first_of_prev_month
        prev_end = prev_start + timedelta(days=length - 1)
        if prev_end > last_day_prev_month:
            prev_end = last_day_prev_month
    elif current.range == "previous_month":
        prev_end = current.start_date - timedelta(days=1)
        prev_start = prev_end.replace(day=1)
    else:
        prev_end = current.start_date - timedelta(days=1)
        prev_start = prev_end - timedelta(days=length - 1)

    start_at, end_at_exclusive = _date_bounds_to_utc(prev_start, prev_end, tz)
    return ResolvedPeriod(
        range=current.range,
        start_date=prev_start,
        end_date=prev_end,
        timezone=current.timezone,
        label=_previous_period_label(prev_start, prev_end, current),
        start_at=start_at,
        end_at_exclusive=end_at_exclusive,
    )


def resolve_period_pair(
    store: ShopifyStore,
    range_key: str | None,
    start_date: date | None,
    end_date: date | None,
) -> tuple[ResolvedPeriod, ResolvedPeriod]:
    current = resolve_shopify_period(store, range_key, start_date, end_date)
    tz, _ = _store_timezone(store)
    previous = compute_previous_period(current, tz)
    return current, previous
