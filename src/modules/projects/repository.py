"""Project persistence."""

import uuid
from typing import Any

from sqlalchemy import and_, false, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.core.enums import UserRole
from src.models.project import Project, ProjectMember
from src.models.user import User


class ProjectsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def code_taken(self, code: str, *, exclude_id: uuid.UUID | None) -> bool:
        stmt = select(Project.id).where(
            Project.code == code,
            Project.deleted_at.is_(None),
        )
        if exclude_id is not None:
            stmt = stmt.where(Project.id != exclude_id)
        stmt = stmt.limit(1)
        row = await self._session.execute(stmt)
        return row.scalar_one_or_none() is not None

    def add_project(self, row: Project) -> None:
        self._session.add(row)

    def add_member(self, row: ProjectMember) -> None:
        self._session.add(row)

    async def get_user_active(self, user_id: uuid.UUID) -> User | None:
        stmt = select(User).where(User.id == user_id, User.deleted_at.is_(None))
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_project_public(self, project_id: uuid.UUID) -> Project | None:
        stmt = (
            select(Project)
            .where(Project.id == project_id, Project.deleted_at.is_(None))
            .options(joinedload(Project.members))
        )
        result = await self._session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def user_has_any_membership(
        self,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        stmt = (
            select(ProjectMember.id)
            .where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id,
            )
            .limit(1)
        )
        row = await self._session.execute(stmt)
        return row.scalar_one_or_none() is not None

    async def user_is_pi_member(
        self,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
        *,
        pi_role_code: str,
    ) -> bool:
        stmt = (
            select(ProjectMember.id)
            .where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id,
                ProjectMember.role == pi_role_code,
            )
            .limit(1)
        )
        row = await self._session.execute(stmt)
        return row.scalar_one_or_none() is not None

    async def has_pi_member(
        self,
        project_id: uuid.UUID,
        *,
        pi_role_code: str,
    ) -> bool:
        stmt = (
            select(ProjectMember.id)
            .where(
                ProjectMember.project_id == project_id,
                ProjectMember.role == pi_role_code,
            )
            .limit(1)
        )
        row = await self._session.execute(stmt)
        return row.scalar_one_or_none() is not None

    def _not_deleted(self) -> Any:
        return Project.deleted_at.is_(None)

    def _q_filter(self, q: str | None) -> list[Any]:
        if q is None or not (term := q.strip()):
            return []
        like = f"%{term}%"
        return [or_(Project.name.ilike(like), Project.code.ilike(like))]

    async def count_list_scope(
        self,
        *,
        user: User,
        q: str | None,
    ) -> int:
        base = [self._not_deleted(), *self._q_filter(q)]
        stmt = select(func.count()).select_from(Project).where(and_(*base))
        if user.role == UserRole.ADMIN.value:
            result = await self._session.scalar(stmt)
            return int(result or 0)
        if user.role == UserRole.PI.value:
            stmt = (
                select(func.count())
                .select_from(Project)
                .join(ProjectMember, ProjectMember.project_id == Project.id)
                .where(
                    *base,
                    ProjectMember.user_id == user.id,
                    ProjectMember.role == "PI",
                )
            )
            result = await self._session.scalar(stmt)
            return int(result or 0)
        if user.role == UserRole.RESEARCHER.value:
            stmt = (
                select(func.count())
                .select_from(Project)
                .join(ProjectMember, ProjectMember.project_id == Project.id)
                .where(
                    *base,
                    ProjectMember.user_id == user.id,
                )
            )
            result = await self._session.scalar(stmt)
            return int(result or 0)
        return 0

    async def list_scope_page(
        self,
        *,
        user: User,
        q: str | None,
        page: int,
        page_size: int,
    ) -> list[Project]:
        base = [self._not_deleted(), *self._q_filter(q)]
        offset = (page - 1) * page_size
        if user.role == UserRole.ADMIN.value:
            stmt = (
                select(Project)
                .where(and_(*base))
                .order_by(Project.created_at.desc())
                .offset(offset)
                .limit(page_size)
            )
        elif user.role == UserRole.PI.value:
            stmt = (
                select(Project)
                .join(ProjectMember, ProjectMember.project_id == Project.id)
                .where(
                    *base,
                    ProjectMember.user_id == user.id,
                    ProjectMember.role == "PI",
                )
                .distinct()
                .order_by(Project.created_at.desc())
                .offset(offset)
                .limit(page_size)
            )
        elif user.role == UserRole.RESEARCHER.value:
            stmt = (
                select(Project)
                .join(ProjectMember, ProjectMember.project_id == Project.id)
                .where(
                    *base,
                    ProjectMember.user_id == user.id,
                )
                .distinct()
                .order_by(Project.created_at.desc())
                .offset(offset)
                .limit(page_size)
            )
        else:
            stmt = select(Project).where(false()).limit(0)
        result = await self._session.execute(stmt)
        return list(result.unique().scalars().all())
