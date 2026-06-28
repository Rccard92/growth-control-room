"""Editorial calendar items for Content SEO Blog & Ricette."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Date, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.project import Project


class ContentSeoEditorialItem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "content_seo_editorial_items"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    title: Mapped[str] = mapped_column(String(500))
    content_type: Mapped[str] = mapped_column(String(64), index=True)
    planned_date: Mapped[date] = mapped_column(Date, index=True)
    status: Mapped[str] = mapped_column(String(32), index=True, default="idea")
    objective: Mapped[str | None] = mapped_column(String(64), nullable=True)
    primary_keyword: Mapped[str | None] = mapped_column(String(255), nullable=True)
    secondary_keywords: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    target_audience: Mapped[str | None] = mapped_column(Text, nullable=True)
    search_intent: Mapped[str | None] = mapped_column(String(32), nullable=True)
    commercial_intensity: Mapped[str | None] = mapped_column(String(32), nullable=True)
    linked_shopify_product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    linked_shopify_product_gid: Mapped[str | None] = mapped_column(String(255), nullable=True)
    linked_shopify_product_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    linked_shopify_product_handle: Mapped[str | None] = mapped_column(String(255), nullable=True)
    linked_collection_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    linked_collection_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    brief_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    article_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    publishing_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    shopify_blog_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    shopify_article_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    shopify_article_gid: Mapped[str | None] = mapped_column(String(255), nullable=True)
    shopify_article_admin_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    shopify_article_public_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    shopify_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    publish_status: Mapped[str] = mapped_column(String(32), default="not_published", index=True)
    publish_mode: Mapped[str | None] = mapped_column(String(32), nullable=True)
    scheduled_publish_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_publish_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="content_seo_editorial_items")
