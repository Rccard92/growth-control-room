"""Revision ID: 028
Revises: 027
Create Date: 2026-06-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "028"
down_revision: Union[str, None] = "027"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_jsonb = postgresql.JSONB(astext_type=sa.Text())
_ts = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "content_seo_brief_generation_jobs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("month", sa.String(length=7), nullable=True),
        sa.Column("only_status", sa.String(length=32), nullable=False, server_default="idea"),
        sa.Column("total_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("current_item_id", sa.UUID(), nullable=True),
        sa.Column("current_item_title", sa.String(length=500), nullable=True),
        sa.Column("errors", _jsonb, nullable=True),
        sa.Column("created_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.Column("completed_at", _ts, nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_content_seo_brief_generation_jobs_project_id",
        "content_seo_brief_generation_jobs",
        ["project_id"],
    )
    op.create_index(
        "ix_content_seo_brief_generation_jobs_status",
        "content_seo_brief_generation_jobs",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_content_seo_brief_generation_jobs_status",
        table_name="content_seo_brief_generation_jobs",
    )
    op.drop_index(
        "ix_content_seo_brief_generation_jobs_project_id",
        table_name="content_seo_brief_generation_jobs",
    )
    op.drop_table("content_seo_brief_generation_jobs")
