"""Pydantic contracts for questionnaire templates and question items."""

from typing import Any, Self

from pydantic import AliasChoices, Field, field_validator, model_validator

from src.modules.auth.schemas import CamelModel


class QuestionnaireTemplateCreateIn(CamelModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    self_report: bool = Field(default=False)
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


class QuestionnaireTemplateUpdateIn(CamelModel):
    code: str | None = Field(default=None, min_length=1, max_length=64)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    self_report: bool | None = None
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
            self.self_report,
            self.template_type,
            self.version,
            self.is_active,
            self.metadata,
        )
        if all(v is None for v in fields):
            raise ValueError("At least one field is required")
        return self


class QuestionnaireTemplateOut(CamelModel):
    id: str
    code: str
    name: str
    description: str | None = None
    self_report: bool = Field(serialization_alias="selfReport")
    template_type: str = Field(
        validation_alias=AliasChoices("type", "templateType"),
        serialization_alias="type",
    )
    version: str
    is_active: bool = Field(serialization_alias="isActive")
    metadata: dict[str, Any]
    created_at: str = Field(serialization_alias="createdAt")
    updated_at: str = Field(serialization_alias="updatedAt")


class QuestionnaireTemplatesListResponse(CamelModel):
    questionnaires: list[QuestionnaireTemplateOut]
    total: int
    page: int
    page_size: int = Field(serialization_alias="pageSize")


class QuestionnaireTemplateListSortField:
    CREATED_AT = "createdAt"
    NAME = "name"
    CODE = "code"
    UPDATED_AT = "updatedAt"


def parse_questionnaire_template_list_sort(raw: str) -> str:
    allowed = {
        QuestionnaireTemplateListSortField.CREATED_AT,
        QuestionnaireTemplateListSortField.NAME,
        QuestionnaireTemplateListSortField.CODE,
        QuestionnaireTemplateListSortField.UPDATED_AT,
    }
    if raw not in allowed:
        return QuestionnaireTemplateListSortField.CREATED_AT
    return raw


class QuestionItemCreateIn(CamelModel):
    code: str = Field(min_length=1, max_length=64)
    label: str = Field(min_length=1, max_length=512)
    item_type: str = Field(
        min_length=1,
        max_length=64,
        validation_alias=AliasChoices("type", "itemType"),
        serialization_alias="type",
    )
    display_order: int = Field(
        ge=0,
        validation_alias=AliasChoices("order", "displayOrder"),
        serialization_alias="order",
    )
    options: dict[str, Any] | None = None
    is_required: bool = Field(default=True)

    @field_validator("code")
    @classmethod
    def normalize_code(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("item_type")
    @classmethod
    def normalize_item_type(cls, v: str) -> str:
        return v.strip().upper()


class QuestionItemUpdateIn(CamelModel):
    code: str | None = Field(default=None, min_length=1, max_length=64)
    label: str | None = Field(default=None, min_length=1, max_length=512)
    item_type: str | None = Field(
        default=None,
        min_length=1,
        max_length=64,
        validation_alias=AliasChoices("type", "itemType"),
        serialization_alias="type",
    )
    display_order: int | None = Field(
        default=None,
        ge=0,
        validation_alias=AliasChoices("order", "displayOrder"),
        serialization_alias="order",
    )
    options: dict[str, Any] | None = None
    is_required: bool | None = None

    @field_validator("code")
    @classmethod
    def normalize_code(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return v.strip().upper()

    @field_validator("item_type")
    @classmethod
    def normalize_item_type(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return v.strip().upper()

    @model_validator(mode="after")
    def at_least_one_field(self) -> Self:
        fields = (
            self.code,
            self.label,
            self.item_type,
            self.display_order,
            self.options,
            self.is_required,
        )
        if all(v is None for v in fields):
            raise ValueError("At least one field is required")
        return self


class QuestionItemOut(CamelModel):
    id: str
    questionnaire_template_id: str = Field(
        serialization_alias="questionnaireTemplateId",
    )
    code: str
    label: str
    item_type: str = Field(
        validation_alias=AliasChoices("type", "itemType"),
        serialization_alias="type",
    )
    display_order: int = Field(
        validation_alias=AliasChoices("order", "displayOrder"),
        serialization_alias="order",
    )
    options: dict[str, Any] | None = None
    is_required: bool = Field(serialization_alias="isRequired")
    created_at: str = Field(serialization_alias="createdAt")
    updated_at: str = Field(serialization_alias="updatedAt")


class QuestionItemsListResponse(CamelModel):
    items: list[QuestionItemOut]
