"""Revision ID: 031
Revises: 030
Create Date: 2026-06-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "031"
down_revision: Union[str, None] = "030"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ai_usage_logs",
        sa.Column("context_profile", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "ai_usage_logs",
        sa.Column("context_hash", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "ai_usage_logs",
        sa.Column("context_chars", sa.Integer(), nullable=True),
    )
    op.add_column(
        "ai_usage_logs",
        sa.Column("context_blocks_used", JSONB(), nullable=True),
    )
    op.create_index(
        "ix_ai_usage_logs_context_profile",
        "ai_usage_logs",
        ["context_profile"],
    )


def downgrade() -> None:
    op.drop_index("ix_ai_usage_logs_context_profile", table_name="ai_usage_logs")
    op.drop_column("ai_usage_logs", "context_blocks_used")
    op.drop_column("ai_usage_logs", "context_chars")
    op.drop_column("ai_usage_logs", "context_hash")
    op.drop_column("ai_usage_logs", "context_profile")
