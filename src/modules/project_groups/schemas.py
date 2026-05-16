"""Pydantic contracts for project groups API."""

from pydantic import Field, field_validator

from src.modules.auth.schemas import CamelModel


class GroupCreateIn(CamelModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    is_active: bool = True

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        return v.strip()


class GroupPatchIn(CamelModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    is_active: bool | None = None

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return v.strip()


class GroupOut(CamelModel):
    id: str
    name: str
    description: str | None = None
    is_active: bool = Field(serialization_alias="isActive")
    created_at: str = Field(serialization_alias="createdAt")
    updated_at: str = Field(serialization_alias="updatedAt")


class GroupListResponse(CamelModel):
    groups: list[GroupOut]
