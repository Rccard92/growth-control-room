from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FaqEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    question: str = ""
    answer: str = ""


class SocialCommentInsight(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    insight: str = ""
    doubt: str = ""
    suggested_reply: str | None = Field(
        default=None, validation_alias="suggestedReply", serialization_alias="suggestedReply"
    )


class BrandFaqObjectionsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    project_id: UUID = Field(serialization_alias="projectId")
    general_faq: list[FaqEntry] | None = Field(default=None, serialization_alias="generalFaq")
    product_process_questions: list[FaqEntry] | None = Field(
        default=None, serialization_alias="productProcessQuestions"
    )
    purchase_shipping_questions: list[FaqEntry] | None = Field(
        default=None, serialization_alias="purchaseShippingQuestions"
    )
    objections: list[str] | None = None
    myths_misconceptions: list[str] | None = Field(
        default=None, serialization_alias="mythsMisconceptions"
    )
    recommended_answers: list[str] | None = Field(
        default=None, serialization_alias="recommendedAnswers"
    )
    content_opportunities: list[str] | None = Field(
        default=None, serialization_alias="contentOpportunities"
    )
    social_comment_insights: list[SocialCommentInsight] | None = Field(
        default=None, serialization_alias="socialCommentInsights"
    )
    notes: str | None = None
    last_import_source: str | None = Field(default=None, serialization_alias="lastImportSource")
    last_confidence: float | None = Field(default=None, serialization_alias="lastConfidence")
    warnings: list[str] | None = None
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class BrandFaqObjectionsUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    general_faq: list[FaqEntry] | None = Field(default=None, validation_alias="generalFaq")
    product_process_questions: list[FaqEntry] | None = Field(
        default=None, validation_alias="productProcessQuestions"
    )
    purchase_shipping_questions: list[FaqEntry] | None = Field(
        default=None, validation_alias="purchaseShippingQuestions"
    )
    objections: list[str] | None = None
    myths_misconceptions: list[str] | None = Field(
        default=None, validation_alias="mythsMisconceptions"
    )
    recommended_answers: list[str] | None = Field(
        default=None, validation_alias="recommendedAnswers"
    )
    content_opportunities: list[str] | None = Field(
        default=None, validation_alias="contentOpportunities"
    )
    social_comment_insights: list[SocialCommentInsight] | None = Field(
        default=None, validation_alias="socialCommentInsights"
    )
    notes: str | None = None


class BrandFaqObjectionsProposal(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    general_faq: list[FaqEntry] | None = Field(
        default=None, validation_alias="generalFaq", serialization_alias="generalFaq"
    )
    product_process_questions: list[FaqEntry] | None = Field(
        default=None,
        validation_alias="productProcessQuestions",
        serialization_alias="productProcessQuestions",
    )
    purchase_shipping_questions: list[FaqEntry] | None = Field(
        default=None,
        validation_alias="purchaseShippingQuestions",
        serialization_alias="purchaseShippingQuestions",
    )
    objections: list[str] | None = None
    myths_misconceptions: list[str] | None = Field(
        default=None, validation_alias="mythsMisconceptions", serialization_alias="mythsMisconceptions"
    )
    recommended_answers: list[str] | None = Field(
        default=None, validation_alias="recommendedAnswers", serialization_alias="recommendedAnswers"
    )
    content_opportunities: list[str] | None = Field(
        default=None,
        validation_alias="contentOpportunities",
        serialization_alias="contentOpportunities",
    )
    social_comment_insights: list[SocialCommentInsight] | None = Field(
        default=None,
        validation_alias="socialCommentInsights",
        serialization_alias="socialCommentInsights",
    )
    notes: str | None = None


class BrandFaqObjectionsImportResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    proposal: BrandFaqObjectionsProposal
    confidence: float = 0.0
    warnings: list[str] = Field(default_factory=list)
    source_summary: str = Field(default="", serialization_alias="sourceSummary")


class BrandFaqObjectionsApplyProposalRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    proposal: BrandFaqObjectionsProposal


class BrandFaqObjectionsApplyProposalResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    faq_objections: BrandFaqObjectionsRead = Field(serialization_alias="faqObjections")
    message: str = "FAQ & Objections aggiornati."


__all__ = [
    "FaqEntry",
    "SocialCommentInsight",
    "BrandFaqObjectionsRead",
    "BrandFaqObjectionsUpdate",
    "BrandFaqObjectionsProposal",
    "BrandFaqObjectionsImportResponse",
    "BrandFaqObjectionsApplyProposalRequest",
    "BrandFaqObjectionsApplyProposalResponse",
]
