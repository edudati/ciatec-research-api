"""Business logic for project members."""

import uuid
from datetime import UTC, date, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.enums import ProjectStatus, UserRole
from src.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnprocessableEntityError,
    ValidationError,
)
from src.models.project import ProjectMember
from src.models.user import User
from src.modules.project_members.repository import ProjectMembersRepository
from src.modules.project_members.schemas import (
    ProjectMemberCreateIn,
    ProjectMemberListResponse,
    ProjectMemberOut,
    ProjectMemberPatchIn,
)
from src.modules.projects.repository import ProjectsRepository
from src.modules.vocabulary.repository import (
    PROJECT_MEMBER_ROLE_SCHEME_CODE,
    VocabularyRepository,
)

_PI_ROLE = "PI"


class ProjectMembersService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._members = ProjectMembersRepository(session)
        self._projects = ProjectsRepository(session)
        self._vocab = VocabularyRepository(session)

    @staticmethod
    def _dt_iso(dt: datetime) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.isoformat()

    @staticmethod
    def _date_iso(d: date | None) -> str | None:
        return d.isoformat() if d is not None else None

    def _to_out(self, row: ProjectMember) -> ProjectMemberOut:
        return ProjectMemberOut(
            id=str(row.id),
            user_id=str(row.user_id),
            role=row.role,
            start_date=self._date_iso(row.start_date) or "",
            end_date=self._date_iso(row.end_date),
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
            pi_role_code=_PI_ROLE,
        ):
            return
        raise ForbiddenError(
            "Only admin or project PI can modify members",
            code="FORBIDDEN",
        )

    async def _validate_role_vocab(self, role: str) -> None:
        ok = await self._vocab.is_active_term_in_scheme(
            scheme_code=PROJECT_MEMBER_ROLE_SCHEME_CODE,
            term_code=role,
        )
        if not ok:
            raise ValidationError(
                "Invalid project member role",
                code="INVALID_PROJECT_MEMBER_ROLE",
            )

    async def _assert_dates(self, start: date, end: date | None) -> None:
        if end is not None and end < start:
            raise ValidationError(
                "endDate must be on or after startDate",
                code="VALIDATION_ERROR",
            )

    async def _would_remove_last_pi_on_active(
        self,
        project_id: uuid.UUID,
        *,
        current_role: str,
        new_role: str | None,
    ) -> bool:
        project = await self._projects.get_project_public(project_id)
        if project is None:
            return False
        if project.status != ProjectStatus.ACTIVE.value:
            return False
        if current_role != _PI_ROLE:
            return False
        if new_role is None or new_role == _PI_ROLE:
            return False
        n = await self._members.count_pi_members(project_id, pi_role_code=_PI_ROLE)
        return n <= 1

    async def _would_delete_last_pi_on_active(
        self,
        project_id: uuid.UUID,
        member_role: str,
    ) -> bool:
        project = await self._projects.get_project_public(project_id)
        if project is None:
            return False
        if project.status != ProjectStatus.ACTIVE.value:
            return False
        if member_role != _PI_ROLE:
            return False
        n = await self._members.count_pi_members(project_id, pi_role_code=_PI_ROLE)
        return n <= 1

    async def create(
        self,
        project_id: uuid.UUID,
        body: ProjectMemberCreateIn,
        actor: User,
    ) -> ProjectMemberOut:
        await self._assert_can_write(project_id, actor)
        await self._validate_role_vocab(body.role)
        await self._assert_dates(body.start_date, body.end_date)
        if await self._projects.user_has_any_membership(project_id, body.user_id):
            raise ConflictError(
                "User is already a member of this project",
                code="PROJECT_MEMBER_DUPLICATE",
            )
        if await self._projects.get_user_active(body.user_id) is None:
            raise NotFoundError("User not found", code="NOT_FOUND")
        row = ProjectMember(
            id=uuid.uuid4(),
            project_id=project_id,
            user_id=body.user_id,
            role=body.role,
            start_date=body.start_date,
            end_date=body.end_date,
        )
        self._members.add_member(row)
        await self._session.commit()
        await self._session.refresh(row)
        return self._to_out(row)

    async def list_for_project(
        self,
        project_id: uuid.UUID,
        viewer: User,
    ) -> ProjectMemberListResponse:
        await self._assert_can_view(project_id, viewer)
        rows = await self._members.list_by_project(project_id)
        return ProjectMemberListResponse(members=[self._to_out(r) for r in rows])

    async def patch(
        self,
        project_id: uuid.UUID,
        member_id: uuid.UUID,
        body: ProjectMemberPatchIn,
        actor: User,
    ) -> ProjectMemberOut:
        await self._assert_can_write(project_id, actor)
        row = await self._members.get_by_id(project_id, member_id)
        if row is None:
            raise NotFoundError("Project member not found", code="NOT_FOUND")
        data = body.model_dump(exclude_unset=True)
        if "role" in data and data["role"] is not None:
            await self._validate_role_vocab(str(data["role"]))
            if await self._would_remove_last_pi_on_active(
                project_id,
                current_role=row.role,
                new_role=str(data["role"]),
            ):
                raise UnprocessableEntityError(
                    "Cannot remove the last PI from an ACTIVE project",
                    code="LAST_PI_REMOVAL",
                )
            row.role = str(data["role"])
        if "start_date" in data:
            row.start_date = data["start_date"]
        if "end_date" in data:
            row.end_date = data["end_date"]
        await self._assert_dates(row.start_date, row.end_date)
        await self._session.commit()
        await self._session.refresh(row)
        return self._to_out(row)

    async def delete(
        self,
        project_id: uuid.UUID,
        member_id: uuid.UUID,
        actor: User,
    ) -> None:
        await self._assert_can_write(project_id, actor)
        row = await self._members.get_by_id(project_id, member_id)
        if row is None:
            raise NotFoundError("Project member not found", code="NOT_FOUND")
        if await self._would_delete_last_pi_on_active(project_id, row.role):
            raise UnprocessableEntityError(
                "Cannot remove the last PI from an ACTIVE project",
                code="LAST_PI_REMOVAL",
            )
        await self._members.delete_member(row)
        await self._session.commit()
