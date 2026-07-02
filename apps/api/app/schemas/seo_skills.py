from typing import Literal

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
