"""Bulk persistence for Bubbles telemetry."""

from typing import Any

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.bubbles_telemetry import BubblesEvent, BubblesPose, BubblesWorld


class BubblesTelemetryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def bulk_insert_world(self, rows: list[dict[str, Any]]) -> int:
        if not rows:
            return 0
        stmt = pg_insert(BubblesWorld).values(rows)
        stmt = stmt.on_conflict_do_nothing(
            constraint="uq_bubbles_world_match_ts_device",
        )
        result = await self._session.execute(stmt)
        assert isinstance(result, CursorResult)
        return int(result.rowcount or 0)

    async def bulk_insert_pose(self, rows: list[dict[str, Any]]) -> int:
        if not rows:
            return 0
        stmt = pg_insert(BubblesPose).values(rows)
        stmt = stmt.on_conflict_do_nothing(
            constraint="uq_bubbles_pose_match_ts",
        )
        result = await self._session.execute(stmt)
        assert isinstance(result, CursorResult)
        return int(result.rowcount or 0)

    def add_events(self, events: list[BubblesEvent]) -> None:
        self._session.add_all(events)
