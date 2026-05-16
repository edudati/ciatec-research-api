"""Questionnaire templates and question items persistence."""

import uuid
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from src.models.question_item import QuestionItem
from src.models.questionnaire_template import QuestionnaireTemplate


class QuestionnairesRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _public_template_conditions(self) -> list[ColumnElement[bool]]:
        return [QuestionnaireTemplate.is_active.is_(True)]

    async def count_templates_public(self) -> int:
        stmt = (
            select(func.count())
            .select_from(QuestionnaireTemplate)
            .where(and_(*self._public_template_conditions()))
        )
        result = await self._session.scalar(stmt)
        return int(result or 0)

    async def list_templates_page_public(
        self,
        *,
        page: int,
        page_size: int,
        sort_column: Any,
        order_desc: bool,
    ) -> list[QuestionnaireTemplate]:
        conds = self._public_template_conditions()
        stmt = select(QuestionnaireTemplate).where(and_(*conds))
        if order_desc:
            stmt = stmt.order_by(sort_column.desc())
        else:
            stmt = stmt.order_by(sort_column.asc())
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_template_by_id(
        self,
        template_id: uuid.UUID,
    ) -> QuestionnaireTemplate | None:
        stmt = select(QuestionnaireTemplate).where(
            QuestionnaireTemplate.id == template_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_template_public_by_id(
        self,
        template_id: uuid.UUID,
    ) -> QuestionnaireTemplate | None:
        stmt = select(QuestionnaireTemplate).where(
            QuestionnaireTemplate.id == template_id,
            *self._public_template_conditions(),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def template_code_taken(
        self,
        code: str,
        exclude_id: uuid.UUID | None,
    ) -> bool:
        stmt = select(QuestionnaireTemplate.id).where(
            QuestionnaireTemplate.code == code
        )
        if exclude_id is not None:
            stmt = stmt.where(QuestionnaireTemplate.id != exclude_id)
        stmt = stmt.limit(1)
        row = await self._session.execute(stmt)
        return row.scalar_one_or_none() is not None

    def add_template(self, row: QuestionnaireTemplate) -> None:
        self._session.add(row)

    async def list_items_for_template_ordered(
        self,
        template_id: uuid.UUID,
    ) -> list[QuestionItem]:
        stmt = (
            select(QuestionItem)
            .where(QuestionItem.questionnaire_template_id == template_id)
            .order_by(QuestionItem.display_order.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_item_by_template_and_id(
        self,
        template_id: uuid.UUID,
        item_id: uuid.UUID,
    ) -> QuestionItem | None:
        stmt = select(QuestionItem).where(
            QuestionItem.id == item_id,
            QuestionItem.questionnaire_template_id == template_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def item_code_taken(
        self,
        template_id: uuid.UUID,
        code: str,
        exclude_item_id: uuid.UUID | None,
    ) -> bool:
        stmt = select(QuestionItem.id).where(
            QuestionItem.questionnaire_template_id == template_id,
            QuestionItem.code == code,
        )
        if exclude_item_id is not None:
            stmt = stmt.where(QuestionItem.id != exclude_item_id)
        stmt = stmt.limit(1)
        row = await self._session.execute(stmt)
        return row.scalar_one_or_none() is not None

    async def item_order_taken(
        self,
        template_id: uuid.UUID,
        order: int,
        exclude_item_id: uuid.UUID | None,
    ) -> bool:
        stmt = select(QuestionItem.id).where(
            QuestionItem.questionnaire_template_id == template_id,
            QuestionItem.display_order == order,
        )
        if exclude_item_id is not None:
            stmt = stmt.where(QuestionItem.id != exclude_item_id)
        stmt = stmt.limit(1)
        row = await self._session.execute(stmt)
        return row.scalar_one_or_none() is not None

    def add_item(self, row: QuestionItem) -> None:
        self._session.add(row)

    async def delete_item(self, row: QuestionItem) -> None:
        await self._session.delete(row)
