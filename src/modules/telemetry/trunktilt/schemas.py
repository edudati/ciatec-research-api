"""Contracts for TrunkTilt telemetry (paths paridade api_antiga, JSON snake_case)."""

import uuid
from datetime import datetime
from typing import Annotated, Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

TRUNKTILT_GAME_SLUG = "trunktilt"


class WorldFrameIn(BaseModel):
    model_config = ConfigDict(extra="allow")

    frame_id: int = Field(ge=0)
    captured_at: datetime | None = None
    ball_x: float | None = None
    ball_y: float | None = None
    ball_z: float | None = None
    plane_tilt_x: float | None = None
    plane_tilt_y: float | None = None
    virtual_input_x: float | None = None
    virtual_input_y: float | None = None


class WorldBatchIn(BaseModel):
    frames: Annotated[list[WorldFrameIn], Field(min_length=1, max_length=200)]


class WorldBatchOut(BaseModel):
    match_id: uuid.UUID
    frames_received: int
    rows_inserted: int


class PoseLandmarkIn(BaseModel):
    model_config = ConfigDict(extra="allow")

    landmark_id: int = Field(
        ge=0,
        le=32,
        validation_alias=AliasChoices("landmark_id", "id"),
    )
    x: float | None = None
    y: float | None = None
    z: float | None = None
    visibility: float | None = None


class PoseFrameIn(BaseModel):
    model_config = ConfigDict(extra="allow")

    frame_id: int = Field(ge=0)
    captured_at: datetime | None = None
    landmarks: list[PoseLandmarkIn] = Field(min_length=1)


class PoseBatchIn(BaseModel):
    frames: Annotated[list[PoseFrameIn], Field(min_length=1, max_length=200)]


class PoseBatchOut(BaseModel):
    match_id: uuid.UUID
    frames_received: int
    rows_inserted: int


class TrunkTiltEventIn(BaseModel):
    model_config = ConfigDict(extra="allow")

    event_type: str = Field(
        min_length=1,
        max_length=128,
        validation_alias=AliasChoices("event_type", "type"),
    )
    captured_at: datetime | None = None


class EventsBatchIn(BaseModel):
    events: Annotated[list[TrunkTiltEventIn], Field(min_length=1, max_length=500)]


class EventsBatchOut(BaseModel):
    match_id: uuid.UUID
    events_received: int
    events_created: int


def world_frame_extras(frame: WorldFrameIn) -> dict[str, Any]:
    return dict(frame.model_extra or {})


def pose_landmark_extras(lm: PoseLandmarkIn) -> dict[str, Any]:
    return dict(lm.model_extra or {})


def event_payload(event: TrunkTiltEventIn) -> dict[str, Any]:
    data = event.model_dump(mode="json")
    data.pop("event_type", None)
    data.pop("captured_at", None)
    return data
