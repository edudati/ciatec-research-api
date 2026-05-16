"""Pydantic contracts for assessment templates (camelCase JSON)."""

from typing import Any, Self

from pydantic import AliasChoices, Field, field_validator, model_validator

from src.modules.auth.schemas import CamelModel


class AssessmentTemplateCreateIn(CamelModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    template_type: str = Field(
        min_length=1,
        max_length=64,
        validation_alias=AliasChoices("type", "templateType"),
        serialization_alias="type",
    )
    version: str = Field(default="1", min_length=1, max_length=32)
    is_active: bool = Field(default=True)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("code")
    @classmethod
    def normalize_code(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("template_type")
    @classmethod
    def normalize_type(cls, v: str) -> str:
        return v.strip().upper()


class AssessmentTemplateUpdateIn(CamelModel):
    code: str | None = Field(default=None, min_length=1, max_length=64)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    template_type: str | None = Field(
        default=None,
        min_length=1,
        max_length=64,
        validation_alias=AliasChoices("type", "templateType"),
        serialization_alias="type",
    )
    version: str | None = Field(default=None, min_length=1, max_length=32)
    is_active: bool | None = None
    metadata: dict[str, Any] | None = None

    @field_validator("code")
    @classmethod
    def normalize_code(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return v.strip().upper()

    @field_validator("template_type")
    @classmethod
    def normalize_type(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return v.strip().upper()

    @model_validator(mode="after")
    def at_least_one_field(self) -> Self:
        fields = (
            self.code,
            self.name,
            self.description,
            self.template_type,
            self.version,
            self.is_active,
            self.metadata,
        )
        if all(v is None for v in fields):
            raise ValueError("At least one field is required")
        return self


class AssessmentTemplateOut(CamelModel):
    id: str
    code: str
    name: str
    description: str | None = None
    template_type: str = Field(
        validation_alias=AliasChoices("type", "templateType"),
        serialization_alias="type",
    )
    version: str
    is_active: bool = Field(serialization_alias="isActive")
    metadata: dict[str, Any]
    created_at: str = Field(serialization_alias="createdAt")
    updated_at: str = Field(serialization_alias="updatedAt")


class AssessmentTemplatesListResponse(CamelModel):
    assessments: list[AssessmentTemplateOut]
    total: int
    page: int
    page_size: int = Field(serialization_alias="pageSize")


class AssessmentTemplateListSortField:
    CREATED_AT = "createdAt"
    NAME = "name"
    CODE = "code"
    UPDATED_AT = "updatedAt"


def parse_assessment_template_list_sort(raw: str) -> str:
    allowed = {
        AssessmentTemplateListSortField.CREATED_AT,
        AssessmentTemplateListSortField.NAME,
        AssessmentTemplateListSortField.CODE,
        AssessmentTemplateListSortField.UPDATED_AT,
    }
    if raw not in allowed:
        return AssessmentTemplateListSortField.CREATED_AT
    return raw


def parse_order(raw: str) -> bool:
    """Returns True if descending."""
    return raw.strip().lower() != "asc"
