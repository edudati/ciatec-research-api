"""Business logic for participant enrollments."""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.enums import ProjectStatus, UserRole
from src.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnprocessableEntityError,
    ValidationError,
)
from src.models.participant_enrollment import ParticipantEnrollment
from src.models.participant_profile import ParticipantProfile
from src.models.user import User
from src.modules.participants.repository import ParticipantsRepository
from src.modules.project_enrollments.repository import ProjectEnrollmentsRepository
from src.modules.project_enrollments.schemas import (
    EnrollmentCreateIn,
    EnrollmentDeleteIn,
    EnrollmentListResponse,
    EnrollmentOut,
    EnrollmentPatchIn,
)
from src.modules.project_groups.repository import ProjectGroupsRepository
from src.modules.projects.repository import ProjectsRepository
from src.modules.timeline.dispatcher import publish_timeline_event
from src.modules.timeline.job_payload import TimelineEventJobPayload
from src.modules.vocabulary.repository import (
    ENROLLMENT_ROLE_SCHEME_CODE,
    ENROLLMENT_STATUS_SCHEME_CODE,
    TIMELINE_EVENT_TYPE_SCHEME_CODE,
    VocabularyRepository,
)

_PI_ROLE = "PI"
_TIMELINE_EVENT_CODE = "ENROLLMENT"
_SOURCE_TYPE = "ParticipantEnrollment"
_WITHDRAWN_STATUS = "WITHDRAWN"


class ProjectEnrollmentsService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ProjectEnrollmentsRepository(session)
        self._projects = ProjectsRepository(session)
        self._groups = ProjectGroupsRepository(session)
        self._participants = ParticipantsRepository(session)
        self._vocab = VocabularyRepository(session)

    @staticmethod
    def _dt_iso(dt: datetime) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.isoformat()

    @staticmethod
    def _naive_utc(dt: datetime) -> datetime:
        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)

    def _to_out(self, row: ParticipantEnrollment) -> EnrollmentOut:
        prof = row.participant_profile
        return EnrollmentOut(
            id=str(row.id),
            participant_profile_id=str(row.participant_profile_id),
            user_id=str(prof.user_id),
            group_id=str(row.group_id) if row.group_id is not None else None,
            role=row.role,
            status=row.status,
            enrolled_at=self._dt_iso(row.enrolled_at),
            exited_at=self._dt_iso(row.exited_at)
            if row.exited_at is not None
            else None,
            exit_reason=row.exit_reason,
            enrolled_by=str(row.enrolled_by) if row.enrolled_by is not None else None,
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
            "Only admin or project PI can modify enrollments",
            code="FORBIDDEN",
        )

    async def _validate_enrollment_role(self, role: str) -> None:
        ok = await self._vocab.is_active_term_in_scheme(
            scheme_code=ENROLLMENT_ROLE_SCHEME_CODE,
            term_code=role,
        )
        if not ok:
            raise ValidationError(
                "Invalid enrollment role",
                code="INVALID_ENROLLMENT_ROLE",
            )

    async def _validate_enrollment_status(self, status: str) -> None:
        ok = await self._vocab.is_active_term_in_scheme(
            scheme_code=ENROLLMENT_STATUS_SCHEME_CODE,
            term_code=status,
        )
        if not ok:
            raise ValidationError(
                "Invalid enrollment status",
                code="INVALID_ENROLLMENT_STATUS",
            )

    async def _validate_timeline_event_type(self, code: str) -> None:
        ok = await self._vocab.is_active_term_in_scheme(
            scheme_code=TIMELINE_EVENT_TYPE_SCHEME_CODE,
            term_code=code,
        )
        if not ok:
            raise ValidationError(
                "Enrollment timeline event type is not configured",
                code="VALIDATION_ERROR",
            )

    async def _ensure_participant_profile(
        self, user_id: uuid.UUID
    ) -> ParticipantProfile:
        existing = await self._participants.get_active_by_user_id(user_id)
        if existing is not None:
            return existing
        row = ParticipantProfile(
            id=uuid.uuid4(),
            user_id=user_id,
        )
        self._participants.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def _assert_project_allows_enrollment(self, project_id: uuid.UUID) -> None:
        project = await self._projects.get_project_public(project_id)
        if project is None:
            raise NotFoundError("Project not found", code="NOT_FOUND")
        if project.status == ProjectStatus.DRAFT.value:
            raise UnprocessableEntityError(
                "Cannot enroll participants in a DRAFT project",
                code="ENROLLMENT_PROJECT_DRAFT",
            )

    async def _assert_group_in_project(
        self,
        project_id: uuid.UUID,
        group_id: uuid.UUID,
    ) -> None:
        g = await self._groups.get_by_id(project_id, group_id)
        if g is None:
            raise ValidationError(
                "Group does not belong to this project",
                code="INVALID_GROUP",
            )

    def _enrollment_timeline_payload(
        self,
        *,
        enrollment: ParticipantEnrollment,
        executor_id: uuid.UUID | None,
        occurred_at: datetime,
        context: dict[str, Any],
    ) -> TimelineEventJobPayload:
        return TimelineEventJobPayload(
            id=uuid.uuid4(),
            participant_profile_id=enrollment.participant_profile_id,
            project_id=enrollment.project_id,
            enrollment_id=enrollment.id,
            executor_id=executor_id,
            event_type=_TIMELINE_EVENT_CODE,
            source_type=_SOURCE_TYPE,
            source_id=str(enrollment.id),
            occurred_at=self._dt_iso(occurred_at),
            context=context,
        )

    async def create(
        self,
        project_id: uuid.UUID,
        body: EnrollmentCreateIn,
        actor: User,
    ) -> EnrollmentOut:
        await self._assert_can_write(project_id, actor)
        await self._assert_project_allows_enrollment(project_id)
        if not await self._projects.get_user_active(body.user_id):
            raise NotFoundError("User not found", code="NOT_FOUND")
        await self._validate_enrollment_role(body.role)
        status = body.status if body.status is not None else "ACTIVE"
        await self._validate_enrollment_status(status)
        await self._validate_timeline_event_type(_TIMELINE_EVENT_CODE)

        profile = await self._ensure_participant_profile(body.user_id)
        if await self._repo.exists_for_project_and_profile(project_id, profile.id):
            raise ConflictError(
                "Participant is already enrolled in this project",
                code="ENROLLMENT_DUPLICATE",
            )
        if body.group_id is not None:
            await self._assert_group_in_project(project_id, body.group_id)

        enrolled_at = (
            self._naive_utc(body.enrolled_at)
            if body.enrolled_at is not None
            else datetime.now(UTC)
        )
        row = ParticipantEnrollment(
            id=uuid.uuid4(),
            project_id=project_id,
            participant_profile_id=profile.id,
            group_id=body.group_id,
            role=body.role,
            status=status,
            enrolled_at=enrolled_at,
            exited_at=None,
            exit_reason=None,
            enrolled_by=actor.id,
        )
        self._repo.add_enrollment(row)
        await self._session.flush()
        ctx: dict[str, Any] = {
            "role": row.role,
            "status": row.status,
            "groupId": str(row.group_id) if row.group_id else None,
        }
        payload = self._enrollment_timeline_payload(
            enrollment=row,
            executor_id=actor.id,
            occurred_at=enrolled_at,
            context=ctx,
        )
        await self._session.commit()
        await publish_timeline_event(payload)
        loaded = await self._repo.get_by_project_and_id(project_id, row.id)
        assert loaded is not None
        return self._to_out(loaded)

    async def list_for_project(
        self,
        project_id: uuid.UUID,
        viewer: User,
    ) -> EnrollmentListResponse:
        await self._assert_can_view(project_id, viewer)
        rows = await self._repo.list_by_project(project_id)
        return EnrollmentListResponse(enrollments=[self._to_out(r) for r in rows])

    async def get_one(
        self,
        project_id: uuid.UUID,
        enrollment_id: uuid.UUID,
        viewer: User,
    ) -> EnrollmentOut:
        await self._assert_can_view(project_id, viewer)
        row = await self._repo.get_by_project_and_id(project_id, enrollment_id)
        if row is None:
            raise NotFoundError("Enrollment not found", code="NOT_FOUND")
        return self._to_out(row)

    async def patch(
        self,
        project_id: uuid.UUID,
        enrollment_id: uuid.UUID,
        body: EnrollmentPatchIn,
        actor: User,
    ) -> EnrollmentOut:
        await self._assert_can_write(project_id, actor)
        row = await self._repo.get_by_project_and_id(project_id, enrollment_id)
        if row is None:
            raise NotFoundError("Enrollment not found", code="NOT_FOUND")
        data = body.model_dump(exclude_unset=True)
        if "group_id" in data:
            gid = data["group_id"]
            if gid is not None:
                await self._assert_group_in_project(project_id, gid)
            row.group_id = gid
        if "status" in data and data["status"] is not None:
            await self._validate_enrollment_status(str(data["status"]))
            row.status = str(data["status"])
        if "enrolled_at" in data and data["enrolled_at"] is not None:
            row.enrolled_at = self._naive_utc(data["enrolled_at"])
        if "exited_at" in data:
            row.exited_at = (
                self._naive_utc(data["exited_at"])
                if data["exited_at"] is not None
                else None
            )
        await self._session.commit()
        await self._session.refresh(row)
        loaded = await self._repo.get_by_project_and_id(project_id, enrollment_id)
        assert loaded is not None
        return self._to_out(loaded)

    async def record_exit(
        self,
        project_id: uuid.UUID,
        enrollment_id: uuid.UUID,
        body: EnrollmentDeleteIn,
        actor: User,
    ) -> None:
        await self._assert_can_write(project_id, actor)
        row = await self._repo.get_by_project_and_id(project_id, enrollment_id)
        if row is None:
            raise NotFoundError("Enrollment not found", code="NOT_FOUND")
        if row.exited_at is not None:
            raise ConflictError(
                "Enrollment is already closed",
                code="ENROLLMENT_ALREADY_EXITED",
            )
        await self._validate_enrollment_status(_WITHDRAWN_STATUS)
        now = datetime.now(UTC)
        row.exited_at = now
        row.exit_reason = body.exit_reason.strip()
        row.status = _WITHDRAWN_STATUS
        await self._session.commit()
