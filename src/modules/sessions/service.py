"""Business logic for daily sessions and creating matches."""

import copy
import uuid
from datetime import UTC, date, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnprocessableEntityError,
)
from src.models.participant_enrollment import ParticipantEnrollment
from src.models.session_match import GameSession, Match
from src.modules.catalog.repository import CatalogRepository
from src.modules.catalog.service import CatalogService
from src.modules.matches.repository import MatchRepository
from src.modules.matches.service import MatchesService
from src.modules.project_enrollments.repository import ProjectEnrollmentsRepository
from src.modules.sessions.repository import SessionRepository
from src.modules.sessions.schemas import (
    CreateMatchBody,
    CurrentSessionResponse,
    MatchCreatedOut,
    SessionOut,
)


def _utc_today() -> date:
    return datetime.now(UTC).date()


class SessionsService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._sessions = SessionRepository(session)
        self._matches = MatchRepository(session)
        self._catalog = CatalogRepository(session)
        self._enrollments = ProjectEnrollmentsRepository(session)

    def _to_session_out(self, row: GameSession) -> SessionOut:
        return SessionOut.model_validate(row)

    async def start(self, user_id: uuid.UUID) -> tuple[SessionOut, bool]:
        today = _utc_today()
        existing = await self._sessions.get_active_session_for_day(user_id, today)
        if existing is not None:
            return self._to_session_out(existing), False

        sid = uuid.uuid4()
        row = GameSession(id=sid, user_id=user_id, session_date=today)
        self._sessions.add(row)
        try:
            await self._session.flush()
        except IntegrityError:
            await self._session.rollback()
            again = await self._sessions.get_active_session_for_day(user_id, today)
            if again is None:
                raise ConflictError(
                    "Could not resolve daily session after concurrent start",
                    code="SESSION_RACE",
                ) from None
            return self._to_session_out(again), False

        await self._session.commit()
        return self._to_session_out(row), True

    async def current(self, user_id: uuid.UUID) -> CurrentSessionResponse:
        today = _utc_today()
        row = await self._sessions.get_active_session_for_day(user_id, today)
        if row is None:
            return CurrentSessionResponse(session=None)
        return CurrentSessionResponse(session=self._to_session_out(row))

    async def _require_enrollment_for_match(
        self,
        enrollment_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> ParticipantEnrollment:
        row = await self._enrollments.get_by_id(enrollment_id)
        if row is None:
            raise NotFoundError("Enrollment not found", code="NOT_FOUND")
        prof = row.participant_profile
        if prof.deleted_at is not None:
            raise NotFoundError("Enrollment not found", code="NOT_FOUND")
        if prof.user_id != user_id:
            raise ForbiddenError(
                "Enrollment does not belong to this user",
                code="FORBIDDEN",
            )
        if row.status != "ACTIVE" or row.exited_at is not None:
            raise UnprocessableEntityError(
                "Enrollment is not active",
                code="ENROLLMENT_NOT_ACTIVE",
            )
        return row

    async def _bind_enrollment_to_daily_session(
        self,
        session_row: GameSession,
        user_id: uuid.UUID,
        body: CreateMatchBody,
    ) -> None:
        if body.enrollment_id is None:
            return
        en = await self._require_enrollment_for_match(body.enrollment_id, user_id)
        if session_row.enrollment_id is None:
            session_row.enrollment_id = en.id
        elif session_row.enrollment_id != en.id:
            raise ConflictError(
                "Session already bound to a different enrollment",
                code="SESSION_ENROLLMENT_MISMATCH",
            )

    async def create_match(
        self,
        user_id: uuid.UUID,
        body: CreateMatchBody,
        matches_service: MatchesService,
    ) -> MatchCreatedOut:
        await matches_service.ensure_user_game_and_seed_progress(user_id, body.game_id)

        unlocked = await self._matches.is_level_unlocked(user_id, body.level_id)
        if not unlocked:
            raise ForbiddenError("Level is locked for this user", code="LEVEL_LOCKED")

        game = await self._catalog.get_game(body.game_id)
        if game is None or game.deleted_at is not None or not game.is_active:
            raise NotFoundError("Game not found", code="GAME_NOT_FOUND")

        level = await self._catalog.get_level_with_chain(body.level_id)
        if level is None or not CatalogService._level_public_ok(level):
            raise NotFoundError("Level not found", code="LEVEL_NOT_FOUND")

        if level.preset.game_id != body.game_id:
            raise NotFoundError(
                "Level does not belong to informed game", code="LEVEL_GAME_MISMATCH"
            )

        today = _utc_today()
        session_row = await self._sessions.get_active_session_for_day(user_id, today)
        if session_row is None:
            sid = uuid.uuid4()
            session_row = GameSession(id=sid, user_id=user_id, session_date=today)
            self._sessions.add(session_row)
            try:
                await self._session.flush()
            except IntegrityError:
                await self._session.rollback()
                session_row = await self._sessions.get_active_session_for_day(
                    user_id, today
                )
                if session_row is None:
                    raise ConflictError(
                        "Could not resolve daily session after concurrent start",
                        code="SESSION_RACE",
                    ) from None

        await self._bind_enrollment_to_daily_session(session_row, user_id, body)

        mid = uuid.uuid4()
        snapshot = (
            copy.deepcopy(level.config)
            if isinstance(level.config, dict)
            else dict(level.config)
        )
        match_row = Match(
            id=mid,
            session_id=session_row.id,
            game_id=body.game_id,
            level_id=body.level_id,
            level_config_snapshot=snapshot,
        )
        self._sessions.add(match_row)
        await self._session.commit()
        await self._session.refresh(match_row)
        return MatchCreatedOut.model_validate(match_row)
