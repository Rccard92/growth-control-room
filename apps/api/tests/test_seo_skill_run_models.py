"""Tests for SEO skill run SQLAlchemy models."""

from datetime import datetime, timezone
from uuid import uuid4

from app.models.seo_skills import SeoSkillRun, SeoSkillRunResult


def test_seo_skill_run_model_instantiation() -> None:
    project_id = uuid4()
    run = SeoSkillRun(
        project_id=project_id,
        target_type="url",
        url="https://example.com",
        status="pending",
        provider="claude",
        selected_skills=["seo_audit", "seo_geo"],
        progress_percent=0,
    )

    assert run.__tablename__ == "seo_skill_runs"
    assert run.project_id == project_id
    assert run.target_type == "url"
    assert run.selected_skills == ["seo_audit", "seo_geo"]
    assert run.status == "pending"
    assert run.provider == "claude"


def test_seo_skill_run_result_model_instantiation() -> None:
    project_id = uuid4()
    run_id = uuid4()
    result = SeoSkillRunResult(
        run_id=run_id,
        project_id=project_id,
        skill_key="seo_audit",
        status="pending",
        score=82,
        findings=[{"type": "title", "severity": "medium"}],
    )

    assert result.__tablename__ == "seo_skill_run_results"
    assert result.run_id == run_id
    assert result.project_id == project_id
    assert result.skill_key == "seo_audit"
    assert result.score == 82


def test_seo_skill_run_results_relationship_and_cascade() -> None:
    project_id = uuid4()
    run = SeoSkillRun(
        id=uuid4(),
        project_id=project_id,
        target_type="url",
        url="https://example.com",
        selected_skills=["seo_audit", "seo_geo"],
    )
    first_result = SeoSkillRunResult(
        id=uuid4(),
        run_id=run.id,
        project_id=project_id,
        skill_key="seo_audit",
        status="completed",
        started_at=datetime.now(timezone.utc),
    )
    second_result = SeoSkillRunResult(
        id=uuid4(),
        run_id=run.id,
        project_id=project_id,
        skill_key="seo_geo",
        status="pending",
    )
    run.results = [first_result, second_result]

    assert len(run.results) == 2
    assert first_result.run is run
    assert second_result.run is run
    assert run.results[0].skill_key == "seo_audit"
    assert run.results[1].skill_key == "seo_geo"

    cascade = SeoSkillRun.__mapper__.relationships["results"].cascade
    assert "delete" in cascade
    assert "save-update" in cascade
