"""Bulk persistence for TrunkTilt telemetry."""

from typing import Any

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.trunktilt_telemetry import TrunkTiltEvent, TrunkTiltPose, TrunkTiltWorld


class TrunkTiltTelemetryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def bulk_insert_world(self, rows: list[dict[str, Any]]) -> int:
        if not rows:
            return 0
        stmt = pg_insert(TrunkTiltWorld).values(rows)
        stmt = stmt.on_conflict_do_nothing(
            constraint="uq_trunktilt_world_match_frame",
        )
        result = await self._session.execute(stmt)
        assert isinstance(result, CursorResult)
        return int(result.rowcount or 0)

    async def bulk_insert_pose(self, rows: list[dict[str, Any]]) -> int:
        if not rows:
            return 0
        stmt = pg_insert(TrunkTiltPose).values(rows)
        stmt = stmt.on_conflict_do_nothing(
            constraint="uq_trunktilt_pose_match_frame_landmark",
        )
        result = await self._session.execute(stmt)
        assert isinstance(result, CursorResult)
        return int(result.rowcount or 0)

    def add_events(self, events: list[TrunkTiltEvent]) -> None:
        self._session.add_all(events)
