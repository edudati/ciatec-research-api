"""Persistence for project groups and enrollment guard queries."""

import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.participant_enrollment import ParticipantEnrollment
from src.models.project import ProjectGroup


class ProjectGroupsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _name_match_expr(self) -> Any:
        return func.lower(func.trim(ProjectGroup.name))

    async def name_taken_ci(
        self,
        project_id: uuid.UUID,
        stripped_name: str,
        *,
        exclude_group_id: uuid.UUID | None,
    ) -> bool:
        target = stripped_name.lower()
        stmt = select(ProjectGroup.id).where(
            ProjectGroup.project_id == project_id,
            self._name_match_expr() == target,
        )
        if exclude_group_id is not None:
            stmt = stmt.where(ProjectGroup.id != exclude_group_id)
        stmt = stmt.limit(1)
        row = await self._session.execute(stmt)
        return row.scalar_one_or_none() is not None

    async def list_by_project(self, project_id: uuid.UUID) -> list[ProjectGroup]:
        stmt = (
            select(ProjectGroup)
            .where(ProjectGroup.project_id == project_id)
            .order_by(ProjectGroup.created_at.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(
        self,
        project_id: uuid.UUID,
        group_id: uuid.UUID,
    ) -> ProjectGroup | None:
        stmt = select(ProjectGroup).where(
            ProjectGroup.id == group_id,
            ProjectGroup.project_id == project_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def count_active_enrollments_for_group(self, group_id: uuid.UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(ParticipantEnrollment)
            .where(
                ParticipantEnrollment.group_id == group_id,
                ParticipantEnrollment.status == "ACTIVE",
                ParticipantEnrollment.exited_at.is_(None),
            )
        )
        raw = await self._session.scalar(stmt)
        return int(raw or 0)

    def add_group(self, row: ProjectGroup) -> None:
        self._session.add(row)

    async def delete_group(self, row: ProjectGroup) -> None:
        await self._session.delete(row)
