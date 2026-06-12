import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.shopify import ShopifyStore


class SeoEntityAnalysis(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "seo_entity_analyses"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "shopify_store_id",
            "entity_type",
            "entity_id",
            name="uq_seo_entity_analyses_entity",
        ),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    shopify_store_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shopify_stores.id", ondelete="CASCADE"),
        index=True,
    )
    entity_type: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    entity_gid: Mapped[str] = mapped_column(String(255))
    entity_title: Mapped[str] = mapped_column(String(500))
    score_total: Mapped[int] = mapped_column(Integer, default=0)
    score_title: Mapped[int] = mapped_column(Integer, default=0)
    score_seo_title: Mapped[int] = mapped_column(Integer, default=0)
    score_meta_description: Mapped[int] = mapped_column(Integer, default=0)
    score_description: Mapped[int] = mapped_column(Integer, default=0)
    score_image_alt: Mapped[int] = mapped_column(Integer, default=0)
    score_handle: Mapped[int] = mapped_column(Integer, default=0)
    score_tags: Mapped[int] = mapped_column(Integer, default=0)
    severity: Mapped[str] = mapped_column(String(20), default="warning")
    issues: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, nullable=True)
    recommendations: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, nullable=True)
    last_analyzed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    project: Mapped["Project"] = relationship()
    store: Mapped["ShopifyStore"] = relationship()


class SeoOptimizationProposal(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "seo_optimization_proposals"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    shopify_store_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shopify_stores.id", ondelete="CASCADE"),
        index=True,
    )
    entity_type: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    entity_gid: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20), default="draft")
    source: Mapped[str] = mapped_column(String(20), default="rules")
    current_values: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    proposed_values: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    reasoning: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)
    risk_level: Mapped[str] = mapped_column(String(20), default="low")
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    applied_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    project: Mapped["Project"] = relationship()
    store: Mapped["ShopifyStore"] = relationship()
    change_logs: Mapped[list["SeoChangeLog"]] = relationship(
        back_populates="proposal",
        cascade="all, delete-orphan",
    )


class SeoChangeLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "seo_change_logs"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    shopify_store_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shopify_stores.id", ondelete="CASCADE"),
        index=True,
    )
    proposal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("seo_optimization_proposals.id", ondelete="CASCADE"),
        index=True,
    )
    entity_type: Mapped[str] = mapped_column(String(50))
    entity_gid: Mapped[str] = mapped_column(String(255))
    applied_values: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    shopify_response: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(20))
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    project: Mapped["Project"] = relationship()
    store: Mapped["ShopifyStore"] = relationship()
    proposal: Mapped["SeoOptimizationProposal"] = relationship(back_populates="change_logs")
