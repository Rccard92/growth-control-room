"""Tests for SEO skill runner."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.schemas.seo_skills import SeoSkillCatalogItem
from app.services.ai.ai_client import AiRequestMetadata
from app.services.ai.exceptions import ClaudeRequestError
from app.services.seo_skills.catalog_loader import get_seo_skill_by_key
from app.services.seo_skills.exceptions import (
    SeoSkillNotAvailableError,
    SeoSkillProviderError,
)
from app.services.seo_skills.skill_runner import run_single_seo_skill


def _available_skill(**overrides: object) -> SeoSkillCatalogItem:
    base = {
        "key": "seo_geo",
        "label": "GEO SEO",
        "description": "AI search optimization",
        "category": "content",
        "upstreamCommand": "/seo geo <url>",
        "status": "available",
        "defaultProvider": "claude",
        "requires": ["url"],
        "optionalIntegrations": [],
        "requiredIntegrations": [],
        "outputSchema": "seo_geo_v1",
        "runtime": "prompt_only",
        "riskLevel": "low",
        "enabled": True,
    }
    base.update(overrides)
    return SeoSkillCatalogItem.model_validate(base)


def _skill_input(**overrides: object) -> dict:
    base = {
        "projectId": str(uuid4()),
        "targetType": "url",
        "targetId": "",
        "url": "https://example.com/page",
        "title": "Example Page",
        "html": "<h1>Example</h1>",
        "text": "Example",
        "metadata": {},
        "shopify": {},
        "brandContext": "",
        "warnings": ["Input incomplete."],
    }
    base.update(overrides)
    return base


def test_run_single_seo_skill_returns_normalized_output() -> None:
    async def run() -> None:
        session = AsyncMock()
        project_id = uuid4()
        skill = _available_skill()

        with (
            patch(
                "app.services.seo_skills.skill_runner.get_seo_skill_by_key",
                return_value=skill,
            ),
            patch(
                "app.services.seo_skills.skill_runner.collect_skill_input",
                new=AsyncMock(return_value=_skill_input()),
            ),
            patch(
                "app.services.seo_skills.skill_runner.build_skill_system_prompt",
                return_value="system prompt",
            ),
            patch(
                "app.services.seo_skills.skill_runner.build_skill_user_prompt",
                return_value="user prompt",
            ),
            patch(
                "app.services.seo_skills.skill_runner.generate_structured_json_with_provider",
                new=AsyncMock(
                    return_value={
                        "summary": "Buona base GEO",
                        "score": 72,
                        "findings": [{"title": "Citability bassa", "severity": "medium"}],
                    }
                ),
            ) as mock_provider,
        ):
            result = await run_single_seo_skill(
                session,
                project_id,
                "seo_geo",
                "url",
                url="https://example.com/page",
                provider="claude",
            )

        assert result["skillKey"] == "seo_geo"
        assert result["provider"] == "claude"
        assert result["operationKey"] == "claude_seo_geo"
        assert result["summary"] == "Buona base GEO"
        assert result["score"] == 72
        assert result["findings"][0]["severity"] == "medium"
        assert "Input incomplete." in result["warnings"]
        assert result["rawOutput"]["summary"] == "Buona base GEO"
        mock_provider.assert_awaited_once()

    asyncio.run(run())


def test_run_single_seo_skill_unknown_skill_raises() -> None:
    async def run() -> None:
        session = AsyncMock()
        with patch(
            "app.services.seo_skills.skill_runner.get_seo_skill_by_key",
            return_value=None,
        ):
            with pytest.raises(
                SeoSkillNotAvailableError,
                match="Unknown SEO skill: seo_unknown",
            ):
                await run_single_seo_skill(
                    session,
                    uuid4(),
                    "seo_unknown",
                    "url",
                    url="https://example.com",
                )

    asyncio.run(run())


@pytest.mark.parametrize(
    ("status", "expected_message"),
    [
        ("needs_config", "SEO skill requires additional configuration: seo_geo"),
        ("external_required", "SEO skill requires an external integration: seo_geo"),
        ("planned", "SEO skill is planned but not implemented yet: seo_geo"),
    ],
)
def test_run_single_seo_skill_unavailable_status_does_not_call_provider(
    status: str,
    expected_message: str,
) -> None:
    async def run() -> None:
        session = AsyncMock()
        skill = _available_skill(status=status)

        with (
            patch(
                "app.services.seo_skills.skill_runner.get_seo_skill_by_key",
                return_value=skill,
            ),
            patch(
                "app.services.seo_skills.skill_runner.generate_structured_json_with_provider",
                new=AsyncMock(),
            ) as mock_provider,
        ):
            with pytest.raises(SeoSkillNotAvailableError, match=expected_message):
                await run_single_seo_skill(
                    session,
                    uuid4(),
                    "seo_geo",
                    "url",
                    url="https://example.com",
                )

        mock_provider.assert_not_awaited()

    asyncio.run(run())


def test_run_single_seo_skill_unsupported_runtime_does_not_call_provider() -> None:
    async def run() -> None:
        session = AsyncMock()
        skill = _available_skill(runtime="external_api_required")

        with (
            patch(
                "app.services.seo_skills.skill_runner.get_seo_skill_by_key",
                return_value=skill,
            ),
            patch(
                "app.services.seo_skills.skill_runner.generate_structured_json_with_provider",
                new=AsyncMock(),
            ) as mock_provider,
        ):
            with pytest.raises(
                SeoSkillNotAvailableError,
                match="SEO skill runtime is not supported yet: seo_geo",
            ):
                await run_single_seo_skill(
                    session,
                    uuid4(),
                    "seo_geo",
                    "url",
                    url="https://example.com",
                )

        mock_provider.assert_not_awaited()

    asyncio.run(run())


def test_run_single_seo_skill_invalid_provider_does_not_call_provider() -> None:
    async def run() -> None:
        session = AsyncMock()
        skill = _available_skill()

        with (
            patch(
                "app.services.seo_skills.skill_runner.get_seo_skill_by_key",
                return_value=skill,
            ),
            patch(
                "app.services.seo_skills.skill_runner.generate_structured_json_with_provider",
                new=AsyncMock(),
            ) as mock_provider,
        ):
            with pytest.raises(
                SeoSkillProviderError,
                match="Unsupported AI provider for SEO skill: anthropic",
            ):
                await run_single_seo_skill(
                    session,
                    uuid4(),
                    "seo_geo",
                    "url",
                    url="https://example.com",
                    provider="anthropic",
                )

        mock_provider.assert_not_awaited()

    asyncio.run(run())


def test_run_single_seo_skill_normalizes_incomplete_output() -> None:
    async def run() -> None:
        session = AsyncMock()
        skill = _available_skill()

        with (
            patch(
                "app.services.seo_skills.skill_runner.get_seo_skill_by_key",
                return_value=skill,
            ),
            patch(
                "app.services.seo_skills.skill_runner.collect_skill_input",
                new=AsyncMock(return_value=_skill_input(warnings=[])),
            ),
            patch(
                "app.services.seo_skills.skill_runner.build_skill_system_prompt",
                return_value="system",
            ),
            patch(
                "app.services.seo_skills.skill_runner.build_skill_user_prompt",
                return_value="user",
            ),
            patch(
                "app.services.seo_skills.skill_runner.generate_structured_json_with_provider",
                new=AsyncMock(return_value={}),
            ),
        ):
            result = await run_single_seo_skill(
                session,
                uuid4(),
                "seo_geo",
                "url",
                url="https://example.com",
            )

        assert result["findings"] == []
        assert result["recommendations"] == []
        assert result["tasks"] == []
        assert result["artifacts"]["jsonLd"] == []
        assert result["summary"] == ""
        assert result["score"] is None

    asyncio.run(run())


def test_run_single_seo_skill_merges_input_collector_warnings() -> None:
    async def run() -> None:
        session = AsyncMock()
        skill = _available_skill()

        with (
            patch(
                "app.services.seo_skills.skill_runner.get_seo_skill_by_key",
                return_value=skill,
            ),
            patch(
                "app.services.seo_skills.skill_runner.collect_skill_input",
                new=AsyncMock(return_value=_skill_input(warnings=["Missing brand context."])),
            ),
            patch(
                "app.services.seo_skills.skill_runner.build_skill_system_prompt",
                return_value="system",
            ),
            patch(
                "app.services.seo_skills.skill_runner.build_skill_user_prompt",
                return_value="user",
            ),
            patch(
                "app.services.seo_skills.skill_runner.generate_structured_json_with_provider",
                new=AsyncMock(return_value={"warnings": ["AI warning."]}),
            ),
        ):
            result = await run_single_seo_skill(
                session,
                uuid4(),
                "seo_geo",
                "url",
                url="https://example.com",
            )

        assert "Missing brand context." in result["warnings"]
        assert "AI warning." in result["warnings"]

    asyncio.run(run())


def test_run_single_seo_skill_provider_error_is_readable() -> None:
    async def run() -> None:
        session = AsyncMock()
        skill = _available_skill()

        with (
            patch(
                "app.services.seo_skills.skill_runner.get_seo_skill_by_key",
                return_value=skill,
            ),
            patch(
                "app.services.seo_skills.skill_runner.collect_skill_input",
                new=AsyncMock(return_value=_skill_input(warnings=[])),
            ),
            patch(
                "app.services.seo_skills.skill_runner.build_skill_system_prompt",
                return_value="system",
            ),
            patch(
                "app.services.seo_skills.skill_runner.build_skill_user_prompt",
                return_value="user",
            ),
            patch(
                "app.services.seo_skills.skill_runner.generate_structured_json_with_provider",
                new=AsyncMock(side_effect=ClaudeRequestError("timeout")),
            ),
        ):
            with pytest.raises(
                SeoSkillProviderError,
                match="Errore temporaneo del provider AI",
            ):
                await run_single_seo_skill(
                    session,
                    uuid4(),
                    "seo_geo",
                    "url",
                    url="https://example.com",
                    provider="claude",
                )

    asyncio.run(run())


def test_run_single_seo_skill_uses_operation_key_claude_seo_geo() -> None:
    async def run() -> None:
        session = AsyncMock()
        project_id = uuid4()
        run_id = uuid4()
        skill = _available_skill()
        captured: dict[str, AiRequestMetadata] = {}

        async def _capture_provider(**kwargs: object) -> dict:
            metadata = kwargs["metadata"]
            assert isinstance(metadata, AiRequestMetadata)
            captured["metadata"] = metadata
            return {"summary": "ok"}

        with (
            patch(
                "app.services.seo_skills.skill_runner.get_seo_skill_by_key",
                return_value=skill,
            ),
            patch(
                "app.services.seo_skills.skill_runner.collect_skill_input",
                new=AsyncMock(return_value=_skill_input(warnings=[])),
            ),
            patch(
                "app.services.seo_skills.skill_runner.build_skill_system_prompt",
                return_value="system",
            ),
            patch(
                "app.services.seo_skills.skill_runner.build_skill_user_prompt",
                return_value="user",
            ),
            patch(
                "app.services.seo_skills.skill_runner.generate_structured_json_with_provider",
                new=AsyncMock(side_effect=_capture_provider),
            ),
        ):
            result = await run_single_seo_skill(
                session,
                project_id,
                "seo_geo",
                "url",
                url="https://example.com",
                provider="claude",
                run_id=run_id,
            )

        assert result["operationKey"] == "claude_seo_geo"
        metadata = captured["metadata"]
        assert metadata.operation_key == "claude_seo_geo"
        assert metadata.job_id == str(run_id)
        assert metadata.module == "seo_skills"
        assert metadata.entity_type == "url"
        assert metadata.context_profile == "seo_skill_audit"

    asyncio.run(run())


def test_run_single_seo_skill_openai_passes_json_schema() -> None:
    async def run() -> None:
        session = AsyncMock()
        skill = _available_skill()
        captured_kwargs: dict[str, object] = {}

        async def _capture_provider(**kwargs: object) -> dict:
            captured_kwargs.update(kwargs)
            return {"summary": "ok"}

        with (
            patch(
                "app.services.seo_skills.skill_runner.get_seo_skill_by_key",
                return_value=skill,
            ),
            patch(
                "app.services.seo_skills.skill_runner.collect_skill_input",
                new=AsyncMock(return_value=_skill_input(warnings=[])),
            ),
            patch(
                "app.services.seo_skills.skill_runner.build_skill_system_prompt",
                return_value="system",
            ),
            patch(
                "app.services.seo_skills.skill_runner.build_skill_user_prompt",
                return_value="user",
            ),
            patch(
                "app.services.seo_skills.skill_runner.generate_structured_json_with_provider",
                new=AsyncMock(side_effect=_capture_provider),
            ),
        ):
            await run_single_seo_skill(
                session,
                uuid4(),
                "seo_geo",
                "url",
                url="https://example.com",
                provider="openai",
            )

        assert captured_kwargs["json_schema_name"] == "seo_skill_output"
        assert isinstance(captured_kwargs["json_schema"], dict)
        assert captured_kwargs["json_schema"]["type"] == "object"

    asyncio.run(run())


def test_catalog_skill_seo_geo_is_available_for_runner() -> None:
    skill = get_seo_skill_by_key("seo_geo")
    assert skill is not None
    assert skill.status == "available"
    assert skill.runtime == "prompt_only"
    assert skill.enabled is True
