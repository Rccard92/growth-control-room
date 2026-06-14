"""Revision ID: 033
Revises: 032
Create Date: 2026-06-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "033"
down_revision: Union[str, None] = "032"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ai_model_settings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=True),
        sa.Column("operation_key", sa.String(length=64), nullable=False),
        sa.Column("module", sa.String(length=64), nullable=False),
        sa.Column("operation", sa.String(length=64), nullable=False),
        sa.Column("context_profile", sa.String(length=64), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("model_tier", sa.String(length=32), nullable=False),
        sa.Column("max_output_tokens", sa.Integer(), nullable=True),
        sa.Column("temperature", sa.Numeric(4, 2), nullable=True),
        sa.Column("reasoning_effort", sa.String(length=32), nullable=True),
        sa.Column("fallback_model", sa.String(length=100), nullable=True),
        sa.Column("allow_fallback", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=False, server_default="default"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "operation_key", name="uq_ai_model_settings_project_operation"),
    )
    op.create_index("ix_ai_model_settings_project_id", "ai_model_settings", ["project_id"])
    op.create_index("ix_ai_model_settings_operation_key", "ai_model_settings", ["operation_key"])

    op.add_column(
        "ai_usage_logs",
        sa.Column("operation_key", sa.String(length=64), nullable=True),
    )
    op.create_index("ix_ai_usage_logs_operation_key", "ai_usage_logs", ["operation_key"])


def downgrade() -> None:
    op.drop_index("ix_ai_usage_logs_operation_key", table_name="ai_usage_logs")
    op.drop_column("ai_usage_logs", "operation_key")
    op.drop_index("ix_ai_model_settings_operation_key", table_name="ai_model_settings")
    op.drop_index("ix_ai_model_settings_project_id", table_name="ai_model_settings")
    op.drop_table("ai_model_settings")
