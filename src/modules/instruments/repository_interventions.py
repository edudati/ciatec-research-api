"""Intervention templates persistence."""

import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.catalog import Game
from src.models.intervention_template import InterventionTemplate


class InterventionTemplatesRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def count_all(self) -> int:
        stmt = select(func.count()).select_from(InterventionTemplate)
        result = await self._session.scalar(stmt)
        return int(result or 0)

    async def list_page(
        self,
        *,
        page: int,
        page_size: int,
        sort_column: Any,
        order_desc: bool,
    ) -> list[InterventionTemplate]:
        stmt = select(InterventionTemplate)
        if order_desc:
            stmt = stmt.order_by(sort_column.desc())
        else:
            stmt = stmt.order_by(sort_column.asc())
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, row_id: uuid.UUID) -> InterventionTemplate | None:
        stmt = select(InterventionTemplate).where(InterventionTemplate.id == row_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def code_taken(self, code: str, exclude_id: uuid.UUID | None) -> bool:
        stmt = select(InterventionTemplate.id).where(InterventionTemplate.code == code)
        if exclude_id is not None:
            stmt = stmt.where(InterventionTemplate.id != exclude_id)
        stmt = stmt.limit(1)
        row = await self._session.execute(stmt)
        return row.scalar_one_or_none() is not None

    async def usable_game_exists(self, game_id: uuid.UUID) -> bool:
        stmt = select(Game.id).where(
            Game.id == game_id,
            Game.deleted_at.is_(None),
        )
        row = await self._session.execute(stmt.limit(1))
        return row.scalar_one_or_none() is not None

    def add(self, row: InterventionTemplate) -> None:
        self._session.add(row)
