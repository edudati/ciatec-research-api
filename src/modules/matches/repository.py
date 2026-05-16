"""Persistence for match results, preset context, and user level unlock state."""

import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.progress import UserGame, UserLevelProgress
from src.models.session_match import MatchResult, MatchResultDetail


class MatchRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_user_game(
        self, user_id: uuid.UUID, game_id: uuid.UUID
    ) -> UserGame | None:
        stmt = select(UserGame).where(
            UserGame.user_id == user_id,
            UserGame.game_id == game_id,
            UserGame.deleted_at.is_(None),
        )
        return (await self._session.scalars(stmt)).first()

    async def is_level_unlocked(self, user_id: uuid.UUID, level_id: uuid.UUID) -> bool:
        stmt = select(UserLevelProgress.unlocked).where(
            UserLevelProgress.user_id == user_id,
            UserLevelProgress.level_id == level_id,
        )
        row = (await self._session.execute(stmt)).one_or_none()
        if row is None:
            return False
        return bool(row[0])

    async def list_user_level_progress_for_preset(
        self, user_id: uuid.UUID, preset_id: uuid.UUID
    ) -> list[UserLevelProgress]:
        stmt = select(UserLevelProgress).where(
            UserLevelProgress.user_id == user_id,
            UserLevelProgress.preset_id == preset_id,
        )
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def update_user_game_current_level(
        self, user_game_id: uuid.UUID, level_id: uuid.UUID
    ) -> None:
        await self._session.execute(
            update(UserGame)
            .where(UserGame.id == user_game_id)
            .values(current_level_id=level_id)
        )

    def add(
        self,
        obj: (UserGame | UserLevelProgress | MatchResult | MatchResultDetail),
    ) -> None:
        self._session.add(obj)

    async def get_match_result_by_match_id(
        self, match_id: uuid.UUID
    ) -> MatchResult | None:
        stmt = select(MatchResult).where(MatchResult.match_id == match_id)
        return (await self._session.scalars(stmt)).first()

    async def get_match_result_by_idempotency_key(self, key: str) -> MatchResult | None:
        stmt = select(MatchResult).where(MatchResult.idempotency_key == key)
        return (await self._session.scalars(stmt)).first()

    async def get_match_result_detail(
        self, match_id: uuid.UUID
    ) -> MatchResultDetail | None:
        stmt = select(MatchResultDetail).where(MatchResultDetail.match_id == match_id)
        return (await self._session.scalars(stmt)).first()
