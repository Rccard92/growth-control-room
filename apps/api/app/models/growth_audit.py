import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.project import Project


class GrowthAuditRun(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "growth_audit_runs"
    __table_args__ = (
        Index("ix_growth_audit_runs_project_id_status", "project_id", "status"),
        Index("ix_growth_audit_runs_project_id_created_at", "project_id", "created_at"),
        Index("ix_growth_audit_runs_normalized_domain", "normalized_domain"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    root_url: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_domain: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="pending", index=True)
    phase: Mapped[str | None] = mapped_column(String(60), nullable=True)
    audit_mode: Mapped[str] = mapped_column(String(50), default="full_site_mvp")
    provider: Mapped[str] = mapped_column(String(30), default="openai")
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)
    pages_discovered: Mapped[int] = mapped_column(Integer, default=0)
    pages_classified: Mapped[int] = mapped_column(Integer, default=0)
    pages_analyzed: Mapped[int] = mapped_column(Integer, default=0)
    pages_failed: Mapped[int] = mapped_column(Integer, default=0)
    total_pages: Mapped[int | None] = mapped_column(Integer, nullable=True)
    current_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    config: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    summary: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    site_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    seo_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    geo_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cro_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    performance_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
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
    pages: Mapped[list["GrowthAuditPage"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
    )
    findings: Mapped[list["GrowthAuditFinding"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
    )
    tasks: Mapped[list["GrowthAuditTask"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
    )
    events: Mapped[list["GrowthAuditEvent"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
    )


class GrowthAuditPage(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "growth_audit_pages"
    __table_args__ = (
        Index("ix_growth_audit_pages_run_id_page_type", "run_id", "page_type"),
        Index("ix_growth_audit_pages_project_id_normalized_url", "project_id", "normalized_url"),
        Index("ix_growth_audit_pages_run_id_status", "run_id", "status"),
        Index("ix_growth_audit_pages_run_id_score", "run_id", "score"),
    )

    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("growth_audit_runs.id", ondelete="CASCADE"),
        index=True,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    url: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_url: Mapped[str] = mapped_column(Text, nullable=False)
    path: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_type: Mapped[str] = mapped_column(String(50), default="unknown", index=True)
    source: Mapped[str] = mapped_column(String(50), default="seed")
    status: Mapped[str] = mapped_column(String(40), default="pending", index=True)
    priority: Mapped[str] = mapped_column(String(30), default="normal")
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    canonical_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    h1: Mapped[str | None] = mapped_column(Text, nullable=True)
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    depth: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    seo_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    geo_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cro_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    performance_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    discovered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    classified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    analyzed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
    )

    run: Mapped["GrowthAuditRun"] = relationship(back_populates="pages")
    project: Mapped["Project"] = relationship()
    results: Mapped[list["GrowthAuditPageResult"]] = relationship(
        back_populates="page",
        cascade="all, delete-orphan",
    )
    findings: Mapped[list["GrowthAuditFinding"]] = relationship(back_populates="page")
    tasks: Mapped[list["GrowthAuditTask"]] = relationship(back_populates="page")


class GrowthAuditPageResult(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "growth_audit_page_results"
    __table_args__ = (
        Index("ix_growth_audit_page_results_run_id_page_id", "run_id", "page_id"),
        Index("ix_growth_audit_page_results_page_id_result_type", "page_id", "result_type"),
        Index("ix_growth_audit_page_results_skill_key", "skill_key"),
    )

    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("growth_audit_runs.id", ondelete="CASCADE"),
        index=True,
    )
    page_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("growth_audit_pages.id", ondelete="CASCADE"),
        index=True,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    result_type: Mapped[str] = mapped_column(String(50), nullable=False)
    skill_key: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="pending")
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    findings: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)
    recommendations: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)
    tasks: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)
    artifacts: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    raw_output: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    run: Mapped["GrowthAuditRun"] = relationship()
    page: Mapped["GrowthAuditPage"] = relationship(back_populates="results")
    project: Mapped["Project"] = relationship()


class GrowthAuditFinding(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "growth_audit_findings"
    __table_args__ = (
        Index("ix_growth_audit_findings_run_id_severity", "run_id", "severity"),
        Index("ix_growth_audit_findings_page_id_severity", "page_id", "severity"),
        Index("ix_growth_audit_findings_project_id_status", "project_id", "status"),
    )

    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("growth_audit_runs.id", ondelete="CASCADE"),
        index=True,
    )
    page_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("growth_audit_pages.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    source_result_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("growth_audit_page_results.id", ondelete="SET NULL"),
        nullable=True,
    )
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(30), default="medium")
    priority: Mapped[str] = mapped_column(String(30), default="medium")
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    how_to_validate: Mapped[str | None] = mapped_column(Text, nullable=True)
    impact: Mapped[str | None] = mapped_column(String(30), nullable=True)
    effort: Mapped[str | None] = mapped_column(String(30), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="open")
    finding_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
    )

    run: Mapped["GrowthAuditRun"] = relationship(back_populates="findings")
    page: Mapped["GrowthAuditPage | None"] = relationship(back_populates="findings")
    project: Mapped["Project"] = relationship()


class GrowthAuditTask(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "growth_audit_tasks"
    __table_args__ = (
        Index("ix_growth_audit_tasks_run_id_status", "run_id", "status"),
        Index("ix_growth_audit_tasks_page_id_status", "page_id", "status"),
        Index("ix_growth_audit_tasks_project_id_priority", "project_id", "priority"),
    )

    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("growth_audit_runs.id", ondelete="CASCADE"),
        index=True,
    )
    page_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("growth_audit_pages.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    finding_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("growth_audit_findings.id", ondelete="SET NULL"),
        nullable=True,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner_type: Mapped[str] = mapped_column(String(30), default="seo")
    priority: Mapped[str] = mapped_column(String(30), default="medium")
    estimated_effort: Mapped[str] = mapped_column(String(30), default="medium")
    status: Mapped[str] = mapped_column(String(30), default="open")
    task_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    run: Mapped["GrowthAuditRun"] = relationship(back_populates="tasks")
    page: Mapped["GrowthAuditPage | None"] = relationship(back_populates="tasks")
    project: Mapped["Project"] = relationship()


class GrowthAuditEvent(Base, UUIDPrimaryKeyMixin, CreatedAtMixin):
    __tablename__ = "growth_audit_events"
    __table_args__ = (
        Index("ix_growth_audit_events_run_id_created_at", "run_id", "created_at"),
        Index("ix_growth_audit_events_project_id_created_at", "project_id", "created_at"),
    )

    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("growth_audit_runs.id", ondelete="CASCADE"),
        index=True,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    phase: Mapped[str | None] = mapped_column(String(60), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    progress_percent: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    run: Mapped["GrowthAuditRun"] = relationship(back_populates="events")
    project: Mapped["Project"] = relationship()
