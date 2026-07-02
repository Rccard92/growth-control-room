"""Revision ID: 036
Revises: 035
Create Date: 2026-06-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "036"
down_revision: Union[str, None] = "035"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_ts = sa.DateTime(timezone=True)
_uuid = postgresql.UUID(as_uuid=True)
_jsonb = postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.create_table(
        "seo_skill_runs",
        sa.Column("id", _uuid, nullable=False),
        sa.Column("project_id", _uuid, nullable=False),
        sa.Column("target_type", sa.String(length=50), nullable=False),
        sa.Column("target_id", _uuid, nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=30), server_default="pending", nullable=False),
        sa.Column("provider", sa.String(length=30), server_default="claude", nullable=False),
        sa.Column("selected_skills", _jsonb, nullable=False),
        sa.Column("progress_percent", sa.Integer(), server_default="0", nullable=False),
        sa.Column("current_skill", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", _ts, nullable=True),
        sa.Column("completed_at", _ts, nullable=True),
        sa.Column("created_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_seo_skill_runs_project_id", "seo_skill_runs", ["project_id"])
    op.create_index("ix_seo_skill_runs_status", "seo_skill_runs", ["status"])
    op.create_index("ix_seo_skill_runs_target_id", "seo_skill_runs", ["target_id"])
    op.create_index(
        "ix_seo_skill_runs_target_type_target_id",
        "seo_skill_runs",
        ["target_type", "target_id"],
    )

    op.create_table(
        "seo_skill_run_results",
        sa.Column("id", _uuid, nullable=False),
        sa.Column("run_id", _uuid, nullable=False),
        sa.Column("project_id", _uuid, nullable=False),
        sa.Column("skill_key", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=30), server_default="pending", nullable=False),
        sa.Column("score", sa.Integer(), nullable=True),
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
        sa.ForeignKeyConstraint(["run_id"], ["seo_skill_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_seo_skill_run_results_run_id", "seo_skill_run_results", ["run_id"])
    op.create_index(
        "ix_seo_skill_run_results_project_id",
        "seo_skill_run_results",
        ["project_id"],
    )
    op.create_index(
        "ix_seo_skill_run_results_skill_key",
        "seo_skill_run_results",
        ["skill_key"],
    )
    op.create_index("ix_seo_skill_run_results_status", "seo_skill_run_results", ["status"])


def downgrade() -> None:
    op.drop_index("ix_seo_skill_run_results_status", table_name="seo_skill_run_results")
    op.drop_index("ix_seo_skill_run_results_skill_key", table_name="seo_skill_run_results")
    op.drop_index("ix_seo_skill_run_results_project_id", table_name="seo_skill_run_results")
    op.drop_index("ix_seo_skill_run_results_run_id", table_name="seo_skill_run_results")
    op.drop_table("seo_skill_run_results")

    op.drop_index("ix_seo_skill_runs_target_type_target_id", table_name="seo_skill_runs")
    op.drop_index("ix_seo_skill_runs_target_id", table_name="seo_skill_runs")
    op.drop_index("ix_seo_skill_runs_status", table_name="seo_skill_runs")
    op.drop_index("ix_seo_skill_runs_project_id", table_name="seo_skill_runs")
    op.drop_table("seo_skill_runs")
