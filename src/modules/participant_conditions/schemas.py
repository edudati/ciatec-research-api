"""Pydantic contracts for participant condition links."""

from datetime import date
from uuid import UUID

from src.modules.auth.schemas import CamelModel


class ParticipantConditionCreateIn(CamelModel):
    health_condition_id: UUID
    diagnosed_at: date | None = None
    resolved_at: date | None = None
    severity: str | None = None
    notes: str | None = None


class ParticipantConditionPatchIn(CamelModel):
    diagnosed_at: date | None = None
    resolved_at: date | None = None
    severity: str | None = None
    notes: str | None = None


class ParticipantConditionOut(CamelModel):
    id: str
    health_condition_id: str
    diagnosed_at: str | None = None
    resolved_at: str | None = None
    severity: str | None = None
    notes: str | None = None
    created_at: str
    updated_at: str


class ParticipantConditionListResponse(CamelModel):
    conditions: list[ParticipantConditionOut]
