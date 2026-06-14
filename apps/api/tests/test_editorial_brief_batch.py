"""Editorial brief batch generation service tests."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.schemas.content_seo_editorial import EditorialBriefBatchStartRequest
from app.services.content.editorial_brief_batch_service import (
    _progress_percent,
    create_brief_batch_job,
    find_batch_candidates,
    has_editorial_brief_payload,
    job_to_response,
    process_brief_batch_job,
)
from app.services.content.editorial_brief_service import BriefGenerationError


def test_has_editorial_brief_payload_empty() -> None:
    assert has_editorial_brief_payload(None) is False
    assert has_editorial_brief_payload({}) is False


def test_has_editorial_brief_payload_with_title() -> None:
    assert has_editorial_brief_payload({"proposedTitle": "Guida olio"}) is True


def test_has_editorial_brief_payload_with_structure() -> None:
    assert has_editorial_brief_payload({"h2H3Structure": ["H2: Intro"]}) is True


def test_find_batch_candidates_filters_without_brief() -> None:
    project_id = uuid4()
    with_brief = SimpleNamespace(
        id=uuid4(),
        brief_payload={"proposedTitle": "Già fatto"},
    )
    without_brief = SimpleNamespace(id=uuid4(), brief_payload=None)

    async def run() -> None:
        session = AsyncMock()
        with patch(
            "app.services.content.editorial_brief_batch_service.list_editorial_items",
            new_callable=AsyncMock,
            return_value=[with_brief, without_brief],
        ):
            rows = await find_batch_candidates(session, project_id, "2026-06", "idea")
        assert rows == [without_brief]

    asyncio.run(run())


def test_create_brief_batch_job_no_openai() -> None:
    project_id = uuid4()
    request = EditorialBriefBatchStartRequest(month="2026-06", only_status="idea")

    async def run() -> None:
        session = AsyncMock()
        with patch(
            "app.services.content.editorial_brief_batch_service.is_openai_configured",
            return_value=False,
        ):
            with pytest.raises(HTTPException) as exc:
                await create_brief_batch_job(session, project_id, request)
            assert exc.value.status_code == 503
            assert "AI non configurata" in str(exc.value.detail)

    asyncio.run(run())


def test_create_brief_batch_job_no_candidates() -> None:
    project_id = uuid4()
    request = EditorialBriefBatchStartRequest(month="2026-06", only_status="idea")

    async def run() -> None:
        session = AsyncMock()
        with patch(
            "app.services.content.editorial_brief_batch_service.is_openai_configured",
            return_value=True,
        ):
            with patch(
                "app.services.content.editorial_brief_batch_service.find_batch_candidates",
                new_callable=AsyncMock,
                return_value=[],
            ):
                with pytest.raises(HTTPException) as exc:
                    await create_brief_batch_job(session, project_id, request)
                assert exc.value.status_code == 422
                assert "Nessun contenuto" in str(exc.value.detail)

    asyncio.run(run())


def test_progress_percent_and_job_response() -> None:
    job = SimpleNamespace(
        id=uuid4(),
        status="running",
        total_items=4,
        completed_items=2,
        failed_items=1,
        current_item_title="Titolo corrente",
        errors=[],
    )
    assert _progress_percent(job) == 75
    response = job_to_response(job)
    assert response.progress_percent == 75
    assert response.current_item_title == "Titolo corrente"


def test_process_brief_batch_job_partial_failed() -> None:
    job_id = uuid4()
    project_id = uuid4()
    item_ok = uuid4()
    item_fail = uuid4()

    job = SimpleNamespace(
        id=job_id,
        project_id=project_id,
        status="pending",
        month="2026-06",
        only_status="idea",
        total_items=2,
        completed_items=0,
        failed_items=0,
        current_item_id=None,
        current_item_title=None,
        errors=[],
        completed_at=None,
    )

    row_ok = SimpleNamespace(id=item_ok, project_id=project_id, title="OK")
    row_fail = SimpleNamespace(id=item_fail, project_id=project_id, title="Fail")

    session = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()

    job_query = MagicMock()
    job_query.scalar_one_or_none.return_value = job

    item_queries = {
        item_ok: MagicMock(scalar_one_or_none=MagicMock(return_value=row_ok)),
        item_fail: MagicMock(scalar_one_or_none=MagicMock(return_value=row_fail)),
    }

    call_count = 0

    async def execute(stmt):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return job_query
        if call_count == 2:
            return item_queries[item_ok]
        if call_count == 3:
            return item_queries[item_fail]
        return item_queries[item_fail]

    session.execute = execute

    async def generate_side_effect(sess, pid, iid):
        del sess, pid
        if iid == item_fail:
            raise BriefGenerationError("Brief non generato per questo contenuto.")

    async def run() -> None:
        factory = MagicMock()
        factory.return_value.__aenter__ = AsyncMock(return_value=session)
        factory.return_value.__aexit__ = AsyncMock(return_value=None)

        candidates = [
            SimpleNamespace(id=item_ok, title="OK"),
            SimpleNamespace(id=item_fail, title="Fail"),
        ]

        with patch(
            "app.services.content.editorial_brief_batch_service.get_session_factory",
            return_value=factory,
        ):
            with patch(
                "app.services.content.editorial_brief_batch_service.find_batch_candidates",
                new_callable=AsyncMock,
                return_value=candidates,
            ):
                with patch(
                    "app.services.content.editorial_brief_batch_service.generate_editorial_brief_core",
                    new_callable=AsyncMock,
                    side_effect=generate_side_effect,
                ):
                    await process_brief_batch_job(job_id)

        assert job.status == "partial_failed"
        assert job.completed_items == 1
        assert job.failed_items == 1
        assert len(job.errors) == 1

    asyncio.run(run())
