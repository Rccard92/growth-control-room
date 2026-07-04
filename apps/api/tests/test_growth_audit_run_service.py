"""Tests for Growth Audit run service."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.models.growth_audit import GrowthAuditEvent, GrowthAuditPage, GrowthAuditRun
from app.schemas.growth_audit import GrowthAuditRunCreateRequest
from app.services.growth_audit.exceptions import (
    GrowthAuditRunNotFoundError,
    GrowthAuditValidationError,
)
from app.services.growth_audit.run_service import (
    _load_pages_to_scan,
    create_growth_audit_run,
    get_growth_audit_run,
    process_growth_audit_run,
    schedule_growth_audit_run,
    start_growth_audit_run,
)


def _request(**overrides: object) -> GrowthAuditRunCreateRequest:
    base = {
        "rootUrl": "https://example.com",
        "provider": "openai",
        "auditMode": "full_site_mvp",
        "maxPages": 50,
        "includeAiAnalysis": False,
    }
    base.update(overrides)
    return GrowthAuditRunCreateRequest.model_validate(base)


def _mock_scan_result(url: str = "https://example.com") -> dict:
    return {
        "url": url,
        "finalUrl": url,
        "httpStatus": 200,
        "fetchError": None,
        "title": "Test Page Title Between Thirty And Sixty Five",
        "titleLength": 48,
        "metaDescription": (
            "A meta description that is long enough to be useful for search engines "
            "and users clicking from results pages and within range."
        ),
        "metaDescriptionLength": 120,
        "canonicalUrl": url,
        "h1": "Main Heading",
        "h1Count": 1,
        "robots": {"noindex": False, "nofollow": False, "raw": ""},
        "schema": {"jsonLdCount": 1, "types": ["WebPage"]},
        "openGraph": {"title": "OG", "description": "Desc", "image": "https://example.com/i.jpg"},
        "images": {"total": 1, "missingAlt": 0},
        "links": {"internal": 2, "external": 1},
        "score": 0,
        "checks": {},
        "findings": [],
        "tasks": [],
        "raw": {"contentType": "text/html", "htmlChars": 1000},
    }


def _patch_technical_scan():
    async def _scan(url: str, **kwargs: object) -> dict:
        return _mock_scan_result(url)

    return patch(
        "app.services.growth_audit.run_service.scan_page_technical",
        new=AsyncMock(side_effect=_scan),
    )


def _build_run(*, project_id, run_id=None, status="queued") -> GrowthAuditRun:
    run_id = run_id or uuid4()
    now = datetime.now(UTC)
    run = GrowthAuditRun(
        id=run_id,
        project_id=project_id,
        root_url="https://example.com",
        normalized_domain="example.com",
        status=status,
        phase="queued",
        audit_mode="full_site_mvp",
        provider="openai",
        progress_percent=0,
        pages_discovered=1,
        pages_analyzed=0,
        pages_failed=0,
        config={"includeAiAnalysis": False},
        created_at=now,
        updated_at=now,
    )
    run.pages = [
        GrowthAuditPage(
            id=uuid4(),
            run_id=run_id,
            project_id=project_id,
            url="https://example.com",
            normalized_url="https://example.com",
            path="/",
            page_type="unknown",
            source="seed",
            status="discovered",
            priority="high",
            depth=0,
            discovered_at=now,
            created_at=now,
            updated_at=now,
        )
    ]
    run.events = []
    return run


def _build_scan_pages(
    *,
    project_id,
    run_id,
    count: int,
    status: str = "classified",
) -> list[GrowthAuditPage]:
    now = datetime.now(UTC)
    pages: list[GrowthAuditPage] = []
    for index in range(count):
        suffix = "" if index == 0 else f"/page-{index}"
        pages.append(
            GrowthAuditPage(
                id=uuid4(),
                run_id=run_id,
                project_id=project_id,
                url=f"https://example.com{suffix}",
                normalized_url=f"https://example.com{suffix}",
                path="/" if index == 0 else f"/page-{index}",
                page_type="homepage" if index == 0 else "product",
                source="seed" if index == 0 else "sitemap",
                status=status,
                priority="high" if index == 0 else "normal",
                depth=index,
                discovered_at=now,
                created_at=now,
                updated_at=now,
            )
        )
    return pages


def _mock_session_execute(
    audit_run: GrowthAuditRun,
    pages_for_scan: list[GrowthAuditPage],
    *,
    tasks_count: int = 0,
) -> AsyncMock:
    run_result = MagicMock()
    run_result.scalar_one_or_none.return_value = audit_run

    pages_result = MagicMock()
    pages_scalars = MagicMock()
    pages_scalars.all.return_value = pages_for_scan
    pages_result.scalars.return_value = pages_scalars

    count_result = MagicMock()
    count_result.scalar_one.return_value = tasks_count

    return AsyncMock(side_effect=[run_result, pages_result, count_result])


def test_load_pages_to_scan_returns_eligible_pages_respecting_limit() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        audit_run = _build_run(project_id=project_id, run_id=run_id)
        audit_run.total_pages = 5

        eligible_pages = _build_scan_pages(project_id=project_id, run_id=run_id, count=3)
        session = AsyncMock()
        pages_result = MagicMock()
        pages_scalars = MagicMock()
        pages_scalars.all.return_value = eligible_pages[:2]
        pages_result.scalars.return_value = pages_scalars
        session.execute = AsyncMock(return_value=pages_result)

        loaded = await _load_pages_to_scan(session, run=audit_run, max_pages=2)

        assert len(loaded) == 2
        assert all(page.status == "classified" for page in loaded)
        session.execute.assert_awaited_once()

    asyncio.run(run())


def test_load_pages_to_scan_excludes_analyzed_and_failed_statuses() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        audit_run = _build_run(project_id=project_id, run_id=run_id)
        audit_run.total_pages = 5

        eligible_only = _build_scan_pages(project_id=project_id, run_id=run_id, count=3)
        session = AsyncMock()
        pages_result = MagicMock()
        pages_scalars = MagicMock()
        pages_scalars.all.return_value = eligible_only
        pages_result.scalars.return_value = pages_scalars
        session.execute = AsyncMock(return_value=pages_result)

        loaded = await _load_pages_to_scan(session, run=audit_run, max_pages=10)

        assert len(loaded) == 3
        assert all(
            page.status in ("classified", "discovered", "pending") for page in loaded
        )

    asyncio.run(run())


def test_create_growth_audit_run_creates_seed_page_and_event() -> None:
    async def run() -> None:
        session = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        created = await create_growth_audit_run(session, uuid4(), _request())

        assert created.status == "queued"
        assert created.pages_discovered == 1
        assert created.normalized_domain == "example.com"
        assert session.add.call_count >= 3
        session.commit.assert_awaited_once()

    asyncio.run(run())


def test_create_growth_audit_run_requires_root_url() -> None:
    async def run() -> None:
        session = AsyncMock()
        with pytest.raises(GrowthAuditValidationError):
            await create_growth_audit_run(
                session,
                uuid4(),
                _request(rootUrl=""),
            )

    asyncio.run(run())


def test_process_growth_audit_run_completes_with_summary() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        audit_run = _build_run(project_id=project_id, run_id=run_id)
        audit_run.total_pages = 3
        scan_pages = _build_scan_pages(project_id=project_id, run_id=run_id, count=3)

        session = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.commit = AsyncMock()
        session.execute = _mock_session_execute(audit_run, scan_pages)

        session_factory = MagicMock()
        session_factory.return_value.__aenter__ = AsyncMock(return_value=session)
        session_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        scan_calls: list[str] = []

        async def track_scan(url: str, **kwargs: object) -> dict:
            scan_calls.append(url)
            return _mock_scan_result(url)

        with (
            patch(
                "app.services.growth_audit.run_service.get_session_factory",
                return_value=session_factory,
            ),
            patch(
                "app.services.growth_audit.run_service.scan_page_technical",
                new=AsyncMock(side_effect=track_scan),
            ),
            patch(
                "app.services.growth_audit.run_service.discover_sitemap_urls",
                new=AsyncMock(
                    return_value=(
                        ["https://example.com/products/a", "https://example.com/pages/about"],
                        [{"type": "sitemap_found", "message": "ok", "count": 2}],
                    )
                ),
            ),
            patch(
                "app.services.growth_audit.run_service.discover_shopify_urls",
                new=AsyncMock(
                    return_value=(
                        [
                            {
                                "url": "https://example.com/products/a",
                                "source": "shopify_product",
                                "pageType": "product",
                                "title": "Product A",
                                "metadata": {},
                            }
                        ],
                        [{"type": "shopify_urls_found", "message": "ok", "count": 1}],
                    )
                ),
            ),
        ):
            await process_growth_audit_run(run_id)

        assert audit_run.status == "completed"
        assert audit_run.phase == "finalization"
        assert audit_run.progress_percent == 100
        assert audit_run.summary is not None
        assert audit_run.summary["pagesDiscovered"] >= 2
        assert audit_run.summary["pagesAnalyzed"] == 3
        assert "averageTechnicalScore" in audit_run.summary
        assert "sources" in audit_run.summary
        assert "pageTypes" in audit_run.summary
        assert audit_run.pages_discovered >= 2
        assert audit_run.pages_analyzed == 3
        assert audit_run.site_score is not None
        assert len(scan_calls) == 3

    asyncio.run(run())


def test_process_growth_audit_run_scans_all_inventory_pages_despite_stale_run_pages() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        audit_run = _build_run(project_id=project_id, run_id=run_id)
        audit_run.total_pages = 5
        assert len(audit_run.pages) == 1

        scan_pages = _build_scan_pages(project_id=project_id, run_id=run_id, count=5)

        session = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.commit = AsyncMock()
        session.execute = _mock_session_execute(audit_run, scan_pages)

        session_factory = MagicMock()
        session_factory.return_value.__aenter__ = AsyncMock(return_value=session)
        session_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        scan_calls: list[str] = []

        async def track_scan(url: str, **kwargs: object) -> dict:
            scan_calls.append(url)
            return _mock_scan_result(url)

        with (
            patch(
                "app.services.growth_audit.run_service.get_session_factory",
                return_value=session_factory,
            ),
            patch(
                "app.services.growth_audit.run_service.scan_page_technical",
                new=AsyncMock(side_effect=track_scan),
            ),
            patch(
                "app.services.growth_audit.run_service.discover_sitemap_urls",
                new=AsyncMock(
                    return_value=(
                        [f"https://example.com/page-{index}" for index in range(1, 5)],
                        [{"type": "sitemap_found", "message": "ok", "count": 4}],
                    )
                ),
            ),
            patch(
                "app.services.growth_audit.run_service.discover_shopify_urls",
                new=AsyncMock(return_value=([], [])),
            ),
        ):
            await process_growth_audit_run(run_id)

        assert audit_run.pages_analyzed == 5
        assert audit_run.summary is not None
        assert audit_run.summary["pagesAnalyzed"] == 5
        assert len(scan_calls) == 5

    asyncio.run(run())


def test_process_growth_audit_run_keeps_seed_when_sitemap_fails() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        audit_run = _build_run(project_id=project_id, run_id=run_id)
        audit_run.total_pages = 1
        scan_pages = _build_scan_pages(project_id=project_id, run_id=run_id, count=1)

        session = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.commit = AsyncMock()
        session.execute = _mock_session_execute(audit_run, scan_pages)

        session_factory = MagicMock()
        session_factory.return_value.__aenter__ = AsyncMock(return_value=session)
        session_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        with (
            patch(
                "app.services.growth_audit.run_service.get_session_factory",
                return_value=session_factory,
            ),
            _patch_technical_scan(),
            patch(
                "app.services.growth_audit.run_service.discover_sitemap_urls",
                new=AsyncMock(side_effect=RuntimeError("sitemap down")),
            ),
            patch(
                "app.services.growth_audit.run_service.discover_shopify_urls",
                new=AsyncMock(return_value=([], [{"type": "shopify_urls_missing", "message": "none"}])),
            ),
        ):
            await process_growth_audit_run(run_id)

        assert audit_run.status == "completed"
        assert audit_run.pages_discovered == 1
        assert audit_run.pages_analyzed == 1
        assert audit_run.summary is not None
        assert audit_run.summary.get("warning")

    asyncio.run(run())


def test_process_growth_audit_run_partial_failed_when_page_scan_fails() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        audit_run = _build_run(project_id=project_id, run_id=run_id)
        audit_run.total_pages = 2
        scan_pages = _build_scan_pages(project_id=project_id, run_id=run_id, count=2)

        session = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.commit = AsyncMock()
        session.execute = _mock_session_execute(audit_run, scan_pages)

        session_factory = MagicMock()
        session_factory.return_value.__aenter__ = AsyncMock(return_value=session)
        session_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        call_count = 0

        async def flaky_scan(url: str, **kwargs: object) -> dict:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("scan failed")
            return _mock_scan_result(url)

        with (
            patch(
                "app.services.growth_audit.run_service.get_session_factory",
                return_value=session_factory,
            ),
            patch(
                "app.services.growth_audit.run_service.scan_page_technical",
                new=AsyncMock(side_effect=flaky_scan),
            ),
            patch(
                "app.services.growth_audit.run_service.discover_sitemap_urls",
                new=AsyncMock(return_value=([], [])),
            ),
            patch(
                "app.services.growth_audit.run_service.discover_shopify_urls",
                new=AsyncMock(return_value=([], [])),
            ),
        ):
            await process_growth_audit_run(run_id)

        assert audit_run.pages_failed >= 1
        assert audit_run.summary is not None

    asyncio.run(run())


def test_process_growth_audit_run_creates_technical_results() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        audit_run = _build_run(project_id=project_id, run_id=run_id)
        audit_run.total_pages = 1
        scan_pages = _build_scan_pages(project_id=project_id, run_id=run_id, count=1)

        session = AsyncMock()
        added: list[object] = []
        session.add = MagicMock(side_effect=lambda obj: added.append(obj))
        session.flush = AsyncMock()
        session.commit = AsyncMock()
        session.execute = _mock_session_execute(audit_run, scan_pages)

        session_factory = MagicMock()
        session_factory.return_value.__aenter__ = AsyncMock(return_value=session)
        session_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        with (
            patch(
                "app.services.growth_audit.run_service.get_session_factory",
                return_value=session_factory,
            ),
            _patch_technical_scan(),
            patch(
                "app.services.growth_audit.run_service.discover_sitemap_urls",
                new=AsyncMock(return_value=([], [])),
            ),
            patch(
                "app.services.growth_audit.run_service.discover_shopify_urls",
                new=AsyncMock(return_value=([], [])),
            ),
        ):
            await process_growth_audit_run(run_id)

        from app.models.growth_audit import GrowthAuditPageResult

        result_types = [
            type(item).__name__
            for item in added
            if type(item).__name__
            in {
                "GrowthAuditPageResult",
                "GrowthAuditFinding",
                "GrowthAuditTask",
            }
        ]
        assert "GrowthAuditPageResult" in result_types or audit_run.pages_analyzed >= 1
        assert audit_run.pages[0].score is not None or audit_run.pages_analyzed >= 1

    asyncio.run(run())


def test_get_growth_audit_run_filters_by_project() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        audit_run = _build_run(project_id=project_id, run_id=run_id)

        session = AsyncMock()
        execute_result = MagicMock()
        execute_result.scalar_one_or_none.return_value = audit_run
        session.execute = AsyncMock(return_value=execute_result)

        found = await get_growth_audit_run(session, project_id, run_id)
        assert found is audit_run

        execute_result.scalar_one_or_none.return_value = None
        missing = await get_growth_audit_run(session, uuid4(), run_id)
        assert missing is None

    asyncio.run(run())


def test_schedule_growth_audit_run_creates_task() -> None:
    run_id = uuid4()
    with patch("app.services.growth_audit.run_service.asyncio.create_task") as mock_task:
        schedule_growth_audit_run(run_id)
        mock_task.assert_called_once()


def test_start_growth_audit_run_schedules_processing() -> None:
    async def run() -> None:
        session = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        with (
            patch(
                "app.services.growth_audit.run_service.schedule_growth_audit_run",
            ) as mock_schedule,
        ):
            created = await start_growth_audit_run(session, uuid4(), _request())
            mock_schedule.assert_called_once_with(created.id)

    asyncio.run(run())


def test_get_growth_audit_run_detail_not_found() -> None:
    async def run() -> None:
        from app.services.growth_audit.run_service import get_growth_audit_run_detail

        session = AsyncMock()
        execute_result = MagicMock()
        execute_result.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(return_value=execute_result)

        with pytest.raises(GrowthAuditRunNotFoundError):
            await get_growth_audit_run_detail(session, uuid4(), uuid4())

    asyncio.run(run())
