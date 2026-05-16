"""Pydantic contracts for questionnaire responses (camelCase JSON)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import Field

from src.modules.auth.schemas import CamelModel

AnswerValue = str | int | float | bool | list[Any]


class QuestionnaireResponseCreateIn(CamelModel):
    participant_profile_id: UUID
    template_id: UUID
    executor_id: UUID | None = None


class QuestionnaireAnswerSubmitIn(CamelModel):
    question_item_id: UUID
    value: AnswerValue
    mark_completed: bool = False


class QuestionAnswerOut(CamelModel):
    id: str
    question_item_id: str
    value: Any
    created_at: str
    updated_at: str


class QuestionnaireResponseSummaryOut(CamelModel):
    id: str
    project_id: str
    participant_profile_id: str
    questionnaire_template_id: str
    executor_id: str | None = None
    status: str
    completed_at: str | None = None
    created_at: str
    updated_at: str


class QuestionnaireResponseDetailOut(QuestionnaireResponseSummaryOut):
    answers: list[QuestionAnswerOut]


class QuestionnaireResponsesListResponse(CamelModel):
    responses: list[QuestionnaireResponseSummaryOut]


class SelfReportSendLinkOut(CamelModel):
    token: str
    expires_at: str = Field(serialization_alias="expiresAt")
    fill_url: str | None = Field(default=None, serialization_alias="fillUrl")
