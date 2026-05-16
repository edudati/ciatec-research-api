"""Pydantic contracts for intervention records (camelCase JSON)."""

from datetime import datetime
from typing import Any, Self
from uuid import UUID

from pydantic import Field, model_validator

from src.modules.auth.schemas import CamelModel


class InterventionRecordCreateIn(CamelModel):
    participant_profile_id: UUID
    template_id: UUID
    executor_id: UUID
    performed_at: datetime
    match_id: UUID | None = None
    duration_minutes: int | None = Field(default=None, ge=0)
    data: dict[str, Any] = Field(default_factory=dict)
    notes: str | None = None


class InterventionRecordPatchIn(CamelModel):
    performed_at: datetime | None = None
    duration_minutes: int | None = Field(default=None, ge=0)
    data: dict[str, Any] | None = None
    notes: str | None = None
    executor_id: UUID | None = None

    @model_validator(mode="after")
    def at_least_one_field(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("At least one field is required")
        return self


class InterventionRecordOut(CamelModel):
    id: str
    project_id: str
    participant_profile_id: str
    template_id: str
    executor_id: str
    match_id: str | None = None
    performed_at: str
    duration_minutes: int | None = None
    data: dict[str, Any]
    notes: str | None = None
    created_at: str
    updated_at: str


class InterventionRecordsListResponse(CamelModel):
    records: list[InterventionRecordOut]
