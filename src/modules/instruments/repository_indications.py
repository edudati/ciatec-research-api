"""Instrument indications persistence."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.assessment_template import AssessmentTemplate
from src.models.health_condition import HealthCondition
from src.models.instrument_indication import InstrumentIndication
from src.models.questionnaire_template import QuestionnaireTemplate


class InstrumentIndicationsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def assessment_template_exists(self, row_id: uuid.UUID) -> bool:
        stmt = (
            select(AssessmentTemplate.id)
            .where(AssessmentTemplate.id == row_id)
            .limit(1)
        )
        row = await self._session.execute(stmt)
        return row.scalar_one_or_none() is not None

    async def questionnaire_template_exists(self, row_id: uuid.UUID) -> bool:
        stmt = (
            select(QuestionnaireTemplate.id)
            .where(QuestionnaireTemplate.id == row_id)
            .limit(1)
        )
        row = await self._session.execute(stmt)
        return row.scalar_one_or_none() is not None

    async def usable_health_condition_exists(self, row_id: uuid.UUID) -> bool:
        stmt = (
            select(HealthCondition.id)
            .where(
                HealthCondition.id == row_id,
                HealthCondition.deleted_at.is_(None),
                HealthCondition.is_active.is_(True),
            )
            .limit(1)
        )
        row = await self._session.execute(stmt)
        return row.scalar_one_or_none() is not None

    async def triple_exists(
        self,
        *,
        instrument_type: str,
        instrument_id: uuid.UUID,
        health_condition_id: uuid.UUID,
    ) -> bool:
        stmt = select(InstrumentIndication.id).where(
            InstrumentIndication.instrument_type == instrument_type,
            InstrumentIndication.instrument_id == instrument_id,
            InstrumentIndication.health_condition_id == health_condition_id,
        )
        row = await self._session.execute(stmt.limit(1))
        return row.scalar_one_or_none() is not None

    def add(self, row: InstrumentIndication) -> None:
        self._session.add(row)

    async def get_by_id(self, row_id: uuid.UUID) -> InstrumentIndication | None:
        stmt = select(InstrumentIndication).where(InstrumentIndication.id == row_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_instrument(
        self,
        *,
        instrument_type: str,
        instrument_id: uuid.UUID,
    ) -> list[InstrumentIndication]:
        stmt = (
            select(InstrumentIndication)
            .where(
                InstrumentIndication.instrument_type == instrument_type,
                InstrumentIndication.instrument_id == instrument_id,
            )
            .order_by(InstrumentIndication.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_health_condition(
        self,
        *,
        health_condition_id: uuid.UUID,
    ) -> list[InstrumentIndication]:
        stmt = (
            select(InstrumentIndication)
            .where(InstrumentIndication.health_condition_id == health_condition_id)
            .order_by(InstrumentIndication.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def delete_by_id(self, row_id: uuid.UUID) -> bool:
        row = await self.get_by_id(row_id)
        if row is None:
            return False
        await self._session.delete(row)
        return True
