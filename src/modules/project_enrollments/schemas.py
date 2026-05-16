"""Pydantic contracts for project enrollments API."""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from src.modules.auth.schemas import CamelModel


class EnrollmentCreateIn(CamelModel):
    user_id: UUID
    role: str = Field(min_length=1, max_length=64)
    group_id: UUID | None = None
    status: str | None = Field(default=None, min_length=1, max_length=32)
    enrolled_at: datetime | None = None


class EnrollmentPatchIn(CamelModel):
    group_id: UUID | None = None
    status: str | None = Field(default=None, min_length=1, max_length=32)
    enrolled_at: datetime | None = None
    exited_at: datetime | None = None


class EnrollmentDeleteIn(CamelModel):
    exit_reason: str = Field(min_length=1, max_length=2000)


class EnrollmentOut(CamelModel):
    id: str
    participant_profile_id: str = Field(serialization_alias="participantProfileId")
    user_id: str = Field(serialization_alias="userId")
    group_id: str | None = Field(default=None, serialization_alias="groupId")
    role: str
    status: str
    enrolled_at: str = Field(serialization_alias="enrolledAt")
    exited_at: str | None = Field(default=None, serialization_alias="exitedAt")
    exit_reason: str | None = Field(default=None, serialization_alias="exitReason")
    enrolled_by: str | None = Field(default=None, serialization_alias="enrolledBy")
    created_at: str = Field(serialization_alias="createdAt")
    updated_at: str = Field(serialization_alias="updatedAt")


class EnrollmentListResponse(CamelModel):
    enrollments: list[EnrollmentOut]
