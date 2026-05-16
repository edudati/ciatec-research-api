"""Business logic for project groups."""

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.enums import UserRole
from src.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from src.models.project import ProjectGroup
from src.models.user import User
from src.modules.project_groups.repository import ProjectGroupsRepository
from src.modules.project_groups.schemas import (
    GroupCreateIn,
    GroupListResponse,
    GroupOut,
    GroupPatchIn,
)
from src.modules.projects.repository import ProjectsRepository

_PROJECT_PI_ROLE_CODE = "PI"


class ProjectGroupsService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._groups = ProjectGroupsRepository(session)
        self._projects = ProjectsRepository(session)

    @staticmethod
    def _dt_iso(dt: datetime) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.isoformat()

    def _to_out(self, row: ProjectGroup) -> GroupOut:
        return GroupOut(
            id=str(row.id),
            name=row.name,
            description=row.description,
            is_active=row.is_active,
            created_at=self._dt_iso(row.created_at),
            updated_at=self._dt_iso(row.updated_at),
        )

    async def _require_project(self, project_id: uuid.UUID) -> None:
        row = await self._projects.get_project_public(project_id)
        if row is None:
            raise NotFoundError("Project not found", code="NOT_FOUND")

    async def _assert_can_view(self, project_id: uuid.UUID, user: User) -> None:
        await self._require_project(project_id)
        if user.role == UserRole.ADMIN.value:
            return
        if await self._projects.user_has_any_membership(project_id, user.id):
            return
        raise ForbiddenError("Access denied to this project", code="FORBIDDEN")

    async def _assert_can_write(self, project_id: uuid.UUID, user: User) -> None:
        await self._require_project(project_id)
        if user.role == UserRole.ADMIN.value:
            return
        if await self._projects.user_is_pi_member(
            project_id,
            user.id,
            pi_role_code=_PROJECT_PI_ROLE_CODE,
        ):
            return
        raise ForbiddenError(
            "Only admin or project PI can modify groups",
            code="FORBIDDEN",
        )

    async def create(
        self,
        project_id: uuid.UUID,
        body: GroupCreateIn,
        actor: User,
    ) -> GroupOut:
        await self._assert_can_write(project_id, actor)
        name = body.name.strip()
        if await self._groups.name_taken_ci(project_id, name, exclude_group_id=None):
            raise ConflictError(
                "Group name already in use in this project",
                code="GROUP_NAME_IN_USE",
            )
        row = ProjectGroup(
            id=uuid.uuid4(),
            project_id=project_id,
            name=name,
            description=body.description,
            is_active=body.is_active,
        )
        self._groups.add_group(row)
        await self._session.commit()
        await self._session.refresh(row)
        return self._to_out(row)

    async def list_for_project(
        self,
        project_id: uuid.UUID,
        viewer: User,
    ) -> GroupListResponse:
        await self._assert_can_view(project_id, viewer)
        rows = await self._groups.list_by_project(project_id)
        return GroupListResponse(groups=[self._to_out(r) for r in rows])

    async def patch(
        self,
        project_id: uuid.UUID,
        group_id: uuid.UUID,
        body: GroupPatchIn,
        actor: User,
    ) -> GroupOut:
        await self._assert_can_write(project_id, actor)
        row = await self._groups.get_by_id(project_id, group_id)
        if row is None:
            raise NotFoundError("Group not found", code="NOT_FOUND")
        data = body.model_dump(exclude_unset=True)
        if "name" in data and data["name"] is not None:
            new_name = str(data["name"]).strip()
            if await self._groups.name_taken_ci(
                project_id,
                new_name,
                exclude_group_id=group_id,
            ):
                raise ConflictError(
                    "Group name already in use in this project",
                    code="GROUP_NAME_IN_USE",
                )
            row.name = new_name
        if "description" in data:
            row.description = data["description"]
        if "is_active" in data and data["is_active"] is not None:
            row.is_active = bool(data["is_active"])
        await self._session.commit()
        await self._session.refresh(row)
        return self._to_out(row)

    async def delete(
        self,
        project_id: uuid.UUID,
        group_id: uuid.UUID,
        actor: User,
    ) -> None:
        await self._assert_can_write(project_id, actor)
        row = await self._groups.get_by_id(project_id, group_id)
        if row is None:
            raise NotFoundError("Group not found", code="NOT_FOUND")
        n = await self._groups.count_active_enrollments_for_group(group_id)
        if n > 0:
            raise ConflictError(
                "Cannot delete group with active enrollments",
                code="GROUP_HAS_ACTIVE_ENROLLMENTS",
            )
        await self._groups.delete_group(row)
        await self._session.commit()
