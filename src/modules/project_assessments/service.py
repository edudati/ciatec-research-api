"""Business logic for project assessment records."""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.enums import UserRole
from src.core.exceptions import (
    ForbiddenError,
    NotFoundError,
    UnprocessableEntityError,
    ValidationError,
)
from src.models.assessment_record import AssessmentRecord
from src.models.user import User
from src.modules.project_assessments.repository import AssessmentRecordsRepository
from src.modules.project_assessments.schemas import (
    AssessmentRecordCreateIn,
    AssessmentRecordOut,
    AssessmentRecordPatchIn,
    AssessmentRecordsListResponse,
)
from src.modules.projects.repository import ProjectsRepository
from src.modules.timeline.dispatcher import publish_timeline_event
from src.modules.timeline.job_payload import TimelineEventJobPayload
from src.modules.vocabulary.repository import (
    TIMELINE_EVENT_TYPE_SCHEME_CODE,
    VocabularyRepository,
)

_TIMELINE_ASSESSMENT = "ASSESSMENT"
_SOURCE_TYPE = "AssessmentRecord"


class AssessmentRecordsService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = AssessmentRecordsRepository(session)
        self._projects = ProjectsRepository(session)
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

    def _to_out(self, row: AssessmentRecord) -> AssessmentRecordOut:
        score_s = str(row.score) if row.score is not None else None
        return AssessmentRecordOut(
            id=str(row.id),
            project_id=str(row.project_id),
            participant_profile_id=str(row.participant_profile_id),
            template_id=str(row.template_id),
            executor_id=str(row.executor_id),
            performed_at=self._dt_iso(row.performed_at),
            score=score_s,
            data=dict(row.record_data),
            notes=row.notes,
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
        await self._assert_can_view(project_id, user)

    async def _validate_timeline_assessment_type(self) -> None:
        ok = await self._vocab.is_active_term_in_scheme(
            scheme_code=TIMELINE_EVENT_TYPE_SCHEME_CODE,
            term_code=_TIMELINE_ASSESSMENT,
        )
        if not ok:
            raise ValidationError(
                "Assessment timeline event type is not configured",
                code="VALIDATION_ERROR",
            )

    async def _assert_executor_is_member(
        self,
        project_id: uuid.UUID,
        executor_id: uuid.UUID,
    ) -> None:
        if not await self._projects.user_has_any_membership(project_id, executor_id):
            raise ForbiddenError(
                "Executor is not a member of this project",
                code="EXECUTOR_NOT_PROJECT_MEMBER",
            )

    async def create(
        self,
        project_id: uuid.UUID,
        body: AssessmentRecordCreateIn,
        actor: User,
    ) -> AssessmentRecordOut:
        await self._assert_can_write(project_id, actor)
        await self._validate_timeline_assessment_type()

        profile_id = body.participant_profile_id
        template_id = body.template_id
        executor_id = body.executor_id

        enrollment_id = await self._repo.get_active_enrollment_id(
            project_id=project_id,
            participant_profile_id=profile_id,
        )
        if enrollment_id is None:
            raise NotFoundError(
                "Participant not enrolled in this project",
                code="NOT_FOUND",
            )

        template = await self._repo.get_assessment_template(template_id)
        if template is None:
            raise NotFoundError("Assessment template not found", code="NOT_FOUND")
        if not template.is_active:
            raise UnprocessableEntityError(
                "Assessment template is not active",
                code="ASSESSMENT_TEMPLATE_INACTIVE",
            )

        await self._assert_executor_is_member(project_id, executor_id)

        row = AssessmentRecord(
            id=uuid.uuid4(),
            project_id=project_id,
            participant_profile_id=profile_id,
            template_id=template_id,
            executor_id=executor_id,
            performed_at=self._naive_utc(body.performed_at),
            score=body.score,
            record_data=body.data,
            notes=body.notes,
        )
        self._repo.add_record(row)
        await self._session.flush()
        await self._session.refresh(row)

        ctx: dict[str, Any] = {
            "templateId": str(template_id),
            "templateCode": template.code,
        }
        if body.score is not None:
            ctx["score"] = str(body.score)

        payload = TimelineEventJobPayload(
            id=uuid.uuid4(),
            participant_profile_id=profile_id,
            project_id=project_id,
            enrollment_id=enrollment_id,
            executor_id=executor_id,
            event_type=_TIMELINE_ASSESSMENT,
            source_type=_SOURCE_TYPE,
            source_id=str(row.id),
            occurred_at=self._dt_iso(row.performed_at),
            context=ctx,
        )
        await self._session.commit()
        await publish_timeline_event(payload)
        await self._session.refresh(row)
        return self._to_out(row)

    async def list_for_project(
        self,
        project_id: uuid.UUID,
        viewer: User,
    ) -> AssessmentRecordsListResponse:
        await self._assert_can_view(project_id, viewer)
        rows = await self._repo.list_by_project(project_id)
        return AssessmentRecordsListResponse(records=[self._to_out(r) for r in rows])

    async def get_one(
        self,
        project_id: uuid.UUID,
        record_id: uuid.UUID,
        viewer: User,
    ) -> AssessmentRecordOut:
        await self._assert_can_view(project_id, viewer)
        row = await self._repo.get_by_project_and_id(project_id, record_id)
        if row is None:
            raise NotFoundError("Assessment record not found", code="NOT_FOUND")
        return self._to_out(row)

    async def patch(
        self,
        project_id: uuid.UUID,
        record_id: uuid.UUID,
        body: AssessmentRecordPatchIn,
        actor: User,
    ) -> AssessmentRecordOut:
        await self._assert_can_write(project_id, actor)
        row = await self._repo.get_by_project_and_id(project_id, record_id)
        if row is None:
            raise NotFoundError("Assessment record not found", code="NOT_FOUND")
        if body.performed_at is not None:
            row.performed_at = self._naive_utc(body.performed_at)
        if body.score is not None:
            row.score = body.score
        if body.data is not None:
            row.record_data = body.data
        if body.notes is not None:
            row.notes = body.notes
        if "executor_id" in body.model_fields_set and body.executor_id is not None:
            ex = body.executor_id
            await self._assert_executor_is_member(project_id, ex)
            row.executor_id = ex
        await self._session.commit()
        await self._session.refresh(row)
        return self._to_out(row)
