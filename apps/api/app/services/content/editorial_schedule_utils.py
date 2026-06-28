"""PED-based Shopify schedule helpers for editorial publishing."""

from __future__ import annotations

from datetime import UTC, date, datetime, time
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.models.shopify import ShopifyStore
from app.schemas.content_seo_editorial import EditorialPublishingPayload

DEFAULT_EDITORIAL_PUBLISH_TIME = time(9, 0)
DEFAULT_EDITORIAL_TIMEZONE = "Europe/Rome"

PlannedDateClass = Literal["future", "today", "past"]
ScheduledPublishSource = Literal["ped_planned_date", "manual"]

PED_PAST_DATE_WARNING = (
    "La data PED è passata. Crea bozza o scegli una nuova data."
)


def resolve_editorial_timezone(store: ShopifyStore | None) -> str:
    if store is None:
        return DEFAULT_EDITORIAL_TIMEZONE
    tz_name = str(getattr(store, "timezone", None) or "").strip()
    if not tz_name:
        return DEFAULT_EDITORIAL_TIMEZONE
    try:
        resolve_zoneinfo(tz_name)
        return tz_name
    except ZoneInfoNotFoundError:
        return DEFAULT_EDITORIAL_TIMEZONE


def resolve_zoneinfo(timezone_name: str | None) -> ZoneInfo:
    name = (timezone_name or DEFAULT_EDITORIAL_TIMEZONE).strip() or DEFAULT_EDITORIAL_TIMEZONE
    for candidate in (name, DEFAULT_EDITORIAL_TIMEZONE, "UTC"):
        try:
            return ZoneInfo(candidate)
        except ZoneInfoNotFoundError:
            continue
    return ZoneInfo("UTC")


def classify_planned_date(planned_date: date, tz: ZoneInfo) -> PlannedDateClass:
    today = datetime.now(tz).date()
    if planned_date > today:
        return "future"
    if planned_date == today:
        return "today"
    return "past"


def parse_publish_time(value: str | time | None) -> time:
    if isinstance(value, time):
        return value
    if not value or not str(value).strip():
        return DEFAULT_EDITORIAL_PUBLISH_TIME
    raw = str(value).strip()
    parts = raw.split(":")
    if len(parts) < 2:
        return DEFAULT_EDITORIAL_PUBLISH_TIME
    try:
        hour = int(parts[0])
        minute = int(parts[1])
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return time(hour, minute)
    except ValueError:
        pass
    return DEFAULT_EDITORIAL_PUBLISH_TIME


def format_publish_time(value: time | None) -> str:
    publish_time = value or DEFAULT_EDITORIAL_PUBLISH_TIME
    return publish_time.strftime("%H:%M")


def build_scheduled_publish_at(
    planned_date: date,
    *,
    publish_time: str | time | None = None,
    timezone_name: str | None = None,
) -> datetime:
    tz = resolve_zoneinfo(timezone_name)
    publish_at = datetime.combine(
        planned_date,
        parse_publish_time(publish_time),
        tzinfo=tz,
    )
    return publish_at


def scheduled_publish_at_to_iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.isoformat()


def parse_scheduled_publish_at(value: str | datetime | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=UTC)
    raw = str(value).strip()
    if not raw:
        return None
    normalized = raw.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed


def resolve_scheduled_publish_at_from_payload(
    publishing: EditorialPublishingPayload,
) -> datetime | None:
    if publishing.scheduled_publish_at:
        return parse_scheduled_publish_at(publishing.scheduled_publish_at)
    if publishing.source_planned_date:
        try:
            planned = date.fromisoformat(publishing.source_planned_date)
        except ValueError:
            return None
        return build_scheduled_publish_at(
            planned,
            publish_time=publishing.scheduled_publish_time,
            timezone_name=publishing.scheduled_publish_timezone,
        )
    return None


def is_scheduled_publish_in_future(
    scheduled_at: datetime | None,
    *,
    timezone_name: str | None = None,
) -> bool:
    if scheduled_at is None:
        return False
    tz = resolve_zoneinfo(timezone_name)
    now = datetime.now(tz)
    checked = scheduled_at if scheduled_at.tzinfo is not None else scheduled_at.replace(tzinfo=UTC)
    return checked.astimezone(tz) > now


def apply_ped_schedule_defaults(
    publishing: EditorialPublishingPayload,
    *,
    planned_date: date,
    timezone_name: str | None = None,
    publish_time: str | time | None = None,
    force: bool = False,
) -> EditorialPublishingPayload:
    tz_name = timezone_name or publishing.scheduled_publish_timezone or DEFAULT_EDITORIAL_TIMEZONE
    publish_time_value = parse_publish_time(
        publish_time or publishing.scheduled_publish_time,
    )
    if not force and publishing.scheduled_publish_source == "manual":
        return publishing

    classification = classify_planned_date(planned_date, resolve_zoneinfo(tz_name))
    if classification == "future":
        scheduled_at = build_scheduled_publish_at(
            planned_date,
            publish_time=publish_time_value,
            timezone_name=tz_name,
        )
        iso_value = scheduled_publish_at_to_iso(scheduled_at)
        return publishing.model_copy(
            update={
                "mode": "schedule",
                "scheduled_publish_at": iso_value,
                "scheduled_publish_timezone": tz_name,
                "scheduled_publish_source": "ped_planned_date",
                "source_planned_date": planned_date.isoformat(),
                "scheduled_publish_time": format_publish_time(publish_time_value),
                "publish_date": iso_value,
                "is_published": False,
            }
        )

    return publishing.model_copy(
        update={
            "mode": "draft",
            "scheduled_publish_at": None,
            "scheduled_publish_timezone": tz_name,
            "scheduled_publish_source": "ped_planned_date",
            "source_planned_date": planned_date.isoformat(),
            "scheduled_publish_time": format_publish_time(publish_time_value),
            "publish_date": None,
            "is_published": False,
        }
    )


def sync_ped_schedule_on_planned_date_change(
    publishing_payload: dict | EditorialPublishingPayload | None,
    *,
    planned_date: date,
    timezone_name: str | None = None,
) -> dict | None:
    if not publishing_payload:
        return None
    from app.services.content.editorial_publishing_utils import normalize_publishing_payload

    publishing = (
        publishing_payload
        if isinstance(publishing_payload, EditorialPublishingPayload)
        else normalize_publishing_payload(dict(publishing_payload))
    )
    if publishing.scheduled_publish_source != "ped_planned_date":
        return publishing.model_dump(by_alias=True, mode="json")
    updated = apply_ped_schedule_defaults(
        publishing,
        planned_date=planned_date,
        timezone_name=timezone_name,
        force=True,
    )
    return updated.model_dump(by_alias=True, mode="json")
