"""Persistence for questionnaire responses, answers, and timeline inserts."""

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from src.models.participant_enrollment import ParticipantEnrollment
from src.models.question_answer import QuestionAnswer
from src.models.question_item import QuestionItem
from src.models.questionnaire_response import QuestionnaireResponse
from src.models.questionnaire_template import QuestionnaireTemplate
from src.models.self_report_token import SelfReportToken


class QuestionnaireResponsesRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_questionnaire_template(
        self,
        template_id: uuid.UUID,
    ) -> QuestionnaireTemplate | None:
        stmt = select(QuestionnaireTemplate).where(
            QuestionnaireTemplate.id == template_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_enrollment_id(
        self,
        *,
        project_id: uuid.UUID,
        participant_profile_id: uuid.UUID,
    ) -> uuid.UUID | None:
        stmt = (
            select(ParticipantEnrollment.id)
            .where(
                ParticipantEnrollment.project_id == project_id,
                ParticipantEnrollment.participant_profile_id == participant_profile_id,
                ParticipantEnrollment.status != "WITHDRAWN",
                ParticipantEnrollment.exited_at.is_(None),
            )
            .limit(1)
        )
        row = await self._session.execute(stmt)
        return row.scalar_one_or_none()

    async def get_question_item_for_template(
        self,
        *,
        template_id: uuid.UUID,
        item_id: uuid.UUID,
    ) -> QuestionItem | None:
        stmt = select(QuestionItem).where(
            QuestionItem.id == item_id,
            QuestionItem.questionnaire_template_id == template_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_required_item_ids(
        self,
        template_id: uuid.UUID,
    ) -> list[uuid.UUID]:
        stmt = select(QuestionItem.id).where(
            QuestionItem.questionnaire_template_id == template_id,
            QuestionItem.is_required.is_(True),
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def has_answer_for_item(
        self,
        *,
        response_id: uuid.UUID,
        item_id: uuid.UUID,
    ) -> bool:
        stmt = select(QuestionAnswer.id).where(
            QuestionAnswer.questionnaire_response_id == response_id,
            QuestionAnswer.question_item_id == item_id,
        )
        row = await self._session.execute(stmt)
        return row.scalar_one_or_none() is not None

    def add_response(self, row: QuestionnaireResponse) -> None:
        self._session.add(row)

    def add_answer(self, row: QuestionAnswer) -> None:
        self._session.add(row)

    async def get_by_project_and_id(
        self,
        project_id: uuid.UUID,
        response_id: uuid.UUID,
        *,
        with_answers: bool = False,
    ) -> QuestionnaireResponse | None:
        stmt = select(QuestionnaireResponse).where(
            QuestionnaireResponse.id == response_id,
            QuestionnaireResponse.project_id == project_id,
        )
        if with_answers:
            stmt = stmt.options(selectinload(QuestionnaireResponse.answers))
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_project(
        self,
        project_id: uuid.UUID,
    ) -> list[QuestionnaireResponse]:
        stmt = (
            select(QuestionnaireResponse)
            .where(QuestionnaireResponse.project_id == project_id)
            .order_by(QuestionnaireResponse.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_self_report_token_by_response_id(
        self,
        response_id: uuid.UUID,
    ) -> SelfReportToken | None:
        stmt = select(SelfReportToken).where(SelfReportToken.response_id == response_id)
        row = await self._session.execute(stmt)
        return row.scalar_one_or_none()

    async def get_self_report_token_bundle(
        self,
        token: uuid.UUID,
    ) -> SelfReportToken | None:
        stmt = (
            select(SelfReportToken)
            .where(SelfReportToken.token == token)
            .options(
                joinedload(SelfReportToken.questionnaire_response).selectinload(
                    QuestionnaireResponse.answers,
                ),
                joinedload(SelfReportToken.questionnaire_response)
                .selectinload(QuestionnaireResponse.template)
                .selectinload(QuestionnaireTemplate.items),
            )
        )
        row = await self._session.execute(stmt)
        return row.unique().scalar_one_or_none()

    async def upsert_self_report_token(
        self,
        *,
        response_id: uuid.UUID,
        token: uuid.UUID,
        expires_at: datetime,
    ) -> SelfReportToken:
        existing = await self.get_self_report_token_by_response_id(response_id)
        if existing is not None:
            existing.token = token
            existing.expires_at = expires_at
            existing.used_at = None
            return existing
        row = SelfReportToken(
            id=uuid.uuid4(),
            response_id=response_id,
            token=token,
            expires_at=expires_at,
            used_at=None,
        )
        self._session.add(row)
        return row
