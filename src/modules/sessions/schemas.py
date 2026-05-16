"""Contracts for session and match creation endpoints."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    started_at: datetime
    enrollment_id: uuid.UUID | None = None


class CurrentSessionResponse(BaseModel):
    session: SessionOut | None


class CreateMatchBody(BaseModel):
    game_id: uuid.UUID
    level_id: uuid.UUID
    enrollment_id: uuid.UUID | None = None


class MatchCreatedOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    game_id: uuid.UUID
    level_id: uuid.UUID
    level_config_snapshot: dict[str, Any]
    started_at: datetime
