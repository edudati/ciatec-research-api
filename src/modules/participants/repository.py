"""Participant profile persistence."""

import uuid
from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.elements import ColumnElement

from src.models.participant_profile import ParticipantProfile
from src.models.user import User


class ParticipantsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def is_user_active(self, user_id: uuid.UUID) -> bool:
        stmt = (
            select(User.id)
            .where(User.id == user_id, User.deleted_at.is_(None))
            .limit(1)
        )
        row = await self._session.execute(stmt)
        return row.scalar_one_or_none() is not None

    async def get_active_by_user_id(
        self, user_id: uuid.UUID
    ) -> ParticipantProfile | None:
        stmt = (
            select(ParticipantProfile)
            .where(
                ParticipantProfile.user_id == user_id,
                ParticipantProfile.deleted_at.is_(None),
            )
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_by_id(
        self, profile_id: uuid.UUID
    ) -> ParticipantProfile | None:
        stmt = (
            select(ParticipantProfile)
            .where(
                ParticipantProfile.id == profile_id,
                ParticipantProfile.deleted_at.is_(None),
            )
            .options(joinedload(ParticipantProfile.user))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    def _list_base_conditions(
        self,
        *,
        q: str | None,
    ) -> list[ColumnElement[bool]]:
        conds: list[ColumnElement[bool]] = [
            ParticipantProfile.deleted_at.is_(None),
            User.deleted_at.is_(None),
        ]
        if q is not None and (term := q.strip()):
            like = f"%{term}%"
            conds.append(
                or_(
                    User.name.ilike(like),
                    User.email.ilike(like),
                    ParticipantProfile.notes.ilike(like),
                ),
            )
        return conds

    async def count_list(self, *, q: str | None) -> int:
        conds = self._list_base_conditions(q=q)
        stmt = (
            select(func.count())
            .select_from(ParticipantProfile)
            .join(User, User.id == ParticipantProfile.user_id)
            .where(and_(*conds))
        )
        result = await self._session.scalar(stmt)
        return int(result or 0)

    async def list_page(
        self,
        *,
        page: int,
        page_size: int,
        q: str | None,
        sort_column: Any,
        order_desc: bool,
    ) -> list[ParticipantProfile]:
        conds = self._list_base_conditions(q=q)
        stmt = (
            select(ParticipantProfile)
            .join(User, User.id == ParticipantProfile.user_id)
            .where(and_(*conds))
            .options(joinedload(ParticipantProfile.user))
        )
        if order_desc:
            stmt = stmt.order_by(sort_column.desc())
        else:
            stmt = stmt.order_by(sort_column.asc())
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)
        result = await self._session.execute(stmt)
        return list(result.unique().scalars().all())

    def add(self, row: ParticipantProfile) -> None:
        self._session.add(row)
