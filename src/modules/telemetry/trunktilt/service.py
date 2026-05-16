"""TrunkTilt telemetry ingest (match ownership, game slug, finished guard)."""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from src.models.trunktilt_telemetry import TrunkTiltEvent
from src.modules.catalog.repository import CatalogRepository
from src.modules.matches.repository import MatchRepository
from src.modules.sessions.repository import SessionRepository
from src.modules.telemetry.trunktilt.repository import TrunkTiltTelemetryRepository
from src.modules.telemetry.trunktilt.schemas import (
    TRUNKTILT_GAME_SLUG,
    EventsBatchIn,
    EventsBatchOut,
    PoseBatchIn,
    PoseBatchOut,
    WorldBatchIn,
    WorldBatchOut,
    event_payload,
    pose_landmark_extras,
    world_frame_extras,
)


class TrunkTiltTelemetryService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._sessions = SessionRepository(session)
        self._matches = MatchRepository(session)
        self._catalog = CatalogRepository(session)
        self._telemetry = TrunkTiltTelemetryRepository(session)

    async def _load_match_for_telemetry(
        self, user_id: uuid.UUID, match_id: uuid.UUID
    ) -> uuid.UUID:
        match = await self._sessions.get_match_owned_by_user(match_id, user_id)
        if match is None:
            raise NotFoundError("Match not found", code="MATCH_NOT_FOUND")

        result = await self._matches.get_match_result_by_match_id(match_id)
        if result is not None:
            raise ConflictError("Match already finished", code="MATCH_ALREADY_FINISHED")

        trunk = await self._catalog.get_game_by_slug(TRUNKTILT_GAME_SLUG)
        if trunk is None or not trunk.is_active:
            raise NotFoundError(
                "TrunkTilt game is not configured",
                code="TRUNKTILT_GAME_NOT_CONFIGURED",
            )
        if match.game_id != trunk.id:
            raise ForbiddenError("Not a TrunkTilt match", code="NOT_TRUNKTILT_MATCH")

        return match_id

    async def ingest_world(
        self, user_id: uuid.UUID, match_id: uuid.UUID, body: WorldBatchIn
    ) -> WorldBatchOut:
        mid = await self._load_match_for_telemetry(user_id, match_id)

        by_frame: dict[int, Any] = {}
        for frame in body.frames:
            by_frame[frame.frame_id] = frame

        rows: list[dict[str, Any]] = []
        for frame in by_frame.values():
            rows.append(
                {
                    "id": uuid.uuid4(),
                    "match_id": mid,
                    "frame_id": frame.frame_id,
                    "captured_at": frame.captured_at,
                    "ball_x": frame.ball_x,
                    "ball_y": frame.ball_y,
                    "ball_z": frame.ball_z,
                    "plane_tilt_x": frame.plane_tilt_x,
                    "plane_tilt_y": frame.plane_tilt_y,
                    "virtual_input_x": frame.virtual_input_x,
                    "virtual_input_y": frame.virtual_input_y,
                    "extras": world_frame_extras(frame),
                },
            )

        inserted = await self._telemetry.bulk_insert_world(rows)
        await self._session.commit()

        return WorldBatchOut(
            match_id=mid,
            frames_received=len(by_frame),
            rows_inserted=inserted,
        )

    async def ingest_pose(
        self, user_id: uuid.UUID, match_id: uuid.UUID, body: PoseBatchIn
    ) -> PoseBatchOut:
        mid = await self._load_match_for_telemetry(user_id, match_id)

        by_key: dict[tuple[int, int], dict[str, Any]] = {}
        frames_seen: dict[int, Any] = {}
        for frame in body.frames:
            frames_seen[frame.frame_id] = frame
            for lm in frame.landmarks:
                by_key[(frame.frame_id, lm.landmark_id)] = {
                    "frame": frame,
                    "landmark": lm,
                }

        rows: list[dict[str, Any]] = []
        for pair in by_key.values():
            frame = pair["frame"]
            lm = pair["landmark"]
            rows.append(
                {
                    "id": uuid.uuid4(),
                    "match_id": mid,
                    "frame_id": frame.frame_id,
                    "landmark_id": lm.landmark_id,
                    "captured_at": frame.captured_at,
                    "visibility": lm.visibility,
                    "x": lm.x,
                    "y": lm.y,
                    "z": lm.z,
                    "extras": pose_landmark_extras(lm),
                },
            )

        inserted = await self._telemetry.bulk_insert_pose(rows)
        await self._session.commit()

        return PoseBatchOut(
            match_id=mid,
            frames_received=len(frames_seen),
            rows_inserted=inserted,
        )

    async def ingest_events(
        self, user_id: uuid.UUID, match_id: uuid.UUID, body: EventsBatchIn
    ) -> EventsBatchOut:
        mid = await self._load_match_for_telemetry(user_id, match_id)

        events: list[TrunkTiltEvent] = []
        for ev in body.events:
            events.append(
                TrunkTiltEvent(
                    id=uuid.uuid4(),
                    match_id=mid,
                    event_type=ev.event_type,
                    captured_at=ev.captured_at,
                    payload=event_payload(ev),
                ),
            )
        self._telemetry.add_events(events)
        await self._session.commit()

        return EventsBatchOut(
            match_id=mid,
            events_received=len(body.events),
            events_created=len(events),
        )
