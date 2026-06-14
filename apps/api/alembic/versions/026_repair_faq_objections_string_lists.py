"""Repair legacy FAQ & Objections JSONB dict arrays to list[str].

Revision ID: 026
Revises: 025
Create Date: 2026-06-13
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.services.brand_intelligence.faq_objections_normalize import normalize_to_string_list

revision: str = "026"
down_revision: Union[str, None] = "025"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_STRING_LIST_FIELDS = (
    "general_faq",
    "product_process_questions",
    "purchase_shipping_questions",
    "objections",
    "myths_misconceptions",
    "recommended_answers",
    "content_opportunities",
    "social_comment_insights",
)


def _field_value_changed(current: object | None, normalized: list[str]) -> bool:
    if current is None:
        return bool(normalized)
    if not isinstance(current, list):
        return True
    if len(current) != len(normalized):
        return True
    for item, norm in zip(current, normalized, strict=False):
        if item != norm:
            return True
    return False


def upgrade() -> None:
    bind = op.get_bind()
    metadata = sa.MetaData()
    table = sa.Table("brand_faq_objections", metadata, autoload_with=bind)

    rows = bind.execute(sa.select(table.c.id, *[table.c[field] for field in _STRING_LIST_FIELDS]))
    for row in rows:
        updates: dict[str, list[str]] = {}
        mapping = row._mapping
        for field in _STRING_LIST_FIELDS:
            current = mapping[field]
            normalized = normalize_to_string_list(current)
            if _field_value_changed(current, normalized):
                updates[field] = normalized
        if updates:
            bind.execute(
                table.update().where(table.c.id == mapping["id"]).values(**updates)
            )


def downgrade() -> None:
    """No-op: string lists are the canonical format."""
