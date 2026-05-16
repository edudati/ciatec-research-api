"""Pydantic contracts for intervention templates (camelCase JSON)."""

from typing import Any, Self
from uuid import UUID

from pydantic import AliasChoices, Field, field_validator, model_validator

from src.modules.auth.schemas import CamelModel


class InterventionTemplateCreateIn(CamelModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    intervention_type: str = Field(
        min_length=1,
        max_length=64,
        validation_alias=AliasChoices("type", "interventionType"),
        serialization_alias="type",
    )
    game_id: UUID | None = Field(default=None, validation_alias=AliasChoices("gameId"))
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("code")
    @classmethod
    def normalize_code(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("intervention_type")
    @classmethod
    def normalize_type(cls, v: str) -> str:
        return v.strip().upper()


class InterventionTemplateUpdateIn(CamelModel):
    code: str | None = Field(default=None, min_length=1, max_length=64)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    intervention_type: str | None = Field(
        default=None,
        min_length=1,
        max_length=64,
        validation_alias=AliasChoices("type", "interventionType"),
        serialization_alias="type",
    )
    game_id: UUID | None = Field(
        default=None,
        validation_alias=AliasChoices("gameId"),
    )
    metadata: dict[str, Any] | None = None

    @field_validator("code")
    @classmethod
    def normalize_code(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return v.strip().upper()

    @field_validator("intervention_type")
    @classmethod
    def normalize_type(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return v.strip().upper()

    @model_validator(mode="after")
    def at_least_one_field(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("At least one field is required")
        return self


class InterventionTemplateOut(CamelModel):
    id: str
    code: str
    name: str
    intervention_type: str = Field(
        validation_alias=AliasChoices("type", "interventionType"),
        serialization_alias="type",
    )
    game_id: str | None = Field(default=None, serialization_alias="gameId")
    metadata: dict[str, Any]
    created_at: str = Field(serialization_alias="createdAt")
    updated_at: str = Field(serialization_alias="updatedAt")


class InterventionTemplatesListResponse(CamelModel):
    interventions: list[InterventionTemplateOut]
    total: int
    page: int
    page_size: int = Field(serialization_alias="pageSize")


class InterventionTemplateListSortField:
    CREATED_AT = "createdAt"
    NAME = "name"
    CODE = "code"
    UPDATED_AT = "updatedAt"


def parse_intervention_template_list_sort(raw: str) -> str:
    allowed = {
        InterventionTemplateListSortField.CREATED_AT,
        InterventionTemplateListSortField.NAME,
        InterventionTemplateListSortField.CODE,
        InterventionTemplateListSortField.UPDATED_AT,
    }
    if raw not in allowed:
        return InterventionTemplateListSortField.CREATED_AT
    return raw


__all__ = [
    "InterventionTemplateCreateIn",
    "InterventionTemplateListSortField",
    "InterventionTemplateOut",
    "InterventionTemplatesListResponse",
    "InterventionTemplateUpdateIn",
    "parse_intervention_template_list_sort",
]
