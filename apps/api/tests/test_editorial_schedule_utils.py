"""Tests for editorial PED schedule helpers."""

from datetime import date

from app.schemas.content_seo_editorial import EditorialPublishingPayload
from app.services.content.editorial_schedule_utils import (
    apply_ped_schedule_defaults,
    build_scheduled_publish_at,
    classify_planned_date,
    resolve_editorial_timezone,
    scheduled_publish_at_to_iso,
    sync_ped_schedule_on_planned_date_change,
)
from app.services.content.editorial_publishing_utils import (
    build_article_create_input,
    build_publishing_payload_from_article,
    validate_publishing_payload,
)


def test_build_scheduled_publish_at_europe_rome_summer() -> None:
    scheduled = build_scheduled_publish_at(
        date(2026, 7, 5),
        publish_time="09:00",
        timezone_name="Europe/Rome",
    )
    assert scheduled_publish_at_to_iso(scheduled) == "2026-07-05T09:00:00+02:00"


def test_apply_ped_schedule_defaults_future_sets_schedule_mode() -> None:
    publishing = EditorialPublishingPayload(title="Titolo", body_html="<p>Ok</p>")
    updated = apply_ped_schedule_defaults(
        publishing,
        planned_date=date(2026, 7, 5),
        timezone_name="Europe/Rome",
    )
    assert updated.mode == "schedule"
    assert updated.scheduled_publish_source == "ped_planned_date"
    assert updated.scheduled_publish_at == "2026-07-05T09:00:00+02:00"


def test_apply_ped_schedule_defaults_past_sets_draft_mode() -> None:
    publishing = EditorialPublishingPayload(
        title="Titolo",
        body_html="<p>Ok</p>",
        mode="schedule",
        scheduled_publish_at="2026-01-01T09:00:00+01:00",
    )
    updated = apply_ped_schedule_defaults(
        publishing,
        planned_date=date(2020, 1, 1),
        timezone_name="Europe/Rome",
    )
    assert updated.mode == "draft"
    assert updated.scheduled_publish_at is None


def test_apply_ped_schedule_defaults_respects_manual_source() -> None:
    publishing = EditorialPublishingPayload(
        title="Titolo",
        body_html="<p>Ok</p>",
        mode="draft",
        scheduled_publish_source="manual",
        scheduled_publish_at="2026-08-01T10:00:00+02:00",
    )
    updated = apply_ped_schedule_defaults(
        publishing,
        planned_date=date(2026, 7, 5),
        timezone_name="Europe/Rome",
    )
    assert updated.scheduled_publish_at == "2026-08-01T10:00:00+02:00"
    assert updated.mode == "draft"


def test_sync_ped_schedule_on_planned_date_change_updates_payload() -> None:
    payload = {
        "title": "Titolo",
        "bodyHtml": "<p>Ok</p>",
        "mode": "schedule",
        "scheduledPublishSource": "ped_planned_date",
        "scheduledPublishTimezone": "Europe/Rome",
        "scheduledPublishTime": "09:00",
        "sourcePlannedDate": "2026-07-05",
        "scheduledPublishAt": "2026-07-05T09:00:00+02:00",
    }
    updated = sync_ped_schedule_on_planned_date_change(
        payload,
        planned_date=date(2026, 7, 10),
        timezone_name="Europe/Rome",
    )
    assert updated is not None
    assert updated["scheduledPublishAt"] == "2026-07-10T09:00:00+02:00"


def test_build_article_create_input_schedule_has_publish_date_and_metafields() -> None:
    from app.schemas.content_seo_editorial import EditorialArticlePayload

    article = EditorialArticlePayload(
        title="Guida",
        handle="guida",
        excerpt="",
        body_html="<p>Ok</p>",
        seo_title="SEO",
        meta_description="Meta",
        tags=[],
        author_name="Redazione",
    )
    publishing = build_publishing_payload_from_article(
        article,
        planned_date=date(2026, 7, 5),
        timezone_name="Europe/Rome",
    )
    article_input = build_article_create_input(
        publishing,
        blog_gid="gid://shopify/Blog/1",
        mode="schedule",
    )
    assert article_input["isPublished"] is True
    assert article_input["publishDate"] == "2026-07-05T09:00:00+02:00"
    assert "seo" not in article_input
    assert "metafields" in article_input


def test_validate_schedule_in_past_returns_error() -> None:
    publishing = EditorialPublishingPayload(
        title="Titolo",
        body_html="<p>Ok</p>",
        author="Redazione",
        handle="handle",
        seo_title="SEO",
        meta_description="Meta",
        blog_gid="gid://shopify/Blog/1",
        mode="schedule",
        scheduled_publish_at="2020-01-01T09:00:00+01:00",
        scheduled_publish_timezone="Europe/Rome",
    )
    errors = validate_publishing_payload(publishing, for_publish=True)
    assert any("futura" in err.lower() for err in errors)


def test_resolve_editorial_timezone_fallback() -> None:
    assert resolve_editorial_timezone(None) == "Europe/Rome"


def test_classify_planned_date_future() -> None:
    from app.services.content.editorial_schedule_utils import resolve_zoneinfo

    classification = classify_planned_date(
        date(2099, 1, 1),
        resolve_zoneinfo("Europe/Rome"),
    )
    assert classification == "future"
