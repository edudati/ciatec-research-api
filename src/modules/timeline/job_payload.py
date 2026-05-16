"""Serializable payload for timeline event persistence (API or arq worker)."""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TimelineEventJobPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: uuid.UUID
    participant_profile_id: uuid.UUID
    project_id: uuid.UUID
    enrollment_id: uuid.UUID | None = None
    executor_id: uuid.UUID | None = None
    event_type: str
    source_type: str
    source_id: str
    occurred_at: str = Field(description="ISO-8601 datetime")
    context: dict[str, Any] = Field(default_factory=dict)
