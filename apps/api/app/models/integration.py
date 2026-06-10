import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import IntegrationStatus

if TYPE_CHECKING:
    from app.models.integration_credential import IntegrationCredential
    from app.models.project import Project


class Integration(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "integrations"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "provider",
            name="uq_integrations_project_id_provider",
        ),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(50))
    status: Mapped[IntegrationStatus] = mapped_column(
        default=IntegrationStatus.NOT_CONNECTED,
    )
    connected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    project: Mapped["Project"] = relationship(back_populates="integrations")
    credential: Mapped["IntegrationCredential | None"] = relationship(
        back_populates="integration",
        cascade="all, delete-orphan",
        uselist=False,
    )
