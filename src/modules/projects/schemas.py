"""Pydantic contracts for projects API."""

from datetime import date
from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from src.core.enums import ProjectStatus
from src.modules.auth.schemas import CamelModel


class ProjectCreateIn(CamelModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    pi_user_id: UUID | None = None

    @field_validator("code")
    @classmethod
    def normalize_code(cls, v: str) -> str:
        return v.strip().upper()


class ProjectPatchIn(CamelModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    status: ProjectStatus | None = None
    start_date: date | None = None
    end_date: date | None = None
    metadata: dict[str, Any] | None = None


class ProjectOut(CamelModel):
    id: str
    code: str
    name: str
    description: str | None = None
    status: ProjectStatus
    start_date: str | None = Field(serialization_alias="startDate")
    end_date: str | None = Field(serialization_alias="endDate")
    metadata: dict[str, Any]
    created_at: str = Field(serialization_alias="createdAt")
    updated_at: str = Field(serialization_alias="updatedAt")


class ProjectListResponse(CamelModel):
    projects: list[ProjectOut]
    total: int
    page: int
    page_size: int
