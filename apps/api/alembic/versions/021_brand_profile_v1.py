"""Revision ID: 021
Revises: 020
Create Date: 2026-06-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "021"
down_revision: Union[str, None] = "020"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_jsonb = postgresql.JSONB(astext_type=sa.Text())
_ts = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.add_column("brand_profiles", sa.Column("instagram_url", sa.String(length=500), nullable=True))
    op.add_column("brand_profiles", sa.Column("facebook_url", sa.String(length=500), nullable=True))
    op.add_column("brand_profiles", sa.Column("tiktok_url", sa.String(length=500), nullable=True))
    op.add_column("brand_profiles", sa.Column("youtube_url", sa.String(length=500), nullable=True))
    op.add_column("brand_profiles", sa.Column("linkedin_url", sa.String(length=500), nullable=True))
    op.add_column("brand_profiles", sa.Column("trustpilot_url", sa.String(length=500), nullable=True))
    op.add_column("brand_profiles", sa.Column("google_business_url", sa.String(length=500), nullable=True))
    op.add_column("brand_profiles", sa.Column("other_sources", _jsonb, nullable=True))
    op.add_column("brand_profiles", sa.Column("origin_notes", sa.Text(), nullable=True))
    op.add_column("brand_profiles", sa.Column("production_notes", sa.Text(), nullable=True))
    op.add_column("brand_profiles", sa.Column("tone_notes", sa.Text(), nullable=True))
    op.add_column("brand_profiles", sa.Column("customer_notes", sa.Text(), nullable=True))
    op.add_column("brand_profiles", sa.Column("ai_summary", sa.Text(), nullable=True))
    op.add_column("brand_profiles", sa.Column("source_status", _jsonb, nullable=True))
    op.add_column("brand_profiles", sa.Column("last_enriched_at", _ts, nullable=True))
    op.add_column("brand_profiles", sa.Column("enrichment_confidence", sa.Float(), nullable=True))
    op.add_column("brand_profiles", sa.Column("enrichment_warnings", _jsonb, nullable=True))


def downgrade() -> None:
    op.drop_column("brand_profiles", "enrichment_warnings")
    op.drop_column("brand_profiles", "enrichment_confidence")
    op.drop_column("brand_profiles", "last_enriched_at")
    op.drop_column("brand_profiles", "source_status")
    op.drop_column("brand_profiles", "ai_summary")
    op.drop_column("brand_profiles", "customer_notes")
    op.drop_column("brand_profiles", "tone_notes")
    op.drop_column("brand_profiles", "production_notes")
    op.drop_column("brand_profiles", "origin_notes")
    op.drop_column("brand_profiles", "other_sources")
    op.drop_column("brand_profiles", "google_business_url")
    op.drop_column("brand_profiles", "trustpilot_url")
    op.drop_column("brand_profiles", "linkedin_url")
    op.drop_column("brand_profiles", "youtube_url")
    op.drop_column("brand_profiles", "tiktok_url")
    op.drop_column("brand_profiles", "facebook_url")
    op.drop_column("brand_profiles", "instagram_url")
