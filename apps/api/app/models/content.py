import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import BlogDraftStatus, ContentPlanStatus

if TYPE_CHECKING:
    from app.models.project import Project


class ContentPlan(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "content_plans"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255))
    status: Mapped[ContentPlanStatus] = mapped_column(default=ContentPlanStatus.DRAFT)
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)

    project: Mapped["Project"] = relationship(back_populates="content_plans")
    blog_drafts: Mapped[list["BlogDraft"]] = relationship(
        back_populates="content_plan",
        cascade="all, delete-orphan",
    )


class BlogDraft(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "blog_drafts"

    content_plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content_plans.id", ondelete="CASCADE"),
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[BlogDraftStatus] = mapped_column(default=BlogDraftStatus.DRAFT)
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    content_plan: Mapped["ContentPlan"] = relationship(back_populates="blog_drafts")
