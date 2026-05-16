"""Pydantic contracts for catalog APIs (snake_case JSON, OpenAPI parity)."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class GameCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    slug: str | None = Field(default=None, max_length=64)
    description: str | None = None
    is_active: bool = True


class GameUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    slug: str | None = Field(default=None, max_length=64)
    description: str | None = None
    is_active: bool | None = None


class GameOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str | None
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class GameAdminOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str | None
    description: str | None
    is_active: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime


class GamesListResponse(BaseModel):
    games: list[GameOut]


class GamesAdminListResponse(BaseModel):
    games: list[GameAdminOut]


class PresetCreate(BaseModel):
    game_id: uuid.UUID
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    is_default: bool = False
    is_active: bool = True


class PresetUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    is_default: bool | None = None
    is_active: bool | None = None


class PresetOut(BaseModel):
    id: uuid.UUID
    game_id: uuid.UUID
    name: str
    description: str | None
    is_default: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PresetAdminOut(BaseModel):
    id: uuid.UUID
    game_id: uuid.UUID
    name: str
    description: str | None
    is_default: bool
    is_active: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime


class PresetsListResponse(BaseModel):
    presets: list[PresetOut]


class PresetsAdminListResponse(BaseModel):
    presets: list[PresetAdminOut]


class LevelCreate(BaseModel):
    preset_id: uuid.UUID
    name: str = Field(min_length=1, max_length=255)
    order: int = Field(ge=0)
    config: dict[str, Any]
    is_active: bool = True


class LevelUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    order: int | None = Field(default=None, ge=0)
    config: dict[str, Any] | None = None
    is_active: bool | None = None


class LevelOut(BaseModel):
    id: uuid.UUID
    preset_id: uuid.UUID
    name: str
    order: int
    config: dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class LevelAdminOut(BaseModel):
    id: uuid.UUID
    preset_id: uuid.UUID
    name: str
    order: int
    config: dict[str, Any]
    is_active: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime


class LevelsListResponse(BaseModel):
    levels: list[LevelOut]


class LevelsAdminListResponse(BaseModel):
    levels: list[LevelAdminOut]
