"""Contracts for user progress bootstrap (F0-06), aligned with api_antiga.json."""

import uuid
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ProgressGameSummary(BaseModel):
    id: uuid.UUID
    name: str


class ProgressPresetSummaryOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None


class ProgressCurrentLevelOut(BaseModel):
    id: uuid.UUID
    name: str
    order: int
    config: dict[str, Any]
    unlocked: bool
    completed: bool
    is_current: bool
    bests: dict[str, Any]


class ProgressLevelTrailOut(BaseModel):
    """Trail row; extra JSON keys allowed (Node OpenAPI uses open objects)."""

    model_config = ConfigDict(extra="allow")

    id: uuid.UUID
    preset_id: uuid.UUID
    name: str
    order: int
    config: dict[str, Any] | None = None
    unlocked: bool
    completed: bool = False
    is_current: bool
    bests: dict[str, Any] = Field(default_factory=dict)


class ProgressStartOut(BaseModel):
    user_game_id: uuid.UUID
    game: ProgressGameSummary
    preset: ProgressPresetSummaryOut
    current_level: ProgressCurrentLevelOut
    levels: list[ProgressLevelTrailOut]


LevelsDetail = Literal["full", "summary"]
