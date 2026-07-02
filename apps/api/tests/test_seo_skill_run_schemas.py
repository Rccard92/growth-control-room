"""Tests for SEO skill run Pydantic schemas."""

from datetime import datetime, timezone
from uuid import uuid4

from app.models.seo_skills import SeoSkillRun, SeoSkillRunResult
from app.schemas.seo_skills import (
    SeoSkillRunCreateRequest,
    SeoSkillRunDetailResponse,
    SeoSkillRunRead,
    SeoSkillRunResultRead,
)


def test_seo_skill_run_create_request_accepts_camel_case() -> None:
    request = SeoSkillRunCreateRequest.model_validate(
        {
            "targetType": "url",
            "url": "https://example.com",
            "selectedSkills": ["seo_audit", "seo_geo"],
        }
    )

    assert request.target_type == "url"
    assert request.url == "https://example.com"
    assert request.selected_skills == ["seo_audit", "seo_geo"]
    assert request.provider == "claude"


def test_seo_skill_run_read_serializes_camel_case() -> None:
    project_id = uuid4()
    run_id = uuid4()
    now = datetime.now(timezone.utc)
    run = SeoSkillRun(
        id=run_id,
        project_id=project_id,
        target_type="url",
        url="https://example.com",
        status="running",
        provider="claude",
        selected_skills=["seo_audit", "seo_geo"],
        progress_percent=50,
        current_skill="seo_audit",
        started_at=now,
        created_at=now,
        updated_at=now,
    )

    dumped = SeoSkillRunRead.model_validate(run).model_dump(by_alias=True)

    assert dumped["id"] == run_id
    assert dumped["projectId"] == project_id
    assert dumped["targetType"] == "url"
    assert dumped["selectedSkills"] == ["seo_audit", "seo_geo"]
    assert dumped["progressPercent"] == 50
    assert dumped["currentSkill"] == "seo_audit"
    assert dumped["startedAt"] == now


def test_seo_skill_run_result_read_serializes_camel_case() -> None:
    project_id = uuid4()
    run_id = uuid4()
    result_id = uuid4()
    now = datetime.now(timezone.utc)
    result = SeoSkillRunResult(
        id=result_id,
        run_id=run_id,
        project_id=project_id,
        skill_key="seo_audit",
        status="completed",
        score=88,
        findings=[{"issue": "missing meta description"}],
        recommendations=["Add a concise meta description"],
        raw_output={"summary": "ok"},
        completed_at=now,
        created_at=now,
        updated_at=now,
    )

    dumped = SeoSkillRunResultRead.model_validate(result).model_dump(by_alias=True)

    assert dumped["runId"] == run_id
    assert dumped["projectId"] == project_id
    assert dumped["skillKey"] == "seo_audit"
    assert dumped["rawOutput"] == {"summary": "ok"}
    assert dumped["completedAt"] == now


def test_seo_skill_run_detail_response_with_two_results() -> None:
    project_id = uuid4()
    run_id = uuid4()
    now = datetime.now(timezone.utc)
    run = SeoSkillRun(
        id=run_id,
        project_id=project_id,
        target_type="url",
        url="https://example.com",
        status="partial_failed",
        provider="claude",
        selected_skills=["seo_audit", "seo_geo"],
        progress_percent=100,
        created_at=now,
        updated_at=now,
    )
    results = [
        SeoSkillRunResult(
            id=uuid4(),
            run_id=run_id,
            project_id=project_id,
            skill_key="seo_audit",
            status="completed",
            score=90,
            created_at=now,
            updated_at=now,
        ),
        SeoSkillRunResult(
            id=uuid4(),
            run_id=run_id,
            project_id=project_id,
            skill_key="seo_geo",
            status="failed",
            error_message="Provider unavailable",
            created_at=now,
            updated_at=now,
        ),
    ]

    response = SeoSkillRunDetailResponse(
        run=SeoSkillRunRead.model_validate(run),
        results=[SeoSkillRunResultRead.model_validate(item) for item in results],
    )
    dumped = response.model_dump(by_alias=True)

    assert dumped["run"]["id"] == run_id
    assert dumped["run"]["progressPercent"] == 100
    assert len(dumped["results"]) == 2
    assert dumped["results"][0]["skillKey"] == "seo_audit"
    assert dumped["results"][1]["errorMessage"] == "Provider unavailable"
