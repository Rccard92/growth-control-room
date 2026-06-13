import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
if TYPE_CHECKING:
    from app.models.ai_run import AiRun
    from app.models.alert import Alert
    from app.models.brand_intelligence import (
        BrandAiGuardrail,
        BrandAsset,
        BrandAudienceInsight,
        BrandClaimRule,
        BrandContentPillar,
        BrandExtractedFact,
        BrandExternalSource,
        BrandImportBatch,
        BrandProductKnowledge,
        BrandProfile,
        BrandSectionDraft,
        BrandSeoStrategy,
        BrandSourceDocument,
        BrandVoice,
    )
    from app.models.integration import Integration
    from app.models.shopify import ShopifyStore
    from app.models.workspace import Workspace


class Project(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "projects"
    __table_args__ = (
        UniqueConstraint("workspace_id", "slug", name="uq_projects_workspace_id_slug"),
    )

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")

    workspace: Mapped["Workspace"] = relationship(back_populates="projects")
    integrations: Mapped[list["Integration"]] = relationship(
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
    shopify_stores: Mapped[list["ShopifyStore"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    brand_profile: Mapped["BrandProfile | None"] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        uselist=False,
    )
    brand_voice: Mapped["BrandVoice | None"] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        uselist=False,
    )
    brand_product_knowledge: Mapped[list["BrandProductKnowledge"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    brand_audience_insights: Mapped[list["BrandAudienceInsight"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    brand_claim_rules: Mapped[list["BrandClaimRule"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    brand_seo_strategy: Mapped["BrandSeoStrategy | None"] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        uselist=False,
    )
    brand_content_pillars: Mapped[list["BrandContentPillar"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    brand_ai_guardrails: Mapped[list["BrandAiGuardrail"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    brand_assets: Mapped[list["BrandAsset"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    brand_source_documents: Mapped[list["BrandSourceDocument"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    brand_extracted_facts: Mapped[list["BrandExtractedFact"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    brand_import_batches: Mapped[list["BrandImportBatch"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    brand_section_drafts: Mapped[list["BrandSectionDraft"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    brand_external_sources: Mapped[list["BrandExternalSource"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
