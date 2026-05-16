"""Contracts for Bubbles telemetry (JSON payloads, limits per F0-08 / api_antiga)."""

import uuid
from typing import Annotated, Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

BUBBLES_GAME_SLUG = "bubbles"


class WorldFrameIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timestamp: int = Field(ge=0)
    device: str = Field(min_length=1, max_length=256)
    data: dict[str, Any]


class WorldBatchIn(BaseModel):
    frames: Annotated[list[WorldFrameIn], Field(min_length=1, max_length=100)]


class WorldBatchOut(BaseModel):
    match_id: uuid.UUID
    frames_received: int
    frames_created: int


class PoseFrameIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timestamp: int = Field(ge=0)
    data: dict[str, Any]


class PoseBatchIn(BaseModel):
    frames: Annotated[list[PoseFrameIn], Field(min_length=1, max_length=100)]


class PoseBatchOut(BaseModel):
    match_id: uuid.UUID
    frames_received: int
    frames_created: int


class BubblesEventIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_type: str = Field(
        min_length=1,
        max_length=128,
        validation_alias=AliasChoices("type", "event_type"),
    )
    timestamp: int = Field(ge=0)
    data: dict[str, Any]


class EventsBatchIn(BaseModel):
    events: Annotated[list[BubblesEventIn], Field(min_length=1, max_length=500)]


class EventsBatchOut(BaseModel):
    match_id: uuid.UUID
    events_received: int
    events_created: int
