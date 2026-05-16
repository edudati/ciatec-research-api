"""Assessment templates persistence."""

import uuid
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from src.models.assessment_template import AssessmentTemplate


class AssessmentTemplatesRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _public_list_conditions(self) -> list[ColumnElement[bool]]:
        return [AssessmentTemplate.is_active.is_(True)]

    async def count_list_public(self) -> int:
        stmt = (
            select(func.count())
            .select_from(AssessmentTemplate)
            .where(and_(*self._public_list_conditions()))
        )
        result = await self._session.scalar(stmt)
        return int(result or 0)

    async def list_page_public(
        self,
        *,
        page: int,
        page_size: int,
        sort_column: Any,
        order_desc: bool,
    ) -> list[AssessmentTemplate]:
        conds = self._public_list_conditions()
        stmt = select(AssessmentTemplate).where(and_(*conds))
        if order_desc:
            stmt = stmt.order_by(sort_column.desc())
        else:
            stmt = stmt.order_by(sort_column.asc())
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, row_id: uuid.UUID) -> AssessmentTemplate | None:
        stmt = select(AssessmentTemplate).where(AssessmentTemplate.id == row_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_public_by_id(self, row_id: uuid.UUID) -> AssessmentTemplate | None:
        stmt = select(AssessmentTemplate).where(
            AssessmentTemplate.id == row_id,
            *self._public_list_conditions(),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_for_admin_mutation(
        self,
        row_id: uuid.UUID,
    ) -> AssessmentTemplate | None:
        return await self.get_by_id(row_id)

    async def code_taken(self, code: str, exclude_id: uuid.UUID | None) -> bool:
        stmt = select(AssessmentTemplate.id).where(AssessmentTemplate.code == code)
        if exclude_id is not None:
            stmt = stmt.where(AssessmentTemplate.id != exclude_id)
        stmt = stmt.limit(1)
        row = await self._session.execute(stmt)
        return row.scalar_one_or_none() is not None

    def add(self, row: AssessmentTemplate) -> None:
        self._session.add(row)
