import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.project import Project


class SeoSkillRun(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "seo_skill_runs"
    __table_args__ = (
        Index("ix_seo_skill_runs_target_type_target_id", "target_type", "target_id"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    target_type: Mapped[str] = mapped_column(String(50))
    target_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="pending", index=True)
    provider: Mapped[str] = mapped_column(String(30), default="claude")
    selected_skills: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)
    current_skill: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    project: Mapped["Project"] = relationship()
    results: Mapped[list["SeoSkillRunResult"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
    )


class SeoSkillRunResult(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "seo_skill_run_results"

    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("seo_skill_runs.id", ondelete="CASCADE"),
        index=True,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    skill_key: Mapped[str] = mapped_column(String(100), index=True)
    status: Mapped[str] = mapped_column(String(30), default="pending", index=True)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    findings: Mapped[Any | None] = mapped_column(JSONB, nullable=True)
    recommendations: Mapped[Any | None] = mapped_column(JSONB, nullable=True)
    tasks: Mapped[Any | None] = mapped_column(JSONB, nullable=True)
    artifacts: Mapped[Any | None] = mapped_column(JSONB, nullable=True)
    raw_output: Mapped[Any | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    run: Mapped["SeoSkillRun"] = relationship(back_populates="results")
