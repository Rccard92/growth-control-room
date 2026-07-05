"""Revision ID: 039
Revises: 038
Create Date: 2026-06-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "039"
down_revision: Union[str, None] = "038"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("public_site_url", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("projects", "public_site_url")
