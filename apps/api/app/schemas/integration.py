from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class IntegrationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID | None = None
    project_id: UUID = Field(serialization_alias="projectId")
    provider: str
    status: str
    connected_at: datetime | None = Field(
        default=None,
        serialization_alias="connectedAt",
    )

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value: object) -> str:
        if hasattr(value, "value"):
            return str(value.value)
        return str(value)
