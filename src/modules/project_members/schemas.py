"""Pydantic contracts for project members API."""

from datetime import date
from uuid import UUID

from pydantic import Field

from src.modules.auth.schemas import CamelModel


class ProjectMemberCreateIn(CamelModel):
    user_id: UUID
    role: str = Field(min_length=1, max_length=64)
    start_date: date
    end_date: date | None = None


class ProjectMemberPatchIn(CamelModel):
    role: str | None = Field(default=None, min_length=1, max_length=64)
    start_date: date | None = None
    end_date: date | None = None


class ProjectMemberOut(CamelModel):
    id: str
    user_id: str = Field(serialization_alias="userId")
    role: str
    start_date: str = Field(serialization_alias="startDate")
    end_date: str | None = Field(default=None, serialization_alias="endDate")
    created_at: str = Field(serialization_alias="createdAt")
    updated_at: str = Field(serialization_alias="updatedAt")


class ProjectMemberListResponse(CamelModel):
    members: list[ProjectMemberOut]
