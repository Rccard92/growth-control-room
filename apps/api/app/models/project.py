import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.ai_run import AiRun
    from app.models.alert import Alert
    from app.models.content import ContentPlan
    from app.models.integration import Integration
    from app.models.workspace import Workspace


class Project(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "projects"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255))
    brand: Mapped[str] = mapped_column(String(255))

    workspace: Mapped["Workspace"] = relationship(back_populates="projects")
    integrations: Mapped[list["Integration"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    content_plans: Mapped[list["ContentPlan"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    ai_runs: Mapped[list["AiRun"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    alerts: Mapped[list["Alert"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
