"""shopify order attribution columns

Revision ID: 006
Revises: 005
Create Date: 2026-06-10

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("shopify_orders", sa.Column("source_name", sa.String(100), nullable=True))
    op.add_column(
        "shopify_orders",
        sa.Column("source_identifier", sa.String(255), nullable=True),
    )
    op.add_column("shopify_orders", sa.Column("channel_name", sa.String(100), nullable=True))
    op.add_column("shopify_orders", sa.Column("landing_page", sa.Text(), nullable=True))
    op.add_column(
        "shopify_orders",
        sa.Column("referrer_source", sa.String(100), nullable=True),
    )
    op.add_column(
        "shopify_orders",
        sa.Column("referrer_name", sa.String(255), nullable=True),
    )
    op.add_column("shopify_orders", sa.Column("utm_source", sa.String(255), nullable=True))
    op.add_column("shopify_orders", sa.Column("utm_medium", sa.String(255), nullable=True))
    op.add_column("shopify_orders", sa.Column("utm_campaign", sa.String(255), nullable=True))
    op.add_column("shopify_orders", sa.Column("utm_content", sa.String(255), nullable=True))
    op.add_column("shopify_orders", sa.Column("utm_term", sa.String(255), nullable=True))
    op.add_column("shopify_orders", sa.Column("customer_type", sa.String(20), nullable=True))


def downgrade() -> None:
    op.drop_column("shopify_orders", "customer_type")
    op.drop_column("shopify_orders", "utm_term")
    op.drop_column("shopify_orders", "utm_content")
    op.drop_column("shopify_orders", "utm_campaign")
    op.drop_column("shopify_orders", "utm_medium")
    op.drop_column("shopify_orders", "utm_source")
    op.drop_column("shopify_orders", "referrer_name")
    op.drop_column("shopify_orders", "referrer_source")
    op.drop_column("shopify_orders", "landing_page")
    op.drop_column("shopify_orders", "channel_name")
    op.drop_column("shopify_orders", "source_identifier")
    op.drop_column("shopify_orders", "source_name")
