"""Project business logic."""

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
from src.models.project import Project, ProjectMember
from src.models.user import User
from src.modules.projects.repository import ProjectsRepository
from src.modules.projects.schemas import (
    ProjectCreateIn,
    ProjectListResponse,
    ProjectOut,
    ProjectPatchIn,
)
from src.modules.vocabulary.repository import (
    PROJECT_MEMBER_ROLE_SCHEME_CODE,
    VocabularyRepository,
)

_PROJECT_PI_ROLE_CODE = "PI"


class ProjectsService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ProjectsRepository(session)
        self._vocab = VocabularyRepository(session)

    @staticmethod
    def _dt_iso(dt: datetime) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.isoformat()

    @staticmethod
    def _date_iso(d: date | None) -> str | None:
        return d.isoformat() if d is not None else None

    def _to_out(self, row: Project) -> ProjectOut:
        return ProjectOut(
            id=str(row.id),
            code=row.code,
            name=row.name,
            description=row.description,
            status=ProjectStatus(row.status),
            start_date=self._date_iso(row.start_date),
            end_date=self._date_iso(row.end_date),
            metadata=dict(row.project_metadata),
            created_at=self._dt_iso(row.created_at),
            updated_at=self._dt_iso(row.updated_at),
        )

    async def _ensure_pi_role_vocab(self) -> None:
        ok = await self._vocab.is_active_term_in_scheme(
            scheme_code=PROJECT_MEMBER_ROLE_SCHEME_CODE,
            term_code=_PROJECT_PI_ROLE_CODE,
        )
        if not ok:
            raise ValidationError(
                "PI role is not configured in vocabulary",
                code="VALIDATION_ERROR",
            )

    async def create(self, body: ProjectCreateIn) -> ProjectOut:
        code = body.code
        if await self._repo.code_taken(code, exclude_id=None):
            raise ConflictError(
                "Project code already in use",
                code="PROJECT_CODE_IN_USE",
            )
        if body.end_date is not None and body.start_date is not None:
            if body.end_date < body.start_date:
                raise ValidationError(
                    "endDate must be on or after startDate",
                    code="VALIDATION_ERROR",
                )
        meta = dict(body.metadata) if body.metadata else {}
        row = Project(
            id=uuid.uuid4(),
            code=code,
            name=body.name.strip(),
            description=body.description,
            status=ProjectStatus.DRAFT.value,
            start_date=body.start_date,
            end_date=body.end_date,
            project_metadata=meta,
        )
        self._repo.add_project(row)
        await self._session.flush()
        if body.pi_user_id is not None:
            await self._ensure_pi_role_vocab()
            target = await self._repo.get_user_active(body.pi_user_id)
            if target is None:
                raise NotFoundError("PI user not found", code="NOT_FOUND")
            if not await self._vocab.is_active_term_in_scheme(
                scheme_code=PROJECT_MEMBER_ROLE_SCHEME_CODE,
                term_code=_PROJECT_PI_ROLE_CODE,
            ):
                raise ValidationError("Invalid PI role", code="VALIDATION_ERROR")
            today = date.today()
            self._repo.add_member(
                ProjectMember(
                    id=uuid.uuid4(),
                    project_id=row.id,
                    user_id=body.pi_user_id,
                    role=_PROJECT_PI_ROLE_CODE,
                    start_date=today,
                    end_date=None,
                ),
            )
        await self._session.commit()
        await self._session.refresh(row)
        return self._to_out(row)

    @staticmethod
    def _assert_status_transition(old: ProjectStatus, new: ProjectStatus) -> None:
        if old == new:
            return
        if old == ProjectStatus.DRAFT and new == ProjectStatus.ACTIVE:
            return
        if old == ProjectStatus.ACTIVE and new in (
            ProjectStatus.COMPLETED,
            ProjectStatus.ARCHIVED,
        ):
            return
        raise ValidationError(
            f"Invalid status transition from {old.value} to {new.value}",
            code="VALIDATION_ERROR",
        )

    async def _ensure_can_activate(self, project_id: uuid.UUID) -> None:
        if not await self._repo.has_pi_member(
            project_id,
            pi_role_code=_PROJECT_PI_ROLE_CODE,
        ):
            raise UnprocessableEntityError(
                "Project must have a PI member before becoming ACTIVE",
                code="ACTIVE_REQUIRES_PI",
            )
        if not await self._vocab.is_active_term_in_scheme(
            scheme_code=PROJECT_MEMBER_ROLE_SCHEME_CODE,
            term_code=_PROJECT_PI_ROLE_CODE,
        ):
            raise UnprocessableEntityError(
                "PI role is not active in vocabulary",
                code="ACTIVE_REQUIRES_PI",
            )

    async def _assert_patch_auth(self, project_id: uuid.UUID, user: User) -> None:
        if user.role == UserRole.ADMIN.value:
            return
        if await self._repo.user_is_pi_member(
            project_id,
            user.id,
            pi_role_code=_PROJECT_PI_ROLE_CODE,
        ):
            return
        raise ForbiddenError(
            "Only admin or project PI can update this project",
            code="FORBIDDEN",
        )

    async def patch(
        self,
        project_id: uuid.UUID,
        body: ProjectPatchIn,
        actor: User,
    ) -> ProjectOut:
        row = await self._repo.get_project_public(project_id)
        if row is None:
            raise NotFoundError("Project not found", code="NOT_FOUND")
        await self._assert_patch_auth(project_id, actor)
        data = body.model_dump(exclude_unset=True)
        if "name" in data and data["name"] is not None:
            row.name = str(data["name"]).strip()
        if "description" in data:
            row.description = data["description"]
        if "start_date" in data:
            row.start_date = data["start_date"]
        if "end_date" in data:
            row.end_date = data["end_date"]
        if "metadata" in data and data["metadata"] is not None:
            row.project_metadata = dict(data["metadata"])
        if "status" in data and data["status"] is not None:
            raw = data["status"]
            new_s = raw if isinstance(raw, ProjectStatus) else ProjectStatus(str(raw))
            old_s = ProjectStatus(row.status)
            self._assert_status_transition(old_s, new_s)
            if new_s == ProjectStatus.ACTIVE:
                await self._ensure_can_activate(project_id)
            row.status = new_s.value
        if (
            row.start_date is not None
            and row.end_date is not None
            and row.end_date < row.start_date
        ):
            raise ValidationError(
                "endDate must be on or after startDate",
                code="VALIDATION_ERROR",
            )
        await self._session.commit()
        await self._session.refresh(row)
        return self._to_out(row)

    async def get(self, project_id: uuid.UUID, viewer: User) -> ProjectOut:
        row = await self._repo.get_project_public(project_id)
        if row is None:
            raise NotFoundError("Project not found", code="NOT_FOUND")
        if viewer.role == UserRole.ADMIN.value:
            return self._to_out(row)
        if await self._repo.user_has_any_membership(project_id, viewer.id):
            return self._to_out(row)
        raise ForbiddenError("Access denied to this project", code="FORBIDDEN")

    async def list_projects(
        self,
        *,
        user: User,
        page: int,
        page_size: int,
        q: str | None,
    ) -> ProjectListResponse:
        total = await self._repo.count_list_scope(user=user, q=q)
        rows = await self._repo.list_scope_page(
            user=user,
            q=q,
            page=page,
            page_size=page_size,
        )
        return ProjectListResponse(
            projects=[self._to_out(r) for r in rows],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def soft_delete(self, project_id: uuid.UUID) -> None:
        row = await self._repo.get_project_public(project_id)
        if row is None:
            return
        now = datetime.now(UTC)
        row.deleted_at = now
        await self._session.commit()
