"""Revision ID: 032
Revises: 031
Create Date: 2026-06-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "032"
down_revision: Union[str, None] = "031"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ai_usage_logs",
        sa.Column("model_tier", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "ai_usage_logs",
        sa.Column("model_policy_source", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "ai_usage_logs",
        sa.Column("requested_model", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "ai_usage_logs",
        sa.Column("max_output_tokens", sa.Integer(), nullable=True),
    )
    op.add_column(
        "ai_usage_logs",
        sa.Column("temperature", sa.Numeric(4, 2), nullable=True),
    )
    op.add_column(
        "ai_usage_logs",
        sa.Column("reasoning_effort", sa.String(length=32), nullable=True),
    )
    op.create_index(
        "ix_ai_usage_logs_model_tier",
        "ai_usage_logs",
        ["model_tier"],
    )


def downgrade() -> None:
    op.drop_index("ix_ai_usage_logs_model_tier", table_name="ai_usage_logs")
    op.drop_column("ai_usage_logs", "reasoning_effort")
    op.drop_column("ai_usage_logs", "temperature")
    op.drop_column("ai_usage_logs", "max_output_tokens")
    op.drop_column("ai_usage_logs", "requested_model")
    op.drop_column("ai_usage_logs", "model_policy_source")
    op.drop_column("ai_usage_logs", "model_tier")
