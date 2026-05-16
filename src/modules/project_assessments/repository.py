"""Persistence for assessment records and timeline inserts."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.assessment_record import AssessmentRecord
from src.models.assessment_template import AssessmentTemplate
from src.models.participant_enrollment import ParticipantEnrollment


class AssessmentRecordsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_assessment_template(
        self,
        template_id: uuid.UUID,
    ) -> AssessmentTemplate | None:
        stmt = select(AssessmentTemplate).where(AssessmentTemplate.id == template_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

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

    def add_record(self, row: AssessmentRecord) -> None:
        self._session.add(row)

    async def get_by_project_and_id(
        self,
        project_id: uuid.UUID,
        record_id: uuid.UUID,
    ) -> AssessmentRecord | None:
        stmt = select(AssessmentRecord).where(
            AssessmentRecord.id == record_id,
            AssessmentRecord.project_id == project_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_project(self, project_id: uuid.UUID) -> list[AssessmentRecord]:
        stmt = (
            select(AssessmentRecord)
            .where(AssessmentRecord.project_id == project_id)
            .order_by(AssessmentRecord.performed_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
