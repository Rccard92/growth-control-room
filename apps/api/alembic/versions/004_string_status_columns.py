"""string status columns

Revision ID: 004
Revises: 003
Create Date: 2026-06-10

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

STATUS_COLUMNS: list[tuple[str, str, str]] = [
    ("projects", "status", "active"),
    ("integrations", "status", "not_connected"),
    ("ai_runs", "status", "pending"),
    ("alerts", "level", "info"),
    ("alerts", "status", "open"),
]

PG_ENUM_TYPES = [
    "projectstatus",
    "integrationstatus",
    "airunstatus",
    "alertlevel",
    "alertstatus",
]


def upgrade() -> None:
    for table, column, default in STATUS_COLUMNS:
        op.alter_column(
            table,
            column,
            existing_type=sa.String(length=20),
            type_=sa.String(length=50),
            server_default=default,
            existing_nullable=False,
            postgresql_using=f"{column}::text",
        )

    for enum_type in PG_ENUM_TYPES:
        op.execute(sa.text(f'DROP TYPE IF EXISTS "{enum_type}" CASCADE'))


def downgrade() -> None:
    for enum_type in PG_ENUM_TYPES:
        op.execute(sa.text(f'DROP TYPE IF EXISTS "{enum_type}" CASCADE'))

    for table, column, default in STATUS_COLUMNS:
        op.alter_column(
            table,
            column,
            existing_type=sa.String(length=50),
            type_=sa.String(length=20),
            server_default=default,
            existing_nullable=False,
            postgresql_using=f"{column}::text",
        )
