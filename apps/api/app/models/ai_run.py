import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import AiRunStatus

if TYPE_CHECKING:
    from app.models.project import Project


class AiRun(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "ai_runs"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    skill_name: Mapped[str] = mapped_column(String(100))
    status: Mapped[AiRunStatus] = mapped_column(default=AiRunStatus.PENDING)
    input_data: Mapped[dict[str, Any]] = mapped_column("input", JSONB, default=dict)
    output_data: Mapped[dict[str, Any]] = mapped_column("output", JSONB, default=dict)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    project: Mapped["Project"] = relationship(back_populates="ai_runs")
