"""Revision ID: 043
Revises: 042
Create Date: 2026-07-06
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "043"
down_revision: Union[str, None] = "042"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_ts = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "data_provider_usage_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=True),
        sa.Column("provider", sa.String(length=50), nullable=False, server_default="dataforseo"),
        sa.Column("endpoint", sa.String(length=255), nullable=False),
        sa.Column("operation", sa.String(length=64), nullable=False),
        sa.Column("request_hash", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("cost_usd", sa.Numeric(12, 6), nullable=True),
        sa.Column("credits_used", sa.Numeric(12, 6), nullable=True),
        sa.Column("items_count", sa.Integer(), nullable=True),
        sa.Column("metadata_json", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("response_summary", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_data_provider_usage_logs_project_id",
        "data_provider_usage_logs",
        ["project_id"],
    )
    op.create_index(
        "ix_data_provider_usage_logs_project_id_created_at",
        "data_provider_usage_logs",
        ["project_id", "created_at"],
    )
    op.create_index(
        "ix_data_provider_usage_logs_operation",
        "data_provider_usage_logs",
        ["operation"],
    )


def downgrade() -> None:
    op.drop_index("ix_data_provider_usage_logs_operation", table_name="data_provider_usage_logs")
    op.drop_index(
        "ix_data_provider_usage_logs_project_id_created_at",
        table_name="data_provider_usage_logs",
    )
    op.drop_index("ix_data_provider_usage_logs_project_id", table_name="data_provider_usage_logs")
    op.drop_table("data_provider_usage_logs")
