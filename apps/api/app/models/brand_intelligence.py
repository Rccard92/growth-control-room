import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.project import Project


class BrandProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "brand_profiles"
    __table_args__ = (UniqueConstraint("project_id", name="uq_brand_profiles_project_id"),)

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    brand_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    website_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(255), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    short_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    story: Mapped[str | None] = mapped_column(Text, nullable=True)
    mission: Mapped[str | None] = mapped_column(Text, nullable=True)
    values: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    differentiators: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    instagram_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    facebook_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    tiktok_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    youtube_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    trustpilot_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    google_business_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    other_sources: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, nullable=True)
    origin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    production_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    tone_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    customer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_status: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, nullable=True)
    last_enriched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    enrichment_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    enrichment_warnings: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="brand_profile")


class BrandIdentity(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "brand_identities"
    __table_args__ = (UniqueConstraint("project_id", name="uq_brand_identities_project_id"),)

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    positioning: Mapped[str | None] = mapped_column(Text, nullable=True)
    brand_values: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    differentiators: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    production_principles: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    quality_principles: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    trust_elements: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    what_brand_is: Mapped[str | None] = mapped_column(Text, nullable=True)
    what_brand_is_not: Mapped[str | None] = mapped_column(Text, nullable=True)
    storytelling_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="brand_identity")


class BrandVisualIdentity(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "brand_visual_identities"
    __table_args__ = (
        UniqueConstraint("project_id", name="uq_brand_visual_identities_project_id"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    primary_logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    secondary_logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    favicon_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    primary_color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    secondary_color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    accent_color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    background_color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    text_color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    color_palette: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, nullable=True)
    fonts: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, nullable=True)
    visual_style_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_style_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    do_show: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    do_not_show: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    website_extracted_palette: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSONB, nullable=True
    )

    project: Mapped["Project"] = relationship(back_populates="brand_visual_identity")


class BrandVoice(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "brand_voices"
    __table_args__ = (UniqueConstraint("project_id", name="uq_brand_voices_project_id"),)

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    tone: Mapped[str | None] = mapped_column(String(255), nullable=True)
    style_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    formality_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    emoji_policy: Mapped[str | None] = mapped_column(String(100), nullable=True)
    words_to_use: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    words_to_avoid: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    examples_good: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    examples_bad: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="brand_voice")


class BrandProductKnowledge(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "brand_product_knowledge"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    name: Mapped[str] = mapped_column(String(500))
    entity_type: Mapped[str] = mapped_column(String(50), default="product")
    shopify_gid: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    ingredients: Mapped[str | None] = mapped_column(Text, nullable=True)
    origin: Mapped[str | None] = mapped_column(String(255), nullable=True)
    production_process: Mapped[str | None] = mapped_column(Text, nullable=True)
    usage_suggestions: Mapped[str | None] = mapped_column(Text, nullable=True)
    conservation: Mapped[str | None] = mapped_column(Text, nullable=True)
    taste_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    objections: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    faq: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, nullable=True)
    claims_allowed: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    claims_forbidden: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    related_products: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    priority: Mapped[str] = mapped_column(String(20), default="medium")

    project: Mapped["Project"] = relationship(back_populates="brand_product_knowledge")


class BrandAudienceInsight(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "brand_audience_insights"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    segment_name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    motivations: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    pain_points: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    objections: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    questions: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    buying_triggers: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="brand_audience_insights")


class BrandClaimRule(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "brand_claim_rules"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    rule_type: Mapped[str] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    examples: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    severity: Mapped[str] = mapped_column(String(20), default="info")

    project: Mapped["Project"] = relationship(back_populates="brand_claim_rules")


class BrandSeoStrategy(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "brand_seo_strategies"
    __table_args__ = (UniqueConstraint("project_id", name="uq_brand_seo_strategies_project_id"),)

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    primary_keywords: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    secondary_keywords: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    keyword_clusters: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, nullable=True)
    priority_pages: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    internal_linking_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta_title_pattern: Mapped[str | None] = mapped_column(String(500), nullable=True)
    meta_description_pattern: Mapped[str | None] = mapped_column(String(500), nullable=True)
    url_handle_pattern: Mapped[str | None] = mapped_column(String(500), nullable=True)
    competitors: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="brand_seo_strategy")


class BrandContentPillar(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "brand_content_pillars"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    objective: Mapped[str | None] = mapped_column(Text, nullable=True)
    products: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    channels: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    example_topics: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    cta_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="brand_content_pillars")


class BrandAiGuardrail(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "brand_ai_guardrails"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    rule_type: Mapped[str] = mapped_column(String(50))
    applies_to: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="brand_ai_guardrails")


class BrandAsset(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "brand_assets"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    asset_type: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(255))
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="brand_assets")


class BrandImportBatch(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "brand_import_batches"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_type: Mapped[str] = mapped_column(String(50), default="file_upload")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)
    current_step: Mapped[str | None] = mapped_column(String(500), nullable=True)
    total_files: Mapped[int] = mapped_column(Integer, default=0)
    processed_files: Mapped[int] = mapped_column(Integer, default=0)
    total_facts: Mapped[int] = mapped_column(Integer, default=0)
    approved_facts: Mapped[int] = mapped_column(Integer, default=0)
    rejected_facts: Mapped[int] = mapped_column(Integer, default=0)
    needs_review_facts: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    warnings: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    declared_brand_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    declared_website_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project: Mapped["Project"] = relationship(back_populates="brand_import_batches")
    documents: Mapped[list["BrandSourceDocument"]] = relationship(
        back_populates="batch",
        cascade="all, delete-orphan",
    )
    extracted_facts: Mapped[list["BrandExtractedFact"]] = relationship(
        back_populates="batch",
        cascade="all, delete-orphan",
    )
    section_drafts: Mapped[list["BrandSectionDraft"]] = relationship(
        back_populates="batch",
        cascade="all, delete-orphan",
    )
    external_sources: Mapped[list["BrandExternalSource"]] = relationship(
        back_populates="batch",
        cascade="all, delete-orphan",
    )
    intelligence_briefs: Mapped[list["BrandIntelligenceBrief"]] = relationship(
        back_populates="source_batch",
        cascade="all, delete-orphan",
    )


class BrandIntelligenceBrief(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "brand_intelligence_briefs"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    source_batch_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brand_import_batches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(50), default="draft", index=True)
    title: Mapped[str] = mapped_column(String(255))
    brief_payload: Mapped[Any] = mapped_column(JSONB, nullable=False, default=dict)
    markdown_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    warnings: Mapped[Any | None] = mapped_column(JSONB, nullable=True)
    source_document_ids: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    source_external_ids: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    source_fact_ids: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project: Mapped["Project"] = relationship(back_populates="brand_intelligence_briefs")
    source_batch: Mapped["BrandImportBatch | None"] = relationship(
        back_populates="intelligence_briefs",
    )


class BrandExternalSource(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "brand_external_sources"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    batch_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brand_import_batches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_type: Mapped[str] = mapped_column(String(50))
    label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    url: Mapped[str] = mapped_column(String(2000))
    status: Mapped[str] = mapped_column(String(50), default="pending")
    fetched_title: Mapped[str | None] = mapped_column(Text, nullable=True)
    fetched_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    fetched_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    fetch_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project: Mapped["Project"] = relationship(back_populates="brand_external_sources")
    batch: Mapped["BrandImportBatch | None"] = relationship(back_populates="external_sources")
    extracted_facts: Mapped[list["BrandExtractedFact"]] = relationship(
        back_populates="source_external",
    )


class BrandSectionDraft(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "brand_section_drafts"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    batch_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brand_import_batches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    section_key: Mapped[str] = mapped_column(String(50), index=True)
    title: Mapped[str] = mapped_column(String(255))
    draft_payload: Mapped[Any] = mapped_column(JSONB, nullable=False, default=dict)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_fact_ids: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    source_document_ids: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    source_external_ids: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="draft", index=True)
    ai_reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    warnings: Mapped[Any | None] = mapped_column(JSONB, nullable=True)
    previous_official_snapshot: Mapped[Any | None] = mapped_column(JSONB, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project: Mapped["Project"] = relationship(back_populates="brand_section_drafts")
    batch: Mapped["BrandImportBatch | None"] = relationship(back_populates="section_drafts")


class BrandSourceDocument(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "brand_source_documents"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    batch_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brand_import_batches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    filename: Mapped[str] = mapped_column(String(500))
    content_type: Mapped[str] = mapped_column(String(255))
    file_size: Mapped[int] = mapped_column(Integer)
    storage_mode: Mapped[str] = mapped_column(String(50), default="text_only")
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    document_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    document_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    extraction_status: Mapped[str] = mapped_column(String(50), default="uploaded")
    extraction_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    processing_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)
    current_step: Mapped[str | None] = mapped_column(String(500), nullable=True)
    extracted_facts_count: Mapped[int] = mapped_column(Integer, default=0)
    needs_review_count: Mapped[int] = mapped_column(Integer, default=0)
    approved_count: Mapped[int] = mapped_column(Integer, default=0)
    rejected_count: Mapped[int] = mapped_column(Integer, default=0)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project: Mapped["Project"] = relationship(back_populates="brand_source_documents")
    batch: Mapped["BrandImportBatch | None"] = relationship(back_populates="documents")
    extracted_facts: Mapped[list["BrandExtractedFact"]] = relationship(
        back_populates="source_document",
        cascade="all, delete-orphan",
    )


class BrandExtractedFact(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "brand_extracted_facts"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    source_document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brand_source_documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_external_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brand_external_sources.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    batch_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brand_import_batches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    target_section: Mapped[str] = mapped_column(String(100))
    target_entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    field_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    extracted_value: Mapped[Any] = mapped_column(JSONB, nullable=True)
    source_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(50), default="suggested")
    ai_reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_update_suggestion: Mapped[bool] = mapped_column(default=False, server_default="false")
    existing_target_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    update_mode: Mapped[str] = mapped_column(String(50), default="create")
    previous_value: Mapped[Any | None] = mapped_column(JSONB, nullable=True)
    conflict_status: Mapped[str] = mapped_column(String(50), default="none")
    source_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    import_round: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project: Mapped["Project"] = relationship(back_populates="brand_extracted_facts")
    batch: Mapped["BrandImportBatch | None"] = relationship(back_populates="extracted_facts")
    source_document: Mapped["BrandSourceDocument | None"] = relationship(
        back_populates="extracted_facts",
    )
    source_external: Mapped["BrandExternalSource | None"] = relationship(
        back_populates="extracted_facts",
    )
