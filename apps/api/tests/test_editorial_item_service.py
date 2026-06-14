"""Editorial item service tests."""

from datetime import date

from app.services.content.editorial_item_service import _month_range


def test_month_range_june_2026() -> None:
    start, end = _month_range("2026-06")
    assert start == date(2026, 6, 1)
    assert end == date(2026, 6, 30)


def test_month_range_february_leap_year() -> None:
    start, end = _month_range("2024-02")
    assert start == date(2024, 2, 1)
    assert end == date(2024, 2, 29)
