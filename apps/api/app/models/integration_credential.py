import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.integration import Integration


class IntegrationCredential(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "integration_credentials"

    integration_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("integrations.id", ondelete="CASCADE"),
        unique=True,
    )
    encrypted_payload: Mapped[str | None] = mapped_column(Text, nullable=True)

    integration: Mapped["Integration"] = relationship(back_populates="credential")
