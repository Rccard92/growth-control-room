import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin
from app.models.enums import AiRunStatus

if TYPE_CHECKING:
    from app.models.project import Project


class AiRun(Base, UUIDPrimaryKeyMixin, CreatedAtMixin):
    __tablename__ = "ai_runs"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    run_type: Mapped[str] = mapped_column(String(100))
    status: Mapped[AiRunStatus] = mapped_column(default=AiRunStatus.PENDING)
    input_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    output_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="ai_runs")
