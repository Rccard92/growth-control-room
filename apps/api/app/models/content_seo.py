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


class ShopifyCollection(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "shopify_collections"
    __table_args__ = (
        UniqueConstraint(
            "shopify_store_id",
            "shopify_gid",
            name="uq_shopify_collections_store_gid",
        ),
    )

    shopify_store_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shopify_stores.id", ondelete="CASCADE"),
        index=True,
    )
    shopify_gid: Mapped[str] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(500))
    handle: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    seo_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    seo_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    products_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    store: Mapped["ShopifyStore"] = relationship(back_populates="collections")


class ShopifyPage(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "shopify_pages"
    __table_args__ = (
        UniqueConstraint(
            "shopify_store_id",
            "shopify_gid",
            name="uq_shopify_pages_store_gid",
        ),
    )

    shopify_store_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shopify_stores.id", ondelete="CASCADE"),
        index=True,
    )
    shopify_gid: Mapped[str] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(500))
    handle: Mapped[str | None] = mapped_column(String(255), nullable=True)
    body_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    seo_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    seo_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at_shopify: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    store: Mapped["ShopifyStore"] = relationship(back_populates="pages")


class ShopifyBlog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "shopify_blogs"
    __table_args__ = (
        UniqueConstraint(
            "shopify_store_id",
            "shopify_gid",
            name="uq_shopify_blogs_store_gid",
        ),
    )

    shopify_store_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shopify_stores.id", ondelete="CASCADE"),
        index=True,
    )
    shopify_gid: Mapped[str] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(500))
    handle: Mapped[str | None] = mapped_column(String(255), nullable=True)
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    store: Mapped["ShopifyStore"] = relationship(back_populates="blogs")
    articles: Mapped[list["ShopifyArticle"]] = relationship(
        back_populates="blog",
        cascade="all, delete-orphan",
    )


class ShopifyArticle(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "shopify_articles"
    __table_args__ = (
        UniqueConstraint(
            "shopify_store_id",
            "shopify_gid",
            name="uq_shopify_articles_store_gid",
        ),
    )

    shopify_store_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shopify_stores.id", ondelete="CASCADE"),
        index=True,
    )
    blog_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shopify_blogs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    shopify_gid: Mapped[str] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(500))
    handle: Mapped[str | None] = mapped_column(String(255), nullable=True)
    body_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    seo_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    seo_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    published_at_shopify: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    store: Mapped["ShopifyStore"] = relationship(back_populates="articles")
    blog: Mapped["ShopifyBlog | None"] = relationship(back_populates="articles")


class SeoAuditIssue(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "seo_audit_issues"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "shopify_store_id",
            "entity_type",
            "entity_id",
            "issue_type",
            name="uq_seo_audit_issues_dedup",
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
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    issue_type: Mapped[str] = mapped_column(String(100))
    severity: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text)
    recommendation: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="open")

    project: Mapped["Project"] = relationship()
    store: Mapped["ShopifyStore"] = relationship()


class ContentOpportunity(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "content_opportunities"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "shopify_store_id",
            "opportunity_type",
            "title",
            "target_entity_id",
            name="uq_content_opportunities_dedup",
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
    opportunity_type: Mapped[str] = mapped_column(String(50))
    priority: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text)
    target_entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    target_entity_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    suggested_keyword: Mapped[str | None] = mapped_column(String(255), nullable=True)
    search_intent: Mapped[str | None] = mapped_column(String(50), nullable=True)
    suggested_products: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, nullable=True)
    suggested_collections: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, nullable=True)
    reason: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="new")

    project: Mapped["Project"] = relationship()
    store: Mapped["ShopifyStore"] = relationship()


class ContentBrief(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "content_briefs"

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
    opportunity_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content_opportunities.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(500))
    primary_keyword: Mapped[str | None] = mapped_column(String(255), nullable=True)
    secondary_keywords: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    search_intent: Mapped[str | None] = mapped_column(String(50), nullable=True)
    outline: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    internal_links: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, nullable=True)
    products_to_feature: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, nullable=True)
    faq: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, nullable=True)
    cta: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="draft")

    project: Mapped["Project"] = relationship()
    store: Mapped["ShopifyStore"] = relationship()
    opportunity: Mapped["ContentOpportunity | None"] = relationship()
