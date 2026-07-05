"""Revision ID: 042
Revises: 041
Create Date: 2026-07-05
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "042"
down_revision: Union[str, None] = "041"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "projects",
        sa.Column("google_merchant_account_id", sa.Text(), nullable=True),
    )
    op.add_column(
        "projects",
        sa.Column("google_merchant_account_name", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("projects", "google_merchant_account_name")
    op.drop_column("projects", "google_merchant_account_id")
