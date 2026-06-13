"""Section drafts latestOnly filter logic tests."""

from types import SimpleNamespace

from app.services.brand_intelligence.section_drafts_service import PENDING_DRAFT_STATUSES


def _filter_latest(rows: list[SimpleNamespace]) -> list[SimpleNamespace]:
    """Mirror list_section_drafts latest_only branch for unit testing."""
    latest: dict[str, SimpleNamespace] = {}
    for row in rows:
        if row.status in ("rejected", "applied"):
            continue
        if row.status not in PENDING_DRAFT_STATUSES:
            continue
        if row.section_key not in latest:
            latest[row.section_key] = row
    return list(latest.values())


def test_latest_only_returns_one_per_section() -> None:
    rows = [
        SimpleNamespace(section_key="brand_profile", status="draft", created_at=2),
        SimpleNamespace(section_key="brand_profile", status="rejected", created_at=3),
        SimpleNamespace(section_key="brand_voice", status="needs_review", created_at=1),
    ]
    result = _filter_latest(rows)
    keys = {r.section_key for r in result}
    assert keys == {"brand_profile", "brand_voice"}
    assert len(result) == 2


def test_latest_only_excludes_applied() -> None:
    rows = [
        SimpleNamespace(section_key="brand_profile", status="applied", created_at=5),
        SimpleNamespace(section_key="brand_profile", status="draft", created_at=4),
    ]
    result = _filter_latest(rows)
    assert len(result) == 1
    assert result[0].status == "draft"


def test_latest_only_excludes_rejected() -> None:
    rows = [
        SimpleNamespace(section_key="brand_profile", status="rejected", created_at=5),
        SimpleNamespace(section_key="brand_profile", status="approved", created_at=4),
    ]
    result = _filter_latest(rows)
    assert len(result) == 1
    assert result[0].status == "approved"
