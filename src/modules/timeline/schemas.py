"""Pydantic contracts for timeline list APIs."""

from typing import Any

from src.modules.auth.schemas import CamelModel


class TimelineEventOut(CamelModel):
    id: str
    participant_profile_id: str
    project_id: str
    enrollment_id: str | None = None
    executor_id: str | None = None
    event_type: str
    source_type: str
    source_id: str
    occurred_at: str
    context: dict[str, Any]
    created_at: str


class TimelineListResponse(CamelModel):
    items: list[TimelineEventOut]
    total: int
    page: int
    page_size: int
