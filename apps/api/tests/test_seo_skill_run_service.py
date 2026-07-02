"""Tests for SEO skill multi-skill run service."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.models.seo_skills import SeoSkillRun, SeoSkillRunResult
from app.schemas.seo_skills import SeoSkillCatalogItem, SeoSkillRunCreateRequest
from app.services.seo_skills.exceptions import (
    SeoSkillProviderError,
    SeoSkillRunValidationError,
)
from app.services.seo_skills.run_service import (
    _validate_provider,
    create_seo_skill_run,
    get_seo_skill_run,
    list_seo_skill_runs,
    process_seo_skill_run,
    schedule_seo_skill_run,
    start_seo_skill_run,
)


def _request(**overrides: object) -> SeoSkillRunCreateRequest:
    base = {
        "targetType": "url",
        "url": "https://example.com/page",
        "selectedSkills": ["seo_geo", "seo_page"],
        "provider": "claude",
    }
    base.update(overrides)
    return SeoSkillRunCreateRequest.model_validate(base)


def _available_skill(key: str) -> SeoSkillCatalogItem:
    return SeoSkillCatalogItem.model_validate(
        {
            "key": key,
            "label": key,
            "description": f"Skill {key}",
            "category": "content",
            "upstreamCommand": f"/seo {key}",
            "status": "available",
            "defaultProvider": "claude",
            "requires": ["url"],
            "optionalIntegrations": [],
            "requiredIntegrations": [],
            "outputSchema": f"{key}_v1",
            "runtime": "prompt_only",
            "riskLevel": "low",
            "enabled": True,
        }
    )


def _build_run(
    *,
    project_id,
    run_id=None,
    selected_skills=None,
    results=None,
    status="pending",
    provider="claude",
) -> SeoSkillRun:
    run_id = run_id or uuid4()
    selected = selected_skills or ["seo_geo", "seo_page"]
    run = SeoSkillRun(
        id=run_id,
        project_id=project_id,
        target_type="url",
        url="https://example.com/page",
        provider=provider,
        selected_skills=selected,
        status=status,
        progress_percent=0,
    )
    if results is None:
        run.results = [
            SeoSkillRunResult(
                id=uuid4(),
                run_id=run_id,
                project_id=project_id,
                skill_key=skill_key,
                status="pending",
            )
            for skill_key in selected
        ]
    else:
        run.results = results
    return run


def test_create_seo_skill_run_creates_pending_run_and_results() -> None:
    async def run() -> None:
        session = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        with patch(
            "app.services.seo_skills.run_service.get_seo_skill_by_key",
            side_effect=lambda key: _available_skill(key),
        ):
            created = await create_seo_skill_run(
                session,
                uuid4(),
                _request(),
            )

        assert created.status == "pending"
        assert created.progress_percent == 0
        assert created.selected_skills == ["seo_geo", "seo_page"]
        assert session.add.call_count == 3
        session.commit.assert_awaited_once()

    asyncio.run(run())


def test_create_seo_skill_run_empty_selected_skills_raises() -> None:
    async def run() -> None:
        session = AsyncMock()
        with pytest.raises(
            SeoSkillRunValidationError,
            match="At least one SEO skill must be selected",
        ):
            await create_seo_skill_run(
                session,
                uuid4(),
                _request(selectedSkills=[]),
            )

    asyncio.run(run())


def test_create_seo_skill_run_url_without_url_raises() -> None:
    async def run() -> None:
        session = AsyncMock()
        with pytest.raises(
            SeoSkillRunValidationError,
            match="url is required for target_type=url",
        ):
            await create_seo_skill_run(
                session,
                uuid4(),
                _request(url=None),
            )

    asyncio.run(run())


def test_create_seo_skill_run_shopify_product_without_target_id_raises() -> None:
    async def run() -> None:
        session = AsyncMock()
        with pytest.raises(
            SeoSkillRunValidationError,
            match="target_id is required for shopify_product",
        ):
            await create_seo_skill_run(
                session,
                uuid4(),
                _request(targetType="shopify_product", url=None, targetId=None),
            )

    asyncio.run(run())


def test_create_seo_skill_run_invalid_provider_raises() -> None:
    with pytest.raises(
        SeoSkillRunValidationError,
        match="Unsupported AI provider: anthropic",
    ):
        _validate_provider("anthropic")


def test_create_seo_skill_run_unknown_skill_raises() -> None:
    async def run() -> None:
        session = AsyncMock()
        with patch(
            "app.services.seo_skills.run_service.get_seo_skill_by_key",
            return_value=None,
        ):
            with pytest.raises(
                SeoSkillRunValidationError,
                match="SEO skill is not runnable: seo_unknown",
            ):
                await create_seo_skill_run(
                    session,
                    uuid4(),
                    _request(selectedSkills=["seo_unknown"]),
                )

    asyncio.run(run())


@pytest.mark.parametrize("status", ["needs_config", "external_required", "planned"])
def test_create_seo_skill_run_non_available_skill_raises(status: str) -> None:
    async def run() -> None:
        session = AsyncMock()
        skill = _available_skill("seo_geo").model_copy(update={"status": status})
        with patch(
            "app.services.seo_skills.run_service.get_seo_skill_by_key",
            return_value=skill,
        ):
            with pytest.raises(
                SeoSkillRunValidationError,
                match="SEO skill is not runnable: seo_geo",
            ):
                await create_seo_skill_run(
                    session,
                    uuid4(),
                    _request(selectedSkills=["seo_geo"]),
                )

    asyncio.run(run())


def test_list_seo_skill_runs_filters_by_project_id() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_a = SimpleNamespace(id=uuid4())
        session = AsyncMock()
        scalars = MagicMock()
        scalars.all.return_value = [run_a]
        session.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(return_value=scalars)))

        rows = await list_seo_skill_runs(session, project_id, limit=20)
        assert rows == [run_a]
        session.execute.assert_awaited_once()

    asyncio.run(run())


def test_get_seo_skill_run_filters_by_project_id() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_id = uuid4()
        expected = SimpleNamespace(id=run_id, project_id=project_id)
        session = AsyncMock()
        session.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=expected))
        )

        row = await get_seo_skill_run(session, project_id, run_id)
        assert row == expected

    asyncio.run(run())


def _process_session_factory(run: SeoSkillRun) -> tuple[AsyncMock, MagicMock]:
    session = AsyncMock()
    session.commit = AsyncMock()

    run_query = MagicMock()
    run_query.scalar_one_or_none.return_value = run

    call_count = 0

    async def execute(_stmt):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return run_query
        return run_query

    session.execute = execute

    factory = MagicMock()
    factory.return_value.__aenter__ = AsyncMock(return_value=session)
    factory.return_value.__aexit__ = AsyncMock(return_value=None)
    return session, factory


def test_process_seo_skill_run_completes_all_skills() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_row = _build_run(project_id=project_id)
        session, factory = _process_session_factory(run_row)

        async def skill_output(**kwargs: object) -> dict:
            return {
                "skillKey": kwargs["skill_key"],
                "score": 80,
                "findings": [{"title": "ok"}],
                "recommendations": [],
                "tasks": [],
                "artifacts": {},
                "warnings": [],
            }

        with (
            patch(
                "app.services.seo_skills.run_service.get_session_factory",
                return_value=factory,
            ),
            patch(
                "app.services.seo_skills.run_service.run_single_seo_skill",
                new=AsyncMock(side_effect=skill_output),
            ),
        ):
            await process_seo_skill_run(run_row.id)

        assert run_row.status == "completed"
        assert run_row.progress_percent == 100
        assert run_row.current_skill is None
        assert all(result.status == "completed" for result in run_row.results)
        session.commit.await_count >= 3

    asyncio.run(run())


def test_process_seo_skill_run_partial_failed() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_row = _build_run(project_id=project_id)
        session, factory = _process_session_factory(run_row)

        async def skill_output(**kwargs: object) -> dict:
            if kwargs["skill_key"] == "seo_page":
                raise SeoSkillProviderError("provider failed")
            return {
                "skillKey": kwargs["skill_key"],
                "score": 70,
                "findings": [],
                "recommendations": [],
                "tasks": [],
                "artifacts": {},
                "warnings": [],
            }

        with (
            patch(
                "app.services.seo_skills.run_service.get_session_factory",
                return_value=factory,
            ),
            patch(
                "app.services.seo_skills.run_service.run_single_seo_skill",
                new=AsyncMock(side_effect=skill_output),
            ),
        ):
            await process_seo_skill_run(run_row.id)

        assert run_row.status == "partial_failed"
        assert run_row.progress_percent == 100
        statuses = {result.skill_key: result.status for result in run_row.results}
        assert statuses["seo_geo"] == "completed"
        assert statuses["seo_page"] == "failed"
        failed_page = next(result for result in run_row.results if result.skill_key == "seo_page")
        assert failed_page.error_message == "provider failed"

    asyncio.run(run())


def test_process_seo_skill_run_partial_failed_humanizes_empty_openai() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_row = _build_run(project_id=project_id, provider="openai")
        session, factory = _process_session_factory(run_row)

        async def skill_output(**kwargs: object) -> dict:
            if kwargs["skill_key"] == "seo_page":
                raise SeoSkillProviderError("Risposta OpenAI vuota")
            return {
                "skillKey": kwargs["skill_key"],
                "score": 70,
                "findings": [],
                "recommendations": [],
                "tasks": [],
                "artifacts": {},
                "warnings": [],
            }

        with (
            patch(
                "app.services.seo_skills.run_service.get_session_factory",
                return_value=factory,
            ),
            patch(
                "app.services.seo_skills.run_service.run_single_seo_skill",
                new=AsyncMock(side_effect=skill_output),
            ),
        ):
            await process_seo_skill_run(run_row.id)

        failed_page = next(result for result in run_row.results if result.skill_key == "seo_page")
        assert "risposta vuota" in failed_page.error_message.lower()

    asyncio.run(run())


def test_process_seo_skill_run_all_failed() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_row = _build_run(project_id=project_id)
        session, factory = _process_session_factory(run_row)

        with (
            patch(
                "app.services.seo_skills.run_service.get_session_factory",
                return_value=factory,
            ),
            patch(
                "app.services.seo_skills.run_service.run_single_seo_skill",
                new=AsyncMock(side_effect=SeoSkillProviderError("provider failed")),
            ),
        ):
            await process_seo_skill_run(run_row.id)

        assert run_row.status == "failed"
        assert run_row.progress_percent == 100
        assert run_row.error_message is not None
        assert all(result.status == "failed" for result in run_row.results)

    asyncio.run(run())


def test_process_seo_skill_run_skips_completed_run() -> None:
    async def run() -> None:
        project_id = uuid4()
        run_row = _build_run(project_id=project_id, status="completed")
        session, factory = _process_session_factory(run_row)

        with (
            patch(
                "app.services.seo_skills.run_service.get_session_factory",
                return_value=factory,
            ),
            patch(
                "app.services.seo_skills.run_service.run_single_seo_skill",
                new=AsyncMock(),
            ) as mock_runner,
        ):
            await process_seo_skill_run(run_row.id)

        mock_runner.assert_not_awaited()
        session.commit.assert_not_awaited()

    asyncio.run(run())


def test_start_seo_skill_run_schedules_background_task() -> None:
    async def run() -> None:
        session = AsyncMock()
        project_id = uuid4()
        created_run = _build_run(project_id=project_id)

        with (
            patch(
                "app.services.seo_skills.run_service.create_seo_skill_run",
                new=AsyncMock(return_value=created_run),
            ),
            patch(
                "app.services.seo_skills.run_service.schedule_seo_skill_run",
            ) as mock_schedule,
        ):
            result = await start_seo_skill_run(session, project_id, _request())

        assert result is created_run
        mock_schedule.assert_called_once_with(created_run.id)

    asyncio.run(run())


def test_schedule_seo_skill_run_creates_asyncio_task() -> None:
    run_id = uuid4()

    def _consume_coro(coro):
        coro.close()

    with patch(
        "app.services.seo_skills.run_service.asyncio.create_task",
        side_effect=_consume_coro,
    ) as mock_create_task:
        schedule_seo_skill_run(run_id)
    mock_create_task.assert_called_once()
