"""Business logic for project questionnaire responses."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Settings
from src.core.enums import UserRole
from src.core.exceptions import (
    ConflictError,
    ForbiddenError,
    GoneError,
    NotFoundError,
    UnprocessableEntityError,
    ValidationError,
)
from src.models.question_answer import QuestionAnswer
from src.models.question_item import QuestionItem
from src.models.questionnaire_response import QuestionnaireResponse
from src.models.self_report_token import SelfReportToken
from src.models.user import User
from src.modules.instruments.schemas_questionnaires import QuestionItemOut
from src.modules.project_questionnaires.answer_value import normalize_answer_value
from src.modules.project_questionnaires.repository import (
    QuestionnaireResponsesRepository,
)
from src.modules.project_questionnaires.schemas import (
    QuestionAnswerOut,
    QuestionnaireAnswerSubmitIn,
    QuestionnaireResponseCreateIn,
    QuestionnaireResponseDetailOut,
    QuestionnaireResponsesListResponse,
    QuestionnaireResponseSummaryOut,
    SelfReportSendLinkOut,
)
from src.modules.projects.repository import ProjectsRepository
from src.modules.self_report.schemas import (
    SelfReportSessionOut,
    SelfReportSubmitIn,
    SelfReportSubmitResponseOut,
    SelfReportTemplateBriefOut,
)
from src.modules.timeline.dispatcher import publish_timeline_event
from src.modules.timeline.job_payload import TimelineEventJobPayload
from src.modules.vocabulary.repository import (
    TIMELINE_EVENT_TYPE_SCHEME_CODE,
    VocabularyRepository,
)

_TIMELINE_QUESTIONNAIRE = "QUESTIONNAIRE"
_SOURCE_TYPE = "QuestionnaireResponse"


class QuestionnaireResponsesService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = QuestionnaireResponsesRepository(session)
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

    def _answer_to_out(self, row: QuestionAnswer) -> QuestionAnswerOut:
        return QuestionAnswerOut(
            id=str(row.id),
            question_item_id=str(row.question_item_id),
            value=row.value,
            created_at=self._dt_iso(row.created_at),
            updated_at=self._dt_iso(row.updated_at),
        )

    def _response_to_summary(
        self,
        row: QuestionnaireResponse,
    ) -> QuestionnaireResponseSummaryOut:
        return QuestionnaireResponseSummaryOut(
            id=str(row.id),
            project_id=str(row.project_id),
            participant_profile_id=str(row.participant_profile_id),
            questionnaire_template_id=str(row.questionnaire_template_id),
            executor_id=str(row.executor_id) if row.executor_id is not None else None,
            status=row.status,
            completed_at=self._dt_iso(row.completed_at) if row.completed_at else None,
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

    async def _validate_timeline_questionnaire_type(self) -> None:
        ok = await self._vocab.is_active_term_in_scheme(
            scheme_code=TIMELINE_EVENT_TYPE_SCHEME_CODE,
            term_code=_TIMELINE_QUESTIONNAIRE,
        )
        if not ok:
            raise ValidationError(
                "Questionnaire timeline event type is not configured",
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

    async def _finalize_questionnaire_completion(
        self,
        *,
        project_id: uuid.UUID,
        row: QuestionnaireResponse,
        completed_at_aware: datetime,
    ) -> TimelineEventJobPayload:
        await self._validate_timeline_questionnaire_type()
        enrollment_id = await self._repo.get_active_enrollment_id(
            project_id=project_id,
            participant_profile_id=row.participant_profile_id,
        )
        if enrollment_id is None:
            raise NotFoundError(
                "Participant not enrolled in this project",
                code="NOT_FOUND",
            )
        row.completed_at = self._naive_utc(completed_at_aware)
        row.status = "COMPLETED"
        tmpl = await self._repo.get_questionnaire_template(
            row.questionnaire_template_id,
        )
        assert tmpl is not None
        return TimelineEventJobPayload(
            id=uuid.uuid4(),
            participant_profile_id=row.participant_profile_id,
            project_id=project_id,
            enrollment_id=enrollment_id,
            executor_id=row.executor_id,
            event_type=_TIMELINE_QUESTIONNAIRE,
            source_type=_SOURCE_TYPE,
            source_id=str(row.id),
            occurred_at=self._dt_iso(completed_at_aware),
            context={
                "templateId": str(row.questionnaire_template_id),
                "templateCode": tmpl.code,
            },
        )

    def _question_item_to_out(self, row: QuestionItem) -> QuestionItemOut:
        opts = dict(row.item_options) if row.item_options is not None else None
        return QuestionItemOut(
            id=str(row.id),
            questionnaire_template_id=str(row.questionnaire_template_id),
            code=row.code,
            label=row.label,
            item_type=row.item_type,
            display_order=row.display_order,
            options=opts,
            is_required=row.is_required,
            created_at=self._dt_iso(row.created_at),
            updated_at=self._dt_iso(row.updated_at),
        )

    def _assert_self_report_token_active(
        self,
        tok: SelfReportToken,
        *,
        now: datetime,
    ) -> QuestionnaireResponse:
        if tok.used_at is not None:
            raise ConflictError(
                "Self-report token has already been used",
                code="SELF_REPORT_TOKEN_USED",
            )
        if now > tok.expires_at:
            raise GoneError(
                "Self-report link has expired",
                code="SELF_REPORT_TOKEN_EXPIRED",
            )
        resp = tok.questionnaire_response
        if resp.status == "COMPLETED":
            raise ConflictError(
                "Questionnaire response is already completed",
                code="QUESTIONNAIRE_ALREADY_COMPLETED",
            )
        return resp

    async def create(
        self,
        project_id: uuid.UUID,
        body: QuestionnaireResponseCreateIn,
        actor: User,
    ) -> QuestionnaireResponseSummaryOut:
        await self._assert_can_write(project_id, actor)

        profile_id = body.participant_profile_id
        template_id = body.template_id

        enrollment_id = await self._repo.get_active_enrollment_id(
            project_id=project_id,
            participant_profile_id=profile_id,
        )
        if enrollment_id is None:
            raise NotFoundError(
                "Participant not enrolled in this project",
                code="NOT_FOUND",
            )

        template = await self._repo.get_questionnaire_template(template_id)
        if template is None:
            raise NotFoundError("Questionnaire template not found", code="NOT_FOUND")
        if not template.is_active:
            raise UnprocessableEntityError(
                "Questionnaire template is not active",
                code="QUESTIONNAIRE_TEMPLATE_INACTIVE",
            )

        if template.self_report:
            if body.executor_id is not None:
                raise UnprocessableEntityError(
                    "Executor must be omitted for self-report questionnaires",
                    code="QUESTIONNAIRE_EXECUTOR_NOT_ALLOWED",
                )
            executor_uuid: uuid.UUID | None = None
        else:
            if body.executor_id is None:
                raise UnprocessableEntityError(
                    "Executor is required for mediated questionnaires",
                    code="QUESTIONNAIRE_EXECUTOR_REQUIRED",
                )
            executor_uuid = body.executor_id
            await self._assert_executor_is_member(project_id, executor_uuid)

        row = QuestionnaireResponse(
            id=uuid.uuid4(),
            project_id=project_id,
            participant_profile_id=profile_id,
            questionnaire_template_id=template_id,
            executor_id=executor_uuid,
            status="PENDING",
            completed_at=None,
        )
        self._repo.add_response(row)
        await self._session.commit()
        await self._session.refresh(row)
        return self._response_to_summary(row)

    async def list_for_project(
        self,
        project_id: uuid.UUID,
        viewer: User,
    ) -> QuestionnaireResponsesListResponse:
        await self._assert_can_view(project_id, viewer)
        rows = await self._repo.list_by_project(project_id)
        return QuestionnaireResponsesListResponse(
            responses=[self._response_to_summary(r) for r in rows],
        )

    async def get_one(
        self,
        project_id: uuid.UUID,
        response_id: uuid.UUID,
        viewer: User,
    ) -> QuestionnaireResponseDetailOut:
        await self._assert_can_view(project_id, viewer)
        row = await self._repo.get_by_project_and_id(
            project_id,
            response_id,
            with_answers=True,
        )
        if row is None:
            raise NotFoundError("Questionnaire response not found", code="NOT_FOUND")
        summary = self._response_to_summary(row)
        answers_sorted = sorted(row.answers, key=lambda a: a.created_at)
        return QuestionnaireResponseDetailOut(
            **summary.model_dump(by_alias=True),
            answers=[self._answer_to_out(a) for a in answers_sorted],
        )

    async def submit_answer(
        self,
        project_id: uuid.UUID,
        response_id: uuid.UUID,
        body: QuestionnaireAnswerSubmitIn,
        actor: User,
    ) -> QuestionnaireResponseDetailOut:
        await self._assert_can_write(project_id, actor)
        row = await self._repo.get_by_project_and_id(
            project_id,
            response_id,
            with_answers=True,
        )
        if row is None:
            raise NotFoundError("Questionnaire response not found", code="NOT_FOUND")

        if row.status == "COMPLETED":
            if body.mark_completed:
                raise UnprocessableEntityError(
                    "Questionnaire response is already completed",
                    code="QUESTIONNAIRE_ALREADY_COMPLETED",
                )
            raise UnprocessableEntityError(
                "Cannot add answers to a completed questionnaire",
                code="QUESTIONNAIRE_ALREADY_COMPLETED",
            )

        if await self._repo.has_answer_for_item(
            response_id=response_id,
            item_id=body.question_item_id,
        ):
            raise ConflictError(
                "An answer already exists for this question item",
                code="QUESTION_ANSWER_DUPLICATE",
            )

        item = await self._repo.get_question_item_for_template(
            template_id=row.questionnaire_template_id,
            item_id=body.question_item_id,
        )
        if item is None:
            raise NotFoundError("Question item not found", code="NOT_FOUND")

        if body.mark_completed:
            required_ids = await self._repo.list_required_item_ids(
                row.questionnaire_template_id,
            )
            for rid in required_ids:
                if rid == body.question_item_id:
                    continue
                if not await self._repo.has_answer_for_item(
                    response_id=row.id,
                    item_id=rid,
                ):
                    raise UnprocessableEntityError(
                        "Not all required questions have been answered",
                        code="QUESTIONNAIRE_INCOMPLETE",
                    )

        stored_value = normalize_answer_value(body.value)
        ans = QuestionAnswer(
            id=uuid.uuid4(),
            questionnaire_response_id=row.id,
            question_item_id=body.question_item_id,
            value=stored_value,
        )
        self._repo.add_answer(ans)

        if row.status == "PENDING":
            row.status = "IN_PROGRESS"

        timeline_after: TimelineEventJobPayload | None = None
        if body.mark_completed:
            completed_at = datetime.now(UTC)
            timeline_after = await self._finalize_questionnaire_completion(
                project_id=project_id,
                row=row,
                completed_at_aware=completed_at,
            )

        await self._session.commit()
        if timeline_after is not None:
            await publish_timeline_event(timeline_after)
        refreshed = await self._repo.get_by_project_and_id(
            project_id,
            response_id,
            with_answers=True,
        )
        assert refreshed is not None
        summary = self._response_to_summary(refreshed)
        answers_sorted = sorted(refreshed.answers, key=lambda a: a.created_at)
        return QuestionnaireResponseDetailOut(
            **summary.model_dump(by_alias=True),
            answers=[self._answer_to_out(a) for a in answers_sorted],
        )

    async def send_self_report_link(
        self,
        project_id: uuid.UUID,
        response_id: uuid.UUID,
        actor: User,
        settings: Settings,
    ) -> SelfReportSendLinkOut:
        await self._assert_can_write(project_id, actor)
        row = await self._repo.get_by_project_and_id(
            project_id,
            response_id,
            with_answers=False,
        )
        if row is None:
            raise NotFoundError("Questionnaire response not found", code="NOT_FOUND")
        if row.status == "COMPLETED":
            raise ConflictError(
                "Questionnaire response is already completed",
                code="QUESTIONNAIRE_ALREADY_COMPLETED",
            )
        template = await self._repo.get_questionnaire_template(
            row.questionnaire_template_id,
        )
        assert template is not None
        if not template.self_report:
            raise UnprocessableEntityError(
                "Questionnaire template is not self-report",
                code="QUESTIONNAIRE_NOT_SELF_REPORT",
            )
        token = uuid.uuid4()
        expires_at = datetime.now(UTC) + timedelta(
            seconds=settings.self_report_token_ttl_seconds,
        )
        await self._repo.upsert_self_report_token(
            response_id=row.id,
            token=token,
            expires_at=expires_at,
        )
        await self._session.commit()
        fill_url: str | None = None
        if settings.app_url:
            base = settings.app_url.rstrip("/")
            fill_url = f"{base}/api/v1/self-report/{token}"
        return SelfReportSendLinkOut(
            token=str(token),
            expires_at=self._dt_iso(expires_at),
            fill_url=fill_url,
        )

    async def get_self_report_public(
        self,
        token: uuid.UUID,
    ) -> SelfReportSessionOut:
        tok = await self._repo.get_self_report_token_bundle(token)
        if tok is None:
            raise NotFoundError("Self-report token not found", code="NOT_FOUND")
        now = datetime.now(UTC)
        resp = self._assert_self_report_token_active(tok, now=now)
        tmpl = resp.template
        items_sorted = sorted(tmpl.items, key=lambda i: i.display_order)
        answers_sorted = sorted(resp.answers, key=lambda a: a.created_at)
        return SelfReportSessionOut(
            expires_at=self._dt_iso(tok.expires_at),
            response_status=resp.status,
            template=SelfReportTemplateBriefOut(code=tmpl.code, name=tmpl.name),
            items=[self._question_item_to_out(i) for i in items_sorted],
            answers=[self._answer_to_out(a) for a in answers_sorted],
        )

    async def submit_self_report_public(
        self,
        token: uuid.UUID,
        body: SelfReportSubmitIn,
    ) -> SelfReportSubmitResponseOut:
        tok = await self._repo.get_self_report_token_bundle(token)
        if tok is None:
            raise NotFoundError("Self-report token not found", code="NOT_FOUND")
        now = datetime.now(UTC)
        resp = self._assert_self_report_token_active(tok, now=now)
        tmpl = resp.template
        template_item_ids = {i.id for i in tmpl.items}
        required_ids = {i.id for i in tmpl.items if i.is_required}
        pair_ids = [a.question_item_id for a in body.answers]
        if len(pair_ids) != len(set(pair_ids)):
            raise UnprocessableEntityError(
                "Duplicate question items in submission",
                code="SELF_REPORT_ANSWERS_DUPLICATE",
            )
        submitted_ids = set(pair_ids)
        if not required_ids.issubset(submitted_ids):
            raise UnprocessableEntityError(
                "Not all required questions have been answered",
                code="QUESTIONNAIRE_INCOMPLETE",
            )
        for pair in body.answers:
            if pair.question_item_id not in template_item_ids:
                raise UnprocessableEntityError(
                    "Unknown question item for this questionnaire",
                    code="QUESTIONNAIRE_ITEM_INVALID",
                )
        by_item: dict[uuid.UUID, QuestionAnswer] = {
            a.question_item_id: a for a in resp.answers
        }
        for pair in body.answers:
            stored = normalize_answer_value(pair.value)
            existing = by_item.get(pair.question_item_id)
            if existing is not None:
                existing.value = stored
            else:
                ans = QuestionAnswer(
                    id=uuid.uuid4(),
                    questionnaire_response_id=resp.id,
                    question_item_id=pair.question_item_id,
                    value=stored,
                )
                self._repo.add_answer(ans)
                by_item[pair.question_item_id] = ans
        if resp.status == "PENDING":
            resp.status = "IN_PROGRESS"
        timeline_payload = await self._finalize_questionnaire_completion(
            project_id=resp.project_id,
            row=resp,
            completed_at_aware=now,
        )
        tok.used_at = self._naive_utc(now)
        await self._session.commit()
        await publish_timeline_event(timeline_payload)
        assert resp.completed_at is not None
        return SelfReportSubmitResponseOut(
            status=resp.status,
            completed_at=self._dt_iso(resp.completed_at),
        )
