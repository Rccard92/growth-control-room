from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.brand_identity_visual import ModuleCompletionStatus


class BrandSafeClaimsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    project_id: UUID = Field(serialization_alias="projectId")
    allowed_claims: list[str] | None = Field(default=None, serialization_alias="allowedClaims")
    forbidden_claims: list[str] | None = Field(default=None, serialization_alias="forbiddenClaims")
    caution_claims: list[str] | None = Field(default=None, serialization_alias="cautionClaims")
    disclaimers: list[str] | None = None
    health_claim_rules: list[str] | None = Field(
        default=None, serialization_alias="healthClaimRules"
    )
    competitor_rules: list[str] | None = Field(
        default=None, serialization_alias="competitorRules"
    )
    process_secrets: list[str] | None = Field(default=None, serialization_alias="processSecrets")
    tone_red_flags: list[str] | None = Field(default=None, serialization_alias="toneRedFlags")
    notes: str | None = None
    last_import_source: str | None = Field(default=None, serialization_alias="lastImportSource")
    last_confidence: float | None = Field(default=None, serialization_alias="lastConfidence")
    warnings: list[str] | None = None
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class BrandSafeClaimsUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    allowed_claims: list[str] | None = Field(default=None, validation_alias="allowedClaims")
    forbidden_claims: list[str] | None = Field(default=None, validation_alias="forbiddenClaims")
    caution_claims: list[str] | None = Field(default=None, validation_alias="cautionClaims")
    disclaimers: list[str] | None = None
    health_claim_rules: list[str] | None = Field(default=None, validation_alias="healthClaimRules")
    competitor_rules: list[str] | None = Field(default=None, validation_alias="competitorRules")
    process_secrets: list[str] | None = Field(default=None, validation_alias="processSecrets")
    tone_red_flags: list[str] | None = Field(default=None, validation_alias="toneRedFlags")
    notes: str | None = None


class BrandSafeClaimsProposal(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    allowed_claims: list[str] | None = Field(
        default=None, validation_alias="allowedClaims", serialization_alias="allowedClaims"
    )
    forbidden_claims: list[str] | None = Field(
        default=None, validation_alias="forbiddenClaims", serialization_alias="forbiddenClaims"
    )
    caution_claims: list[str] | None = Field(
        default=None, validation_alias="cautionClaims", serialization_alias="cautionClaims"
    )
    disclaimers: list[str] | None = None
    health_claim_rules: list[str] | None = Field(
        default=None, validation_alias="healthClaimRules", serialization_alias="healthClaimRules"
    )
    competitor_rules: list[str] | None = Field(
        default=None, validation_alias="competitorRules", serialization_alias="competitorRules"
    )
    process_secrets: list[str] | None = Field(
        default=None, validation_alias="processSecrets", serialization_alias="processSecrets"
    )
    tone_red_flags: list[str] | None = Field(
        default=None, validation_alias="toneRedFlags", serialization_alias="toneRedFlags"
    )
    notes: str | None = None


class BrandSafeClaimsImportResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    proposal: BrandSafeClaimsProposal
    confidence: float = 0.0
    warnings: list[str] = Field(default_factory=list)
    source_summary: str = Field(default="", serialization_alias="sourceSummary")


class BrandSafeClaimsApplyProposalRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    proposal: BrandSafeClaimsProposal


class BrandSafeClaimsApplyProposalResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    safe_claims: BrandSafeClaimsRead = Field(serialization_alias="safeClaims")
    message: str = "Safe Claims aggiornati."


__all__ = [
    "BrandSafeClaimsRead",
    "BrandSafeClaimsUpdate",
    "BrandSafeClaimsProposal",
    "BrandSafeClaimsImportResponse",
    "BrandSafeClaimsApplyProposalRequest",
    "BrandSafeClaimsApplyProposalResponse",
    "ModuleCompletionStatus",
]
