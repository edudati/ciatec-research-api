"""Match preset, level read, finish with idempotency."""

import json
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ConflictError, NotFoundError, ValidationError
from src.models.progress import UserGame, UserLevelProgress
from src.models.session_match import Match, MatchResult, MatchResultDetail
from src.modules.catalog.repository import CatalogRepository
from src.modules.catalog.service import CatalogService
from src.modules.matches.repository import MatchRepository
from src.modules.matches.schemas import (
    MatchFinishBody,
    MatchFinishOut,
    MatchFinishResponse,
    MatchLevelOut,
    MatchPresetOut,
    PresetLevelSummaryOut,
    PresetWithLevelsOut,
    build_result_detail_payload,
    normalize_idempotency_key,
)
from src.modules.project_enrollments.repository import ProjectEnrollmentsRepository
from src.modules.sessions.repository import SessionRepository
from src.modules.timeline.dispatcher import publish_timeline_event
from src.modules.timeline.job_payload import TimelineEventJobPayload
from src.modules.vocabulary.repository import (
    TIMELINE_EVENT_TYPE_SCHEME_CODE,
    VocabularyRepository,
)

_TIMELINE_GAME_SESSION = "GAME_SESSION"
_SOURCE_TYPE_MATCH = "Match"


class MatchesService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._matches = MatchRepository(session)
        self._sessions = SessionRepository(session)
        self._catalog = CatalogRepository(session)
        self._enrollments = ProjectEnrollmentsRepository(session)
        self._vocab = VocabularyRepository(session)

    async def ensure_user_game_and_seed_progress(
        self, user_id: uuid.UUID, game_id: uuid.UUID
    ) -> UserGame:
        existing = await self._matches.get_user_game(user_id, game_id)
        if existing is not None:
            return existing

        game = await self._catalog.get_game(game_id)
        if game is None or game.deleted_at is not None or not game.is_active:
            raise NotFoundError("Game not found", code="GAME_NOT_FOUND")

        presets = await self._catalog.list_presets_for_game_public(game_id)
        if not presets:
            raise NotFoundError(
                "No preset found for this game", code="PRESET_NOT_FOUND"
            )
        preset = presets[0]

        levels = await self._catalog.list_levels_for_preset_public(preset.id)
        if not levels:
            raise NotFoundError(
                "No level found for the selected preset", code="LEVEL_NOT_FOUND"
            )
        first = levels[0]

        ug = UserGame(
            id=uuid.uuid4(),
            user_id=user_id,
            game_id=game_id,
            preset_id=preset.id,
            current_level_id=first.id,
        )
        self._matches.add(ug)

        for lvl in levels:
            self._matches.add(
                UserLevelProgress(
                    id=uuid.uuid4(),
                    user_id=user_id,
                    preset_id=preset.id,
                    level_id=lvl.id,
                    unlocked=(lvl.id == first.id),
                )
            )
        try:
            await self._session.flush()
        except IntegrityError:
            await self._session.rollback()
            again = await self._matches.get_user_game(user_id, game_id)
            if again is None:
                raise ConflictError(
                    "Could not create user game after concurrent request",
                    code="USER_GAME_RACE",
                ) from None
            return again

        await self._session.commit()
        return ug

    async def get_preset(
        self, user_id: uuid.UUID, game_id: uuid.UUID
    ) -> MatchPresetOut:
        user_game = await self.ensure_user_game_and_seed_progress(user_id, game_id)

        preset = await self._catalog.get_preset_with_game(user_game.preset_id)
        if preset is None:
            raise NotFoundError("Preset not found", code="PRESET_NOT_FOUND")

        anchor = await self._catalog.get_level_with_chain(user_game.current_level_id)
        if anchor is None or not CatalogService._level_public_ok(anchor):
            raise NotFoundError("Preset not found", code="PRESET_NOT_FOUND")

        levels = await self._catalog.list_levels_for_preset_public(preset.id)
        level_summaries = [
            PresetLevelSummaryOut(
                id=lvl.id,
                preset_id=lvl.preset_id,
                name=lvl.name,
                order=lvl.level_order,
            )
            for lvl in levels
        ]
        return MatchPresetOut(
            user_game_id=user_game.id,
            game_id=user_game.game_id,
            preset=PresetWithLevelsOut(
                id=preset.id,
                game_id=preset.game_id,
                name=preset.name,
                description=preset.description,
                is_default=preset.is_default,
                levels=level_summaries,
            ),
            current_level_id=user_game.current_level_id,
        )

    async def get_level(
        self, preset_id: uuid.UUID, level_id: uuid.UUID
    ) -> MatchLevelOut:
        level = await self._catalog.get_level_with_chain(level_id)
        if (
            level is None
            or level.preset_id != preset_id
            or not CatalogService._level_public_ok(level)
        ):
            raise NotFoundError("Level not found", code="LEVEL_NOT_FOUND")
        return MatchLevelOut(
            id=level.id,
            preset_id=level.preset_id,
            name=level.name,
            order=level.level_order,
            config=level.config
            if isinstance(level.config, dict)
            else dict(level.config),
        )

    @staticmethod
    def _payloads_equivalent(
        stored_result: MatchResult,
        stored_detail: dict[str, object],
        body: MatchFinishBody,
    ) -> bool:
        if (
            stored_result.score != body.score
            or stored_result.duration_ms != body.duration_ms
            or stored_result.completed != body.completed
        ):
            return False
        expected = build_result_detail_payload(body.extra, body.client_meta)
        return json.dumps(expected, sort_keys=True, default=str) == json.dumps(
            stored_detail, sort_keys=True, default=str
        )

    @staticmethod
    def _to_finish_out(
        result: MatchResult,
        detail: dict[str, Any],
        match: Match,
    ) -> MatchFinishOut:
        server_ms = result.server_duration_ms
        if server_ms is None:
            delta = result.created_at - match.started_at
            server_ms = max(0, int(delta.total_seconds() * 1000))
        return MatchFinishOut(
            id=result.id,
            match_id=result.match_id,
            score=result.score,
            duration_ms=result.duration_ms,
            server_duration_ms=server_ms,
            completed=result.completed,
            extra=detail if isinstance(detail, dict) else {},
            created_at=result.created_at,
        )

    @staticmethod
    def _naive_utc(dt: datetime) -> datetime:
        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)

    @staticmethod
    def _dt_iso(dt: datetime) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC).isoformat()

    async def _validate_timeline_game_session_type(self) -> None:
        ok = await self._vocab.is_active_term_in_scheme(
            scheme_code=TIMELINE_EVENT_TYPE_SCHEME_CODE,
            term_code=_TIMELINE_GAME_SESSION,
        )
        if not ok:
            raise ValidationError(
                "Game session timeline event type is not configured",
                code="VALIDATION_ERROR",
            )

    async def _maybe_game_session_timeline_payload(
        self,
        match: Match,
        result: MatchResult,
    ) -> TimelineEventJobPayload | None:
        if match.session.enrollment_id is None:
            return None
        enrollment = await self._enrollments.get_by_id(match.session.enrollment_id)
        if enrollment is None:
            return None
        await self._validate_timeline_game_session_type()
        ctx: dict[str, Any] = {
            "gameId": str(match.game_id),
            "levelId": str(match.level_id),
            "score": result.score,
            "durationMs": result.duration_ms,
            "completed": result.completed,
        }
        return TimelineEventJobPayload(
            id=uuid.uuid4(),
            participant_profile_id=enrollment.participant_profile_id,
            project_id=enrollment.project_id,
            enrollment_id=enrollment.id,
            executor_id=None,
            event_type=_TIMELINE_GAME_SESSION,
            source_type=_SOURCE_TYPE_MATCH,
            source_id=str(match.id),
            occurred_at=self._dt_iso(match.started_at),
            context=ctx,
        )

    async def finish_match(
        self,
        user_id: uuid.UUID,
        match_id: uuid.UUID,
        body: MatchFinishBody,
        idempotency_header: str | None,
    ) -> MatchFinishResponse:
        try:
            idem_key = normalize_idempotency_key(idempotency_header, body)
        except ValueError as exc:
            raise ValidationError(str(exc), code="VALIDATION_ERROR") from exc

        match = await self._sessions.get_match_owned_by_user(match_id, user_id)
        if match is None:
            raise NotFoundError("Match not found", code="MATCH_NOT_FOUND")

        existing = await self._matches.get_match_result_by_match_id(match_id)
        detail_row = await self._matches.get_match_result_detail(match_id)
        stored_detail: dict[str, Any] = (
            dict(detail_row.data)
            if detail_row is not None and isinstance(detail_row.data, dict)
            else {}
        )

        if existing is not None:
            return self._finish_when_already_stored(
                existing, stored_detail, body, idem_key, match
            )

        if idem_key is not None:
            key_owner = await self._matches.get_match_result_by_idempotency_key(
                idem_key
            )
            if key_owner is not None and key_owner.match_id != match_id:
                raise ConflictError(
                    "Idempotency key already used",
                    code="IDEMPOTENCY_KEY_IN_USE",
                )

        server_ms = max(
            0,
            int((datetime.now(UTC) - match.started_at).total_seconds() * 1000),
        )
        detail_payload = build_result_detail_payload(body.extra, body.client_meta)

        new_result = MatchResult(
            id=uuid.uuid4(),
            match_id=match_id,
            score=body.score,
            duration_ms=body.duration_ms,
            server_duration_ms=server_ms,
            completed=body.completed,
            idempotency_key=idem_key,
        )
        new_detail = MatchResultDetail(
            id=uuid.uuid4(),
            match_id=match_id,
            data=detail_payload,
        )
        self._matches.add(new_result)
        self._matches.add(new_detail)

        try:
            await self._session.flush()
        except IntegrityError:
            await self._session.rollback()
            return await self._reconcile_finish_after_race(
                user_id, match_id, body, idem_key
            )

        tl_payload = await self._maybe_game_session_timeline_payload(match, new_result)
        await self._session.commit()
        if tl_payload is not None:
            await publish_timeline_event(tl_payload)
        await self._session.refresh(new_result)
        out = self._to_finish_out(new_result, detail_payload, match)
        return MatchFinishResponse(body=out, status_code=201)

    def _finish_when_already_stored(
        self,
        existing: MatchResult,
        stored_detail: dict[str, Any],
        body: MatchFinishBody,
        idem_key: str | None,
        match: Match,
    ) -> MatchFinishResponse:
        if idem_key is None or existing.idempotency_key != idem_key:
            raise ConflictError("Match already finished", code="MATCH_ALREADY_FINISHED")

        if not self._payloads_equivalent(existing, stored_detail, body):
            raise ConflictError(
                "Idempotency key reused with different payload",
                code="IDEMPOTENCY_MISMATCH",
            )

        out = self._to_finish_out(existing, stored_detail, match)
        return MatchFinishResponse(body=out, status_code=200)

    async def _reconcile_finish_after_race(
        self,
        user_id: uuid.UUID,
        match_id: uuid.UUID,
        body: MatchFinishBody,
        idem_key: str | None,
    ) -> MatchFinishResponse:
        match = await self._sessions.get_match_owned_by_user(match_id, user_id)
        if match is None:
            raise NotFoundError("Match not found", code="MATCH_NOT_FOUND")

        by_match = await self._matches.get_match_result_by_match_id(match_id)
        detail_row = await self._matches.get_match_result_detail(match_id)
        stored_detail: dict[str, Any] = (
            dict(detail_row.data)
            if detail_row is not None and isinstance(detail_row.data, dict)
            else {}
        )

        if by_match is not None:
            return self._finish_when_already_stored(
                by_match, stored_detail, body, idem_key, match
            )

        if idem_key is not None:
            by_key = await self._matches.get_match_result_by_idempotency_key(idem_key)
            if by_key is not None:
                if by_key.match_id != match_id:
                    raise ConflictError(
                        "Idempotency key already used",
                        code="IDEMPOTENCY_KEY_IN_USE",
                    )
                detail2 = await self._matches.get_match_result_detail(by_key.match_id)
                stored2: dict[str, Any] = (
                    dict(detail2.data)
                    if detail2 is not None and isinstance(detail2.data, dict)
                    else {}
                )
                return self._finish_when_already_stored(
                    by_key, stored2, body, idem_key, match
                )

        raise ConflictError("Match already finished", code="MATCH_ALREADY_FINISHED")
