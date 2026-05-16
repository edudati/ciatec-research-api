"""Persistence for intervention records and timeline inserts."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.intervention_record import InterventionRecord
from src.models.intervention_template import InterventionTemplate
from src.models.participant_enrollment import ParticipantEnrollment
from src.models.session_match import Match


class InterventionRecordsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_intervention_template(
        self,
        template_id: uuid.UUID,
    ) -> InterventionTemplate | None:
        stmt = select(InterventionTemplate).where(
            InterventionTemplate.id == template_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_match(self, match_id: uuid.UUID) -> Match | None:
        stmt = select(Match).where(Match.id == match_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def has_record_for_match(self, match_id: uuid.UUID) -> bool:
        stmt = select(InterventionRecord.id).where(
            InterventionRecord.match_id == match_id,
        )
        row = await self._session.execute(stmt)
        return row.scalar_one_or_none() is not None

    async def get_active_enrollment_id(
        self,
        *,
        project_id: uuid.UUID,
        participant_profile_id: uuid.UUID,
    ) -> uuid.UUID | None:
        stmt = (
            select(ParticipantEnrollment.id)
            .where(
                ParticipantEnrollment.project_id == project_id,
                ParticipantEnrollment.participant_profile_id == participant_profile_id,
                ParticipantEnrollment.status != "WITHDRAWN",
                ParticipantEnrollment.exited_at.is_(None),
            )
            .limit(1)
        )
        row = await self._session.execute(stmt)
        return row.scalar_one_or_none()

    def add_record(self, row: InterventionRecord) -> None:
        self._session.add(row)

    async def get_by_project_and_id(
        self,
        project_id: uuid.UUID,
        record_id: uuid.UUID,
    ) -> InterventionRecord | None:
        stmt = select(InterventionRecord).where(
            InterventionRecord.id == record_id,
            InterventionRecord.project_id == project_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_project(
        self,
        project_id: uuid.UUID,
    ) -> list[InterventionRecord]:
        stmt = (
            select(InterventionRecord)
            .where(InterventionRecord.project_id == project_id)
            .order_by(InterventionRecord.performed_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
