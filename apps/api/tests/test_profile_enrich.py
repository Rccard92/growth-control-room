"""Profile enrich source fetcher tests."""

from app.services.brand_intelligence.source_fetcher import map_fetch_result_to_source_status


def test_map_blocked_403() -> None:
    assert map_fetch_result_to_source_status(403, "failed") == "blocked"


def test_map_blocked_429() -> None:
    assert map_fetch_result_to_source_status(429, "failed") == "blocked"


def test_map_fetched() -> None:
    assert map_fetch_result_to_source_status(200, "fetched") == "fetched"


def test_map_failed_other() -> None:
    assert map_fetch_result_to_source_status(500, "failed") == "failed"
