"""Persistence for participant x health condition links."""

import uuid

from sqlalchemy import and_, nulls_last, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.health_condition import HealthCondition
from src.models.participant_condition import ParticipantCondition
from src.models.participant_profile import ParticipantProfile


class ParticipantConditionsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_active_profile(
        self,
        profile_id: uuid.UUID,
    ) -> ParticipantProfile | None:
        stmt = (
            select(ParticipantProfile)
            .where(
                ParticipantProfile.id == profile_id,
                ParticipantProfile.deleted_at.is_(None),
            )
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_assignable_health_condition(
        self,
        hc_id: uuid.UUID,
    ) -> HealthCondition | None:
        stmt = select(HealthCondition).where(
            HealthCondition.id == hc_id,
            HealthCondition.deleted_at.is_(None),
            HealthCondition.is_active.is_(True),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_participant(
        self,
        profile_id: uuid.UUID,
    ) -> list[ParticipantCondition]:
        stmt = (
            select(ParticipantCondition)
            .where(ParticipantCondition.participant_profile_id == profile_id)
            .order_by(
                nulls_last(ParticipantCondition.diagnosed_at.asc()),
                ParticipantCondition.created_at.asc(),
            )
        )
        result = await self._session.execute(stmt)
        return list(result.unique().scalars().all())

    async def get_link_for_participant(
        self,
        profile_id: uuid.UUID,
        link_id: uuid.UUID,
    ) -> ParticipantCondition | None:
        stmt = (
            select(ParticipantCondition)
            .where(
                and_(
                    ParticipantCondition.id == link_id,
                    ParticipantCondition.participant_profile_id == profile_id,
                ),
            )
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, row: ParticipantCondition) -> None:
        self._session.add(row)

    async def delete(self, row: ParticipantCondition) -> None:
        await self._session.delete(row)
