"""Revision ID: 030
Revises: 029
Create Date: 2026-06-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "030"
down_revision: Union[str, None] = "029"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_ts = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "ai_usage_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=True),
        sa.Column("provider", sa.String(length=50), nullable=False, server_default="openai"),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("module", sa.String(length=64), nullable=False),
        sa.Column("operation", sa.String(length=64), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=True),
        sa.Column("entity_id", sa.String(length=255), nullable=True),
        sa.Column("job_id", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cached_input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reasoning_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("estimated_input_cost", sa.Numeric(12, 6), nullable=True),
        sa.Column("estimated_output_cost", sa.Numeric(12, 6), nullable=True),
        sa.Column("estimated_cached_cost", sa.Numeric(12, 6), nullable=True),
        sa.Column("estimated_total_cost", sa.Numeric(12, 6), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("prompt_chars", sa.Integer(), nullable=True),
        sa.Column("output_chars", sa.Integer(), nullable=True),
        sa.Column("prompt_hash", sa.String(length=64), nullable=True),
        sa.Column("prompt_preview", sa.Text(), nullable=True),
        sa.Column("output_preview", sa.Text(), nullable=True),
        sa.Column("prompt_cache_key", sa.String(length=255), nullable=True),
        sa.Column("response_id", sa.String(length=255), nullable=True),
        sa.Column("error_type", sa.String(length=128), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_usage_logs_project_id", "ai_usage_logs", ["project_id"])
    op.create_index(
        "ix_ai_usage_logs_project_id_created_at",
        "ai_usage_logs",
        ["project_id", "created_at"],
    )
    op.create_index(
        "ix_ai_usage_logs_project_id_module",
        "ai_usage_logs",
        ["project_id", "module"],
    )
    op.create_index("ix_ai_usage_logs_model", "ai_usage_logs", ["model"])


def downgrade() -> None:
    op.drop_index("ix_ai_usage_logs_model", table_name="ai_usage_logs")
    op.drop_index("ix_ai_usage_logs_project_id_module", table_name="ai_usage_logs")
    op.drop_index("ix_ai_usage_logs_project_id_created_at", table_name="ai_usage_logs")
    op.drop_index("ix_ai_usage_logs_project_id", table_name="ai_usage_logs")
    op.drop_table("ai_usage_logs")
