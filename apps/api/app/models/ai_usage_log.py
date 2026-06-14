import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.project import Project


class AiUsageLog(Base, UUIDPrimaryKeyMixin, CreatedAtMixin):
    __tablename__ = "ai_usage_logs"

    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False, default="openai")
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    module: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    operation: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    job_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cached_input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reasoning_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estimated_input_cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 6), nullable=True)
    estimated_output_cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 6), nullable=True)
    estimated_cached_cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 6), nullable=True)
    estimated_total_cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 6), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    prompt_chars: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_chars: Mapped[int | None] = mapped_column(Integer, nullable=True)
    prompt_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    prompt_preview: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_preview: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt_cache_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    context_profile: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    context_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    context_chars: Mapped[int | None] = mapped_column(Integer, nullable=True)
    context_blocks_used: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    model_tier: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    model_policy_source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    requested_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    max_output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    temperature: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), nullable=True)
    reasoning_effort: Mapped[str | None] = mapped_column(String(32), nullable=True)
    operation_key: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    response_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    project: Mapped["Project | None"] = relationship(back_populates="ai_usage_logs")
