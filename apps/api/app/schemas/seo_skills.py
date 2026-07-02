from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SeoSkillCatalogItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    key: str
    label: str
    description: str
    category: str
    source: str = "claude-seo"
    upstream_command: str = Field(alias="upstreamCommand")
    status: Literal["available", "needs_config", "external_required", "planned"]
    default_provider: str = Field(default="claude", alias="defaultProvider")
    requires: list[str] = Field(default_factory=list)
    optional_integrations: list[str] = Field(
        default_factory=list, alias="optionalIntegrations"
    )
    required_integrations: list[str] = Field(
        default_factory=list, alias="requiredIntegrations"
    )
    output_schema: str = Field(alias="outputSchema")
    runtime: Literal[
        "prompt_only", "connector_required", "external_api_required", "planned"
    ]
    risk_level: Literal["low", "medium", "high"] = Field(alias="riskLevel")
    enabled: bool = True


class SeoSkillCatalogCounts(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    total: int
    available: int
    needs_config: int = Field(alias="needsConfig")
    external_required: int = Field(alias="externalRequired")
    planned: int


class SeoSkillCatalogResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    skills: list[SeoSkillCatalogItem]
    counts: SeoSkillCatalogCounts


class SeoSkillRunCreateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    target_type: str = Field(alias="targetType")
    target_id: UUID | None = Field(default=None, alias="targetId")
    url: str | None = None
    selected_skills: list[str] = Field(alias="selectedSkills")
    provider: str = "claude"


class SeoSkillRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    project_id: UUID = Field(serialization_alias="projectId")
    target_type: str = Field(serialization_alias="targetType")
    target_id: UUID | None = Field(default=None, serialization_alias="targetId")
    url: str | None = None
    status: str
    provider: str
    selected_skills: list[str] = Field(serialization_alias="selectedSkills")
    progress_percent: int = Field(serialization_alias="progressPercent")
    current_skill: str | None = Field(default=None, serialization_alias="currentSkill")
    error_message: str | None = Field(default=None, serialization_alias="errorMessage")
    started_at: datetime | None = Field(default=None, serialization_alias="startedAt")
    completed_at: datetime | None = Field(default=None, serialization_alias="completedAt")
    created_at: datetime | None = Field(default=None, serialization_alias="createdAt")
    updated_at: datetime | None = Field(default=None, serialization_alias="updatedAt")


class SeoSkillRunResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    run_id: UUID = Field(serialization_alias="runId")
    project_id: UUID = Field(serialization_alias="projectId")
    skill_key: str = Field(serialization_alias="skillKey")
    status: str
    score: int | None = None
    findings: Any | None = None
    recommendations: Any | None = None
    tasks: Any | None = None
    artifacts: Any | None = None
    raw_output: Any | None = Field(default=None, serialization_alias="rawOutput")
    error_message: str | None = Field(default=None, serialization_alias="errorMessage")
    started_at: datetime | None = Field(default=None, serialization_alias="startedAt")
    completed_at: datetime | None = Field(default=None, serialization_alias="completedAt")
    created_at: datetime | None = Field(default=None, serialization_alias="createdAt")
    updated_at: datetime | None = Field(default=None, serialization_alias="updatedAt")


class SeoSkillRunDetailResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    run: SeoSkillRunRead
    results: list[SeoSkillRunResultRead]


class SeoSkillRunStartResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    run: SeoSkillRunRead
