import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin
from app.models.enums import AlertLevel, AlertStatus

if TYPE_CHECKING:
    from app.models.project import Project


class Alert(Base, UUIDPrimaryKeyMixin, CreatedAtMixin):
    __tablename__ = "alerts"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    level: Mapped[AlertLevel] = mapped_column(default=AlertLevel.INFO)
    title: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[AlertStatus] = mapped_column(default=AlertStatus.OPEN)

    project: Mapped["Project"] = relationship(back_populates="alerts")
