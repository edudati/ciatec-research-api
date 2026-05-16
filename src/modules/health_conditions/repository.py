"""Health conditions persistence."""

import uuid
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from src.models.health_condition import HealthCondition
from src.models.participant_condition import ParticipantCondition


class HealthConditionsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _public_list_conditions(self) -> list[ColumnElement[bool]]:
        return [
            HealthCondition.deleted_at.is_(None),
            HealthCondition.is_active.is_(True),
        ]

    def _list_conditions(
        self,
        *,
        category: str | None,
        public_only: bool,
    ) -> list[ColumnElement[bool]]:
        conds: list[ColumnElement[bool]] = []
        if public_only:
            conds.extend(self._public_list_conditions())
        else:
            conds.append(HealthCondition.deleted_at.is_(None))
        if category is not None and (term := category.strip()):
            conds.append(
                func.lower(HealthCondition.category) == func.lower(term),
            )
        return conds

    async def count_list(
        self,
        *,
        category: str | None,
        public_only: bool,
    ) -> int:
        conds = self._list_conditions(category=category, public_only=public_only)
        stmt = select(func.count()).select_from(HealthCondition).where(and_(*conds))
        result = await self._session.scalar(stmt)
        return int(result or 0)

    async def list_page(
        self,
        *,
        page: int,
        page_size: int,
        category: str | None,
        public_only: bool,
        sort_column: Any,
        order_desc: bool,
    ) -> list[HealthCondition]:
        conds = self._list_conditions(category=category, public_only=public_only)
        stmt = select(HealthCondition).where(and_(*conds))
        if order_desc:
            stmt = stmt.order_by(sort_column.desc())
        else:
            stmt = stmt.order_by(sort_column.asc())
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, hc_id: uuid.UUID) -> HealthCondition | None:
        stmt = select(HealthCondition).where(HealthCondition.id == hc_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_public_by_id(self, hc_id: uuid.UUID) -> HealthCondition | None:
        stmt = select(HealthCondition).where(
            HealthCondition.id == hc_id,
            *self._public_list_conditions(),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_row_for_mutation(
        self,
        hc_id: uuid.UUID,
    ) -> HealthCondition | None:
        stmt = select(HealthCondition).where(
            HealthCondition.id == hc_id,
            HealthCondition.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def code_taken(self, code: str, exclude_id: uuid.UUID | None) -> bool:
        stmt = select(HealthCondition.id).where(HealthCondition.code == code)
        if exclude_id is not None:
            stmt = stmt.where(HealthCondition.id != exclude_id)
        stmt = stmt.limit(1)
        row = await self._session.execute(stmt)
        return row.scalar_one_or_none() is not None

    async def count_participant_links(self, health_condition_id: uuid.UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(ParticipantCondition)
            .where(ParticipantCondition.health_condition_id == health_condition_id)
        )
        result = await self._session.scalar(stmt)
        return int(result or 0)

    def add(self, row: HealthCondition) -> None:
        self._session.add(row)
