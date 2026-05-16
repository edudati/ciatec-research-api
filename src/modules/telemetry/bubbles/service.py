"""Bubbles telemetry ingest (match ownership, game slug, finished guard)."""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from src.models.bubbles_telemetry import BubblesEvent
from src.modules.catalog.repository import CatalogRepository
from src.modules.matches.repository import MatchRepository
from src.modules.sessions.repository import SessionRepository
from src.modules.telemetry.bubbles.repository import BubblesTelemetryRepository
from src.modules.telemetry.bubbles.schemas import (
    BUBBLES_GAME_SLUG,
    EventsBatchIn,
    EventsBatchOut,
    PoseBatchIn,
    PoseBatchOut,
    PoseFrameIn,
    WorldBatchIn,
    WorldBatchOut,
    WorldFrameIn,
)


class BubblesTelemetryService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._sessions = SessionRepository(session)
        self._matches = MatchRepository(session)
        self._catalog = CatalogRepository(session)
        self._telemetry = BubblesTelemetryRepository(session)

    async def _load_match_for_telemetry(
        self, user_id: uuid.UUID, match_id: uuid.UUID
    ) -> uuid.UUID:
        match = await self._sessions.get_match_owned_by_user(match_id, user_id)
        if match is None:
            raise NotFoundError("Match not found", code="MATCH_NOT_FOUND")

        result = await self._matches.get_match_result_by_match_id(match_id)
        if result is not None:
            raise ConflictError("Match already finished", code="MATCH_ALREADY_FINISHED")

        bubbles = await self._catalog.get_game_by_slug(BUBBLES_GAME_SLUG)
        if bubbles is None or not bubbles.is_active:
            raise NotFoundError(
                "Bubbles game is not configured",
                code="BUBBLES_GAME_NOT_CONFIGURED",
            )
        if match.game_id != bubbles.id:
            raise ForbiddenError("Not a Bubbles match", code="NOT_BUBBLES_MATCH")

        return match_id

    async def ingest_world(
        self, user_id: uuid.UUID, match_id: uuid.UUID, body: WorldBatchIn
    ) -> WorldBatchOut:
        mid = await self._load_match_for_telemetry(user_id, match_id)

        by_frame: dict[tuple[int, str], WorldFrameIn] = {}
        for frame in body.frames:
            key = (frame.timestamp, frame.device)
            by_frame[key] = frame

        rows: list[dict[str, Any]] = []
        for frame in by_frame.values():
            rows.append(
                {
                    "id": uuid.uuid4(),
                    "match_id": mid,
                    "timestamp_ms": frame.timestamp,
                    "device": frame.device,
                    "data": frame.data,
                },
            )

        inserted = await self._telemetry.bulk_insert_world(rows)
        await self._session.commit()

        return WorldBatchOut(
            match_id=mid,
            frames_received=len(by_frame),
            frames_created=inserted,
        )

    async def ingest_pose(
        self, user_id: uuid.UUID, match_id: uuid.UUID, body: PoseBatchIn
    ) -> PoseBatchOut:
        mid = await self._load_match_for_telemetry(user_id, match_id)

        by_ts: dict[int, PoseFrameIn] = {}
        for frame in body.frames:
            by_ts[frame.timestamp] = frame

        rows: list[dict[str, Any]] = []
        for frame in by_ts.values():
            rows.append(
                {
                    "id": uuid.uuid4(),
                    "match_id": mid,
                    "timestamp_ms": frame.timestamp,
                    "data": frame.data,
                },
            )

        inserted = await self._telemetry.bulk_insert_pose(rows)
        await self._session.commit()

        return PoseBatchOut(
            match_id=mid,
            frames_received=len(by_ts),
            frames_created=inserted,
        )

    async def ingest_events(
        self, user_id: uuid.UUID, match_id: uuid.UUID, body: EventsBatchIn
    ) -> EventsBatchOut:
        mid = await self._load_match_for_telemetry(user_id, match_id)

        events: list[BubblesEvent] = []
        for ev in body.events:
            events.append(
                BubblesEvent(
                    id=uuid.uuid4(),
                    match_id=mid,
                    event_type=ev.event_type,
                    timestamp_ms=ev.timestamp,
                    payload=ev.data,
                ),
            )
        self._telemetry.add_events(events)
        await self._session.commit()

        return EventsBatchOut(
            match_id=mid,
            events_received=len(body.events),
            events_created=len(events),
        )
