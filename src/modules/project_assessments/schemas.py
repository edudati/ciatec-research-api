"""Pydantic contracts for assessment records (camelCase JSON)."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Self
from uuid import UUID

from pydantic import Field, model_validator

from src.modules.auth.schemas import CamelModel


class AssessmentRecordCreateIn(CamelModel):
    participant_profile_id: UUID
    template_id: UUID
    executor_id: UUID
    performed_at: datetime
    score: Decimal | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    notes: str | None = None


class AssessmentRecordPatchIn(CamelModel):
    performed_at: datetime | None = None
    score: Decimal | None = None
    data: dict[str, Any] | None = None
    notes: str | None = None
    executor_id: UUID | None = None

    @model_validator(mode="after")
    def at_least_one_field(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("At least one field is required")
        return self


class AssessmentRecordOut(CamelModel):
    id: str
    project_id: str = Field(serialization_alias="projectId")
    participant_profile_id: str = Field(serialization_alias="participantProfileId")
    template_id: str = Field(serialization_alias="templateId")
    executor_id: str = Field(serialization_alias="executorId")
    performed_at: str = Field(serialization_alias="performedAt")
    score: str | None = None
    data: dict[str, Any]
    notes: str | None = None
    created_at: str = Field(serialization_alias="createdAt")
    updated_at: str = Field(serialization_alias="updatedAt")


class AssessmentRecordsListResponse(CamelModel):
    records: list[AssessmentRecordOut]
