"""Revision ID: 022
Revises: 021
Create Date: 2026-06-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "022"
down_revision: Union[str, None] = "021"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_jsonb = postgresql.JSONB(astext_type=sa.Text())
_ts = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "brand_identities",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("positioning", sa.Text(), nullable=True),
        sa.Column("brand_values", _jsonb, nullable=True),
        sa.Column("differentiators", _jsonb, nullable=True),
        sa.Column("production_principles", _jsonb, nullable=True),
        sa.Column("quality_principles", _jsonb, nullable=True),
        sa.Column("trust_elements", _jsonb, nullable=True),
        sa.Column("what_brand_is", sa.Text(), nullable=True),
        sa.Column("what_brand_is_not", sa.Text(), nullable=True),
        sa.Column("storytelling_notes", sa.Text(), nullable=True),
        sa.Column("created_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", name="uq_brand_identities_project_id"),
    )
    op.create_index("ix_brand_identities_project_id", "brand_identities", ["project_id"])

    op.create_table(
        "brand_visual_identities",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("primary_logo_url", sa.String(length=500), nullable=True),
        sa.Column("secondary_logo_url", sa.String(length=500), nullable=True),
        sa.Column("favicon_url", sa.String(length=500), nullable=True),
        sa.Column("primary_color", sa.String(length=20), nullable=True),
        sa.Column("secondary_color", sa.String(length=20), nullable=True),
        sa.Column("accent_color", sa.String(length=20), nullable=True),
        sa.Column("background_color", sa.String(length=20), nullable=True),
        sa.Column("text_color", sa.String(length=20), nullable=True),
        sa.Column("color_palette", _jsonb, nullable=True),
        sa.Column("fonts", _jsonb, nullable=True),
        sa.Column("visual_style_notes", sa.Text(), nullable=True),
        sa.Column("image_style_notes", sa.Text(), nullable=True),
        sa.Column("do_show", _jsonb, nullable=True),
        sa.Column("do_not_show", _jsonb, nullable=True),
        sa.Column("website_extracted_palette", _jsonb, nullable=True),
        sa.Column("created_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", name="uq_brand_visual_identities_project_id"),
    )
    op.create_index(
        "ix_brand_visual_identities_project_id", "brand_visual_identities", ["project_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_brand_visual_identities_project_id", table_name="brand_visual_identities")
    op.drop_table("brand_visual_identities")
    op.drop_index("ix_brand_identities_project_id", table_name="brand_identities")
    op.drop_table("brand_identities")
