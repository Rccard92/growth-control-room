"""Revision ID: 040
Revises: 039
Create Date: 2026-06-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "040"
down_revision: Union[str, None] = "039"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("search_console_site_url", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("projects", "search_console_site_url")
