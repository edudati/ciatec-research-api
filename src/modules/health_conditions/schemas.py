"""Pydantic contracts for health conditions (camelCase JSON)."""

from typing import Self

from pydantic import Field, field_validator, model_validator

from src.modules.auth.schemas import CamelModel


class HealthConditionCreateIn(CamelModel):
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    category: str | None = Field(default=None, max_length=128)
    is_active: bool = Field(default=True)

    @field_validator("code")
    @classmethod
    def normalize_code(cls, v: str) -> str:
        return v.strip().upper()


class HealthConditionUpdateIn(CamelModel):
    code: str | None = Field(default=None, min_length=1, max_length=32)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    category: str | None = Field(default=None, max_length=128)
    is_active: bool | None = None

    @field_validator("code")
    @classmethod
    def normalize_code(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return v.strip().upper()

    @model_validator(mode="after")
    def at_least_one_field(self) -> Self:
        fields = (
            self.code,
            self.name,
            self.description,
            self.category,
            self.is_active,
        )
        if all(v is None for v in fields):
            raise ValueError("At least one field is required")
        return self


class HealthConditionOut(CamelModel):
    id: str
    code: str
    name: str
    description: str | None = None
    category: str | None = None
    is_active: bool = Field(serialization_alias="isActive")
    created_at: str = Field(serialization_alias="createdAt")
    updated_at: str = Field(serialization_alias="updatedAt")


class HealthConditionListResponse(CamelModel):
    conditions: list[HealthConditionOut]
    total: int
    page: int
    page_size: int


class HealthConditionListSortField:
    CREATED_AT = "createdAt"
    NAME = "name"
    CODE = "code"
    UPDATED_AT = "updatedAt"


def parse_health_condition_list_sort(raw: str) -> str:
    allowed = {
        HealthConditionListSortField.CREATED_AT,
        HealthConditionListSortField.NAME,
        HealthConditionListSortField.CODE,
        HealthConditionListSortField.UPDATED_AT,
    }
    if raw not in allowed:
        return HealthConditionListSortField.CREATED_AT
    return raw


def parse_order(raw: str) -> bool:
    """Returns True if descending."""
    return raw.strip().lower() != "asc"
