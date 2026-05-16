"""Contracts for match preset, level read, and finish."""

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PresetLevelSummaryOut(BaseModel):
    id: uuid.UUID
    preset_id: uuid.UUID
    name: str
    order: int


class PresetWithLevelsOut(BaseModel):
    id: uuid.UUID
    game_id: uuid.UUID
    name: str
    description: str | None
    is_default: bool
    levels: list[PresetLevelSummaryOut]


class MatchPresetOut(BaseModel):
    user_game_id: uuid.UUID
    game_id: uuid.UUID
    preset: PresetWithLevelsOut
    current_level_id: uuid.UUID


class MatchLevelOut(BaseModel):
    id: uuid.UUID
    preset_id: uuid.UUID
    name: str
    order: int
    config: dict[str, Any]


class ClientMetaIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    app_version: str | None = Field(default=None, max_length=128)
    unity_version: str | None = Field(default=None, max_length=64)
    platform: str | None = Field(default=None, max_length=64)
    device_model: str | None = Field(default=None, max_length=128)
    locale: str | None = Field(default=None, max_length=32)


class MatchFinishBody(BaseModel):
    score: int = Field(ge=0)
    duration_ms: int = Field(ge=1)
    completed: bool
    client_request_id: str | None = Field(default=None, max_length=128)
    client_meta: ClientMetaIn | None = None
    extra: dict[str, Any] | None = None


class MatchFinishOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    match_id: uuid.UUID
    score: int
    duration_ms: int
    server_duration_ms: int
    completed: bool
    extra: dict[str, Any]
    created_at: datetime


@dataclass(frozen=True)
class MatchFinishResponse:
    """HTTP envelope for finish (201 first write, 200 idempotent replay)."""

    body: MatchFinishOut
    status_code: int


def build_result_detail_payload(
    extra: dict[str, Any] | None,
    client_meta: ClientMetaIn | None,
) -> dict[str, Any]:
    data: dict[str, Any] = {**(extra or {})}
    if client_meta is not None:
        meta = client_meta.model_dump(exclude_none=True)
        if meta:
            data["client_meta"] = meta
        elif "client_meta" in data:
            del data["client_meta"]
    return data


def normalize_idempotency_key(
    header_value: str | None,
    body: MatchFinishBody,
) -> str | None:
    h = header_value.strip() if header_value else None
    b = body.client_request_id.strip() if body.client_request_id else None
    if h and b and h != b:
        raise ValueError(
            "Idempotency-Key and client_request_id must match when both are set"
        )
    return h or b
