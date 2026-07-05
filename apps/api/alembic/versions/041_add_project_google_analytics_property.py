"""Revision ID: 041
Revises: 040
Create Date: 2026-06-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "041"
down_revision: Union[str, None] = "040"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "projects",
        sa.Column("google_analytics_property_id", sa.Text(), nullable=True),
    )
    op.add_column(
        "projects",
        sa.Column("google_analytics_property_name", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("projects", "google_analytics_property_name")
    op.drop_column("projects", "google_analytics_property_id")
