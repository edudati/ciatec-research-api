"""Insert timeline_events row from job payload (idempotent by primary key)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.timeline_event import TimelineEvent
from src.modules.timeline.job_payload import TimelineEventJobPayload


def _parse_occurred_at(raw: str) -> datetime:
    dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


async def insert_timeline_event_from_payload(
    session: AsyncSession,
    payload: TimelineEventJobPayload,
) -> None:
    existing = await session.get(TimelineEvent, payload.id)
    if existing is not None:
        return
    row = TimelineEvent(
        id=payload.id,
        participant_profile_id=payload.participant_profile_id,
        project_id=payload.project_id,
        enrollment_id=payload.enrollment_id,
        executor_id=payload.executor_id,
        event_type=payload.event_type,
        source_type=payload.source_type,
        source_id=payload.source_id,
        occurred_at=_parse_occurred_at(payload.occurred_at),
        context=dict(payload.context),
    )
    session.add(row)
