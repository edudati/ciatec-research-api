"""Persistence for project members."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.models.project import ProjectMember


class ProjectMembersRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_project(self, project_id: uuid.UUID) -> list[ProjectMember]:
        stmt = (
            select(ProjectMember)
            .where(ProjectMember.project_id == project_id)
            .order_by(ProjectMember.created_at.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(
        self,
        project_id: uuid.UUID,
        member_id: uuid.UUID,
    ) -> ProjectMember | None:
        stmt = (
            select(ProjectMember)
            .where(
                ProjectMember.id == member_id,
                ProjectMember.project_id == project_id,
            )
            .options(joinedload(ProjectMember.user))
        )
        result = await self._session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def count_pi_members(
        self,
        project_id: uuid.UUID,
        *,
        pi_role_code: str,
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(ProjectMember)
            .where(
                ProjectMember.project_id == project_id,
                ProjectMember.role == pi_role_code,
            )
        )
        raw = await self._session.scalar(stmt)
        return int(raw or 0)

    def add_member(self, row: ProjectMember) -> None:
        self._session.add(row)

    async def delete_member(self, row: ProjectMember) -> None:
        await self._session.delete(row)
