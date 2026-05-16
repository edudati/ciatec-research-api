"""Persistence for daily sessions and match rows."""

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.models.session_match import GameSession, Match


class SessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_active_session_for_day(
        self, user_id: uuid.UUID, session_date: date
    ) -> GameSession | None:
        stmt = select(GameSession).where(
            GameSession.user_id == user_id,
            GameSession.session_date == session_date,
            GameSession.deleted_at.is_(None),
        )
        return (await self._session.scalars(stmt)).first()

    def add(self, obj: GameSession | Match) -> None:
        self._session.add(obj)

    async def get_match_owned_by_user(
        self, match_id: uuid.UUID, user_id: uuid.UUID
    ) -> Match | None:
        stmt = (
            select(Match)
            .join(GameSession, Match.session_id == GameSession.id)
            .where(
                Match.id == match_id,
                Match.deleted_at.is_(None),
                GameSession.user_id == user_id,
                GameSession.deleted_at.is_(None),
            )
            .options(joinedload(Match.session))
        )
        result = await self._session.execute(stmt)
        return result.unique().scalar_one_or_none()
