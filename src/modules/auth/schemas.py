"""Pydantic contracts for auth (camelCase JSON per OpenAPI)."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from src.core.enums import UserRole
from src.modules.auth.passwords import validate_password_strength


def to_camel(s: str) -> str:
    parts = s.split("_")
    return parts[0] + "".join(p.title() for p in parts[1:])


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class UserPublic(CamelModel):
    id: str
    email: EmailStr
    name: str
    role: UserRole
    created_at: str = Field(serialization_alias="createdAt")
    email_verified: bool = Field(serialization_alias="emailVerified")
    is_first_access: bool = Field(serialization_alias="isFirstAccess")
    totp_enabled: bool = Field(default=False, serialization_alias="totpEnabled")


class RegisterIn(CamelModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = Field(min_length=1)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        return validate_password_strength(v)


class LoginIn(CamelModel):
    email: EmailStr
    password: str


class RefreshIn(CamelModel):
    refresh_token: str


class LogoutIn(CamelModel):
    refresh_token: str | None = None


class AuthTokens(CamelModel):
    access_token: str
    refresh_token: str


class RegisterResponse(CamelModel):
    user: UserPublic
    access_token: str
    refresh_token: str


class LoginResponse(CamelModel):
    user: UserPublic
    access_token: str
    refresh_token: str


class RefreshResponse(CamelModel):
    access_token: str
    refresh_token: str


class ChangePasswordIn(CamelModel):
    password: str = Field(min_length=8)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        return validate_password_strength(v)


class ChangePasswordResponse(CamelModel):
    user: UserPublic
