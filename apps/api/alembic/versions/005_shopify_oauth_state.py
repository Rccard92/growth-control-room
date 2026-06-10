"""shopify oauth state

Revision ID: 005
Revises: 004
Create Date: 2026-06-10

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "shopify_oauth_states",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("shop_domain", sa.String(length=255), nullable=False),
        sa.Column("state", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name=op.f("fk_shopify_oauth_states_project_id_projects"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_shopify_oauth_states")),
    )
    op.create_index(
        op.f("ix_shopify_oauth_states_project_id"),
        "shopify_oauth_states",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_shopify_oauth_states_state"),
        "shopify_oauth_states",
        ["state"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_shopify_oauth_states_state"), table_name="shopify_oauth_states")
    op.drop_index(op.f("ix_shopify_oauth_states_project_id"), table_name="shopify_oauth_states")
    op.drop_table("shopify_oauth_states")
