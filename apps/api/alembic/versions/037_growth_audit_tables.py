"""Revision ID: 037
Revises: 036
Create Date: 2026-06-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "037"
down_revision: Union[str, None] = "036"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_ts = sa.DateTime(timezone=True)
_uuid = postgresql.UUID(as_uuid=True)
_jsonb = postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.create_table(
        "growth_audit_runs",
        sa.Column("id", _uuid, nullable=False),
        sa.Column("project_id", _uuid, nullable=False),
        sa.Column("root_url", sa.Text(), nullable=False),
        sa.Column("normalized_domain", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=40), server_default="pending", nullable=False),
        sa.Column("phase", sa.String(length=60), nullable=True),
        sa.Column("audit_mode", sa.String(length=50), server_default="full_site_mvp", nullable=False),
        sa.Column("provider", sa.String(length=30), server_default="openai", nullable=False),
        sa.Column("progress_percent", sa.Integer(), server_default="0", nullable=False),
        sa.Column("pages_discovered", sa.Integer(), server_default="0", nullable=False),
        sa.Column("pages_classified", sa.Integer(), server_default="0", nullable=False),
        sa.Column("pages_analyzed", sa.Integer(), server_default="0", nullable=False),
        sa.Column("pages_failed", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_pages", sa.Integer(), nullable=True),
        sa.Column("current_url", sa.Text(), nullable=True),
        sa.Column("config", _jsonb, nullable=True),
        sa.Column("summary", _jsonb, nullable=True),
        sa.Column("site_score", sa.Integer(), nullable=True),
        sa.Column("seo_score", sa.Integer(), nullable=True),
        sa.Column("geo_score", sa.Integer(), nullable=True),
        sa.Column("cro_score", sa.Integer(), nullable=True),
        sa.Column("performance_score", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", _ts, nullable=True),
        sa.Column("completed_at", _ts, nullable=True),
        sa.Column("created_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_growth_audit_runs_project_id", "growth_audit_runs", ["project_id"])
    op.create_index("ix_growth_audit_runs_status", "growth_audit_runs", ["status"])
    op.create_index(
        "ix_growth_audit_runs_project_id_status",
        "growth_audit_runs",
        ["project_id", "status"],
    )
    op.create_index(
        "ix_growth_audit_runs_project_id_created_at",
        "growth_audit_runs",
        ["project_id", "created_at"],
    )
    op.create_index(
        "ix_growth_audit_runs_normalized_domain",
        "growth_audit_runs",
        ["normalized_domain"],
    )

    op.create_table(
        "growth_audit_pages",
        sa.Column("id", _uuid, nullable=False),
        sa.Column("run_id", _uuid, nullable=False),
        sa.Column("project_id", _uuid, nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("normalized_url", sa.Text(), nullable=False),
        sa.Column("path", sa.Text(), nullable=True),
        sa.Column("page_type", sa.String(length=50), server_default="unknown", nullable=False),
        sa.Column("source", sa.String(length=50), server_default="seed", nullable=False),
        sa.Column("status", sa.String(length=40), server_default="pending", nullable=False),
        sa.Column("priority", sa.String(length=30), server_default="normal", nullable=False),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("meta_description", sa.Text(), nullable=True),
        sa.Column("canonical_url", sa.Text(), nullable=True),
        sa.Column("h1", sa.Text(), nullable=True),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("depth", sa.Integer(), nullable=True),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("seo_score", sa.Integer(), nullable=True),
        sa.Column("geo_score", sa.Integer(), nullable=True),
        sa.Column("cro_score", sa.Integer(), nullable=True),
        sa.Column("performance_score", sa.Integer(), nullable=True),
        sa.Column("discovered_at", _ts, nullable=True),
        sa.Column("classified_at", _ts, nullable=True),
        sa.Column("analyzed_at", _ts, nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata", _jsonb, nullable=True),
        sa.Column("created_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["run_id"], ["growth_audit_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_growth_audit_pages_run_id", "growth_audit_pages", ["run_id"])
    op.create_index("ix_growth_audit_pages_project_id", "growth_audit_pages", ["project_id"])
    op.create_index("ix_growth_audit_pages_page_type", "growth_audit_pages", ["page_type"])
    op.create_index("ix_growth_audit_pages_status", "growth_audit_pages", ["status"])
    op.create_index(
        "ix_growth_audit_pages_run_id_page_type",
        "growth_audit_pages",
        ["run_id", "page_type"],
    )
    op.create_index(
        "ix_growth_audit_pages_project_id_normalized_url",
        "growth_audit_pages",
        ["project_id", "normalized_url"],
    )
    op.create_index(
        "ix_growth_audit_pages_run_id_status",
        "growth_audit_pages",
        ["run_id", "status"],
    )
    op.create_index(
        "ix_growth_audit_pages_run_id_score",
        "growth_audit_pages",
        ["run_id", "score"],
    )

    op.create_table(
        "growth_audit_page_results",
        sa.Column("id", _uuid, nullable=False),
        sa.Column("run_id", _uuid, nullable=False),
        sa.Column("page_id", _uuid, nullable=False),
        sa.Column("project_id", _uuid, nullable=False),
        sa.Column("result_type", sa.String(length=50), nullable=False),
        sa.Column("skill_key", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=40), server_default="pending", nullable=False),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("findings", _jsonb, nullable=True),
        sa.Column("recommendations", _jsonb, nullable=True),
        sa.Column("tasks", _jsonb, nullable=True),
        sa.Column("artifacts", _jsonb, nullable=True),
        sa.Column("raw_output", _jsonb, nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", _ts, nullable=True),
        sa.Column("completed_at", _ts, nullable=True),
        sa.Column("created_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["page_id"], ["growth_audit_pages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["run_id"], ["growth_audit_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_growth_audit_page_results_run_id",
        "growth_audit_page_results",
        ["run_id"],
    )
    op.create_index(
        "ix_growth_audit_page_results_page_id",
        "growth_audit_page_results",
        ["page_id"],
    )
    op.create_index(
        "ix_growth_audit_page_results_project_id",
        "growth_audit_page_results",
        ["project_id"],
    )
    op.create_index(
        "ix_growth_audit_page_results_run_id_page_id",
        "growth_audit_page_results",
        ["run_id", "page_id"],
    )
    op.create_index(
        "ix_growth_audit_page_results_page_id_result_type",
        "growth_audit_page_results",
        ["page_id", "result_type"],
    )
    op.create_index(
        "ix_growth_audit_page_results_skill_key",
        "growth_audit_page_results",
        ["skill_key"],
    )

    op.create_table(
        "growth_audit_findings",
        sa.Column("id", _uuid, nullable=False),
        sa.Column("run_id", _uuid, nullable=False),
        sa.Column("page_id", _uuid, nullable=True),
        sa.Column("project_id", _uuid, nullable=False),
        sa.Column("source_result_id", _uuid, nullable=True),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("severity", sa.String(length=30), server_default="medium", nullable=False),
        sa.Column("priority", sa.String(length=30), server_default="medium", nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("evidence", sa.Text(), nullable=True),
        sa.Column("recommendation", sa.Text(), nullable=True),
        sa.Column("how_to_validate", sa.Text(), nullable=True),
        sa.Column("impact", sa.String(length=30), nullable=True),
        sa.Column("effort", sa.String(length=30), nullable=True),
        sa.Column("status", sa.String(length=30), server_default="open", nullable=False),
        sa.Column("metadata", _jsonb, nullable=True),
        sa.Column("created_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["page_id"], ["growth_audit_pages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["run_id"], ["growth_audit_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["source_result_id"],
            ["growth_audit_page_results.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_growth_audit_findings_run_id", "growth_audit_findings", ["run_id"])
    op.create_index("ix_growth_audit_findings_page_id", "growth_audit_findings", ["page_id"])
    op.create_index(
        "ix_growth_audit_findings_project_id",
        "growth_audit_findings",
        ["project_id"],
    )
    op.create_index(
        "ix_growth_audit_findings_run_id_severity",
        "growth_audit_findings",
        ["run_id", "severity"],
    )
    op.create_index(
        "ix_growth_audit_findings_page_id_severity",
        "growth_audit_findings",
        ["page_id", "severity"],
    )
    op.create_index(
        "ix_growth_audit_findings_project_id_status",
        "growth_audit_findings",
        ["project_id", "status"],
    )

    op.create_table(
        "growth_audit_tasks",
        sa.Column("id", _uuid, nullable=False),
        sa.Column("run_id", _uuid, nullable=False),
        sa.Column("page_id", _uuid, nullable=True),
        sa.Column("finding_id", _uuid, nullable=True),
        sa.Column("project_id", _uuid, nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("owner_type", sa.String(length=30), server_default="seo", nullable=False),
        sa.Column("priority", sa.String(length=30), server_default="medium", nullable=False),
        sa.Column("estimated_effort", sa.String(length=30), server_default="medium", nullable=False),
        sa.Column("status", sa.String(length=30), server_default="open", nullable=False),
        sa.Column("metadata", _jsonb, nullable=True),
        sa.Column("completed_at", _ts, nullable=True),
        sa.Column("created_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["finding_id"], ["growth_audit_findings.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["page_id"], ["growth_audit_pages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["run_id"], ["growth_audit_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_growth_audit_tasks_run_id", "growth_audit_tasks", ["run_id"])
    op.create_index("ix_growth_audit_tasks_page_id", "growth_audit_tasks", ["page_id"])
    op.create_index("ix_growth_audit_tasks_project_id", "growth_audit_tasks", ["project_id"])
    op.create_index(
        "ix_growth_audit_tasks_run_id_status",
        "growth_audit_tasks",
        ["run_id", "status"],
    )
    op.create_index(
        "ix_growth_audit_tasks_page_id_status",
        "growth_audit_tasks",
        ["page_id", "status"],
    )
    op.create_index(
        "ix_growth_audit_tasks_project_id_priority",
        "growth_audit_tasks",
        ["project_id", "priority"],
    )

    op.create_table(
        "growth_audit_events",
        sa.Column("id", _uuid, nullable=False),
        sa.Column("run_id", _uuid, nullable=False),
        sa.Column("project_id", _uuid, nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("phase", sa.String(length=60), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("progress_percent", sa.Integer(), nullable=True),
        sa.Column("payload", _jsonb, nullable=True),
        sa.Column("created_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["run_id"], ["growth_audit_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_growth_audit_events_run_id", "growth_audit_events", ["run_id"])
    op.create_index("ix_growth_audit_events_project_id", "growth_audit_events", ["project_id"])
    op.create_index(
        "ix_growth_audit_events_run_id_created_at",
        "growth_audit_events",
        ["run_id", "created_at"],
    )
    op.create_index(
        "ix_growth_audit_events_project_id_created_at",
        "growth_audit_events",
        ["project_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_growth_audit_events_project_id_created_at",
        table_name="growth_audit_events",
    )
    op.drop_index(
        "ix_growth_audit_events_run_id_created_at",
        table_name="growth_audit_events",
    )
    op.drop_index("ix_growth_audit_events_project_id", table_name="growth_audit_events")
    op.drop_index("ix_growth_audit_events_run_id", table_name="growth_audit_events")
    op.drop_table("growth_audit_events")

    op.drop_index(
        "ix_growth_audit_tasks_project_id_priority",
        table_name="growth_audit_tasks",
    )
    op.drop_index("ix_growth_audit_tasks_page_id_status", table_name="growth_audit_tasks")
    op.drop_index("ix_growth_audit_tasks_run_id_status", table_name="growth_audit_tasks")
    op.drop_index("ix_growth_audit_tasks_project_id", table_name="growth_audit_tasks")
    op.drop_index("ix_growth_audit_tasks_page_id", table_name="growth_audit_tasks")
    op.drop_index("ix_growth_audit_tasks_run_id", table_name="growth_audit_tasks")
    op.drop_table("growth_audit_tasks")

    op.drop_index(
        "ix_growth_audit_findings_project_id_status",
        table_name="growth_audit_findings",
    )
    op.drop_index(
        "ix_growth_audit_findings_page_id_severity",
        table_name="growth_audit_findings",
    )
    op.drop_index(
        "ix_growth_audit_findings_run_id_severity",
        table_name="growth_audit_findings",
    )
    op.drop_index("ix_growth_audit_findings_project_id", table_name="growth_audit_findings")
    op.drop_index("ix_growth_audit_findings_page_id", table_name="growth_audit_findings")
    op.drop_index("ix_growth_audit_findings_run_id", table_name="growth_audit_findings")
    op.drop_table("growth_audit_findings")

    op.drop_index(
        "ix_growth_audit_page_results_skill_key",
        table_name="growth_audit_page_results",
    )
    op.drop_index(
        "ix_growth_audit_page_results_page_id_result_type",
        table_name="growth_audit_page_results",
    )
    op.drop_index(
        "ix_growth_audit_page_results_run_id_page_id",
        table_name="growth_audit_page_results",
    )
    op.drop_index(
        "ix_growth_audit_page_results_project_id",
        table_name="growth_audit_page_results",
    )
    op.drop_index(
        "ix_growth_audit_page_results_page_id",
        table_name="growth_audit_page_results",
    )
    op.drop_index(
        "ix_growth_audit_page_results_run_id",
        table_name="growth_audit_page_results",
    )
    op.drop_table("growth_audit_page_results")

    op.drop_index("ix_growth_audit_pages_run_id_score", table_name="growth_audit_pages")
    op.drop_index("ix_growth_audit_pages_run_id_status", table_name="growth_audit_pages")
    op.drop_index(
        "ix_growth_audit_pages_project_id_normalized_url",
        table_name="growth_audit_pages",
    )
    op.drop_index(
        "ix_growth_audit_pages_run_id_page_type",
        table_name="growth_audit_pages",
    )
    op.drop_index("ix_growth_audit_pages_status", table_name="growth_audit_pages")
    op.drop_index("ix_growth_audit_pages_page_type", table_name="growth_audit_pages")
    op.drop_index("ix_growth_audit_pages_project_id", table_name="growth_audit_pages")
    op.drop_index("ix_growth_audit_pages_run_id", table_name="growth_audit_pages")
    op.drop_table("growth_audit_pages")

    op.drop_index(
        "ix_growth_audit_runs_normalized_domain",
        table_name="growth_audit_runs",
    )
    op.drop_index(
        "ix_growth_audit_runs_project_id_created_at",
        table_name="growth_audit_runs",
    )
    op.drop_index(
        "ix_growth_audit_runs_project_id_status",
        table_name="growth_audit_runs",
    )
    op.drop_index("ix_growth_audit_runs_status", table_name="growth_audit_runs")
    op.drop_index("ix_growth_audit_runs_project_id", table_name="growth_audit_runs")
    op.drop_table("growth_audit_runs")
