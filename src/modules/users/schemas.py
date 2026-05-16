"""Pydantic contracts for admin user APIs (camelCase JSON)."""

from typing import Self

from pydantic import EmailStr, Field, field_validator, model_validator

from src.core.enums import UserRole
from src.modules.auth.passwords import validate_password_strength
from src.modules.auth.schemas import CamelModel


class UserCreateIn(CamelModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = Field(min_length=1)
    role: UserRole

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        return validate_password_strength(v)


class UserUpdateIn(CamelModel):
    name: str | None = Field(default=None, min_length=1)
    role: UserRole | None = None
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8)
    is_first_access: bool | None = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return validate_password_strength(v)

    @model_validator(mode="after")
    def at_least_one_field(self) -> Self:
        fields = (self.name, self.role, self.email, self.password, self.is_first_access)
        if all(v is None for v in fields):
            raise ValueError("At least one field is required")
        return self


class UserListItemOut(CamelModel):
    id: str
    email: EmailStr
    name: str
    role: UserRole
    created_at: str = Field(serialization_alias="createdAt")
    email_verified: bool = Field(serialization_alias="emailVerified")
    is_first_access: bool = Field(serialization_alias="isFirstAccess")
    totp_enabled: bool = Field(default=False, serialization_alias="totpEnabled")
    updated_at: str = Field(serialization_alias="updatedAt")


class UserAdminOut(CamelModel):
    id: str
    email: EmailStr
    name: str
    role: UserRole
    created_at: str = Field(serialization_alias="createdAt")
    email_verified: bool = Field(serialization_alias="emailVerified")
    is_first_access: bool = Field(serialization_alias="isFirstAccess")
    totp_enabled: bool = Field(default=False, serialization_alias="totpEnabled")
    updated_at: str = Field(serialization_alias="updatedAt")
    deleted_at: str | None = Field(serialization_alias="deletedAt")


class UserListResponse(CamelModel):
    users: list[UserListItemOut]
    total: int
    page: int
    page_size: int


class UserListSortField:
    CREATED_AT = "createdAt"
    NAME = "name"
    EMAIL = "email"
    UPDATED_AT = "updatedAt"


def parse_user_list_sort(raw: str) -> str:
    allowed = {
        UserListSortField.CREATED_AT,
        UserListSortField.NAME,
        UserListSortField.EMAIL,
        UserListSortField.UPDATED_AT,
    }
    if raw not in allowed:
        return UserListSortField.CREATED_AT
    return raw


def parse_order(raw: str) -> bool:
    """Returns True if descending."""
    return raw.strip().lower() != "asc"
