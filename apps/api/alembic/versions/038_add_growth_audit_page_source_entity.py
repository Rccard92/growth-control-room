"""Revision ID: 038
Revises: 037
Create Date: 2026-06-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "038"
down_revision: Union[str, None] = "037"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_ts = sa.DateTime(timezone=True)
_uuid = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.add_column(
        "growth_audit_pages",
        sa.Column("source_entity_type", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "growth_audit_pages",
        sa.Column("source_entity_id", _uuid, nullable=True),
    )
    op.add_column(
        "growth_audit_pages",
        sa.Column("source_entity_gid", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "growth_audit_pages",
        sa.Column("source_entity_handle", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "growth_audit_pages",
        sa.Column("source_entity_title", sa.Text(), nullable=True),
    )
    op.add_column(
        "growth_audit_pages",
        sa.Column("source_entity_synced_at", _ts, nullable=True),
    )
    op.create_index(
        "ix_growth_audit_pages_project_id_source_entity_type",
        "growth_audit_pages",
        ["project_id", "source_entity_type"],
    )
    op.create_index(
        "ix_growth_audit_pages_source_entity_type_id",
        "growth_audit_pages",
        ["source_entity_type", "source_entity_id"],
    )
    op.create_index(
        "ix_growth_audit_pages_run_id_source_entity_type",
        "growth_audit_pages",
        ["run_id", "source_entity_type"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_growth_audit_pages_run_id_source_entity_type",
        table_name="growth_audit_pages",
    )
    op.drop_index(
        "ix_growth_audit_pages_source_entity_type_id",
        table_name="growth_audit_pages",
    )
    op.drop_index(
        "ix_growth_audit_pages_project_id_source_entity_type",
        table_name="growth_audit_pages",
    )
    op.drop_column("growth_audit_pages", "source_entity_synced_at")
    op.drop_column("growth_audit_pages", "source_entity_title")
    op.drop_column("growth_audit_pages", "source_entity_handle")
    op.drop_column("growth_audit_pages", "source_entity_gid")
    op.drop_column("growth_audit_pages", "source_entity_id")
    op.drop_column("growth_audit_pages", "source_entity_type")
