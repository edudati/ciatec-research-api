"""Pydantic contracts for participant profile APIs (camelCase JSON)."""

from datetime import date
from typing import Self
from uuid import UUID

from pydantic import Field, model_validator

from src.core.enums import BiologicalSex
from src.modules.auth.schemas import CamelModel


class ParticipantCreateIn(CamelModel):
    user_id: UUID
    birth_date: date | None = None
    biological_sex: BiologicalSex | None = None
    phone: str | None = Field(default=None, max_length=64)
    notes: str | None = None


class ParticipantUpdateIn(CamelModel):
    birth_date: date | None = None
    biological_sex: BiologicalSex | None = None
    phone: str | None = Field(default=None, max_length=64)
    notes: str | None = None

    @model_validator(mode="after")
    def at_least_one_field(self) -> Self:
        fields = (
            self.birth_date,
            self.biological_sex,
            self.phone,
            self.notes,
        )
        if all(v is None for v in fields):
            raise ValueError("At least one field is required")
        return self


class ParticipantOut(CamelModel):
    id: str
    user_id: str = Field(serialization_alias="userId")
    birth_date: str | None = Field(serialization_alias="birthDate")
    biological_sex: BiologicalSex | None = Field(serialization_alias="biologicalSex")
    phone: str | None = None
    notes: str | None = None
    created_at: str = Field(serialization_alias="createdAt")
    updated_at: str = Field(serialization_alias="updatedAt")


class ParticipantListResponse(CamelModel):
    participants: list[ParticipantOut]
    total: int
    page: int
    page_size: int


class ParticipantListSortField:
    CREATED_AT = "createdAt"
    UPDATED_AT = "updatedAt"


def parse_participant_list_sort(raw: str) -> str:
    allowed = {
        ParticipantListSortField.CREATED_AT,
        ParticipantListSortField.UPDATED_AT,
    }
    if raw not in allowed:
        return ParticipantListSortField.CREATED_AT
    return raw


def parse_order(raw: str) -> bool:
    """Returns True if descending."""
    return raw.strip().lower() != "asc"
