"""Persistence for timeline event queries."""

import uuid
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any

from sqlalchemy import and_, func, select, true
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.timeline_event import TimelineEvent


class TimelineRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _conditions(
        self,
        *,
        participant_profile_id: uuid.UUID | None,
        project_id: uuid.UUID | None,
        force_executor_id: uuid.UUID | None,
        event_type: str | None,
        executor_id: uuid.UUID | None,
        occurred_from: datetime | None,
        occurred_to: datetime | None,
    ) -> list[Any]:
        conds: list[Any] = []
        if participant_profile_id is not None:
            conds.append(
                TimelineEvent.participant_profile_id == participant_profile_id,
            )
        if project_id is not None:
            conds.append(TimelineEvent.project_id == project_id)
        if force_executor_id is not None:
            conds.append(TimelineEvent.executor_id == force_executor_id)
        if event_type is not None and (et := event_type.strip()):
            conds.append(TimelineEvent.event_type == et)
        if executor_id is not None:
            conds.append(TimelineEvent.executor_id == executor_id)
        if occurred_from is not None:
            conds.append(TimelineEvent.occurred_at >= occurred_from)
        if occurred_to is not None:
            conds.append(TimelineEvent.occurred_at <= occurred_to)
        return conds

    async def count_filtered(
        self,
        *,
        participant_profile_id: uuid.UUID | None,
        project_id: uuid.UUID | None,
        force_executor_id: uuid.UUID | None,
        event_type: str | None,
        executor_id: uuid.UUID | None,
        occurred_from: datetime | None,
        occurred_to: datetime | None,
    ) -> int:
        conds = self._conditions(
            participant_profile_id=participant_profile_id,
            project_id=project_id,
            force_executor_id=force_executor_id,
            event_type=event_type,
            executor_id=executor_id,
            occurred_from=occurred_from,
            occurred_to=occurred_to,
        )
        where_clause = and_(*conds) if conds else true()
        stmt = select(func.count()).select_from(TimelineEvent).where(where_clause)
        result = await self._session.scalar(stmt)
        return int(result or 0)

    async def list_page_filtered(
        self,
        *,
        participant_profile_id: uuid.UUID | None,
        project_id: uuid.UUID | None,
        force_executor_id: uuid.UUID | None,
        event_type: str | None,
        executor_id: uuid.UUID | None,
        occurred_from: datetime | None,
        occurred_to: datetime | None,
        page: int,
        page_size: int,
    ) -> list[TimelineEvent]:
        conds = self._conditions(
            participant_profile_id=participant_profile_id,
            project_id=project_id,
            force_executor_id=force_executor_id,
            event_type=event_type,
            executor_id=executor_id,
            occurred_from=occurred_from,
            occurred_to=occurred_to,
        )
        offset = (page - 1) * page_size
        where_clause = and_(*conds) if conds else true()
        stmt = (
            select(TimelineEvent)
            .where(where_clause)
            .order_by(TimelineEvent.occurred_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_project(self, project_id: uuid.UUID) -> int:
        return await self.count_filtered(
            participant_profile_id=None,
            project_id=project_id,
            force_executor_id=None,
            event_type=None,
            executor_id=None,
            occurred_from=None,
            occurred_to=None,
        )

    async def iter_project_events_batches(
        self,
        project_id: uuid.UUID,
        *,
        batch_size: int,
    ) -> AsyncIterator[list[TimelineEvent]]:
        offset = 0
        while True:
            stmt = (
                select(TimelineEvent)
                .where(TimelineEvent.project_id == project_id)
                .order_by(
                    TimelineEvent.occurred_at.asc(),
                    TimelineEvent.id.asc(),
                )
                .offset(offset)
                .limit(batch_size)
            )
            result = await self._session.execute(stmt)
            rows = list(result.scalars().all())
            if not rows:
                break
            yield rows
            offset += len(rows)
            if len(rows) < batch_size:
                break
