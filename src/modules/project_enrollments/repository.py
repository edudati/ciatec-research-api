"""Persistence for participant enrollments and timeline inserts."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.models.participant_enrollment import ParticipantEnrollment


class ProjectEnrollmentsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def exists_for_project_and_profile(
        self,
        project_id: uuid.UUID,
        participant_profile_id: uuid.UUID,
    ) -> bool:
        stmt = (
            select(ParticipantEnrollment.id)
            .where(
                ParticipantEnrollment.project_id == project_id,
                ParticipantEnrollment.participant_profile_id == participant_profile_id,
            )
            .limit(1)
        )
        row = await self._session.execute(stmt)
        return row.scalar_one_or_none() is not None

    async def list_by_project(
        self, project_id: uuid.UUID
    ) -> list[ParticipantEnrollment]:
        stmt = (
            select(ParticipantEnrollment)
            .where(ParticipantEnrollment.project_id == project_id)
            .options(joinedload(ParticipantEnrollment.participant_profile))
            .order_by(ParticipantEnrollment.enrolled_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.unique().scalars().all())

    async def get_by_id(self, enrollment_id: uuid.UUID) -> ParticipantEnrollment | None:
        stmt = (
            select(ParticipantEnrollment)
            .where(ParticipantEnrollment.id == enrollment_id)
            .options(joinedload(ParticipantEnrollment.participant_profile))
        )
        result = await self._session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_by_project_and_id(
        self,
        project_id: uuid.UUID,
        enrollment_id: uuid.UUID,
    ) -> ParticipantEnrollment | None:
        stmt = (
            select(ParticipantEnrollment)
            .where(
                ParticipantEnrollment.id == enrollment_id,
                ParticipantEnrollment.project_id == project_id,
            )
            .options(joinedload(ParticipantEnrollment.participant_profile))
        )
        result = await self._session.execute(stmt)
        return result.unique().scalar_one_or_none()

    def add_enrollment(self, row: ParticipantEnrollment) -> None:
        self._session.add(row)
