"""Public self-report (token) JSON contracts."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from src.modules.auth.schemas import CamelModel
from src.modules.instruments.schemas_questionnaires import QuestionItemOut
from src.modules.project_questionnaires.schemas import AnswerValue, QuestionAnswerOut


class SelfReportTemplateBriefOut(CamelModel):
    code: str
    name: str


class SelfReportSessionOut(CamelModel):
    expires_at: str = Field(serialization_alias="expiresAt")
    response_status: str = Field(serialization_alias="responseStatus")
    template: SelfReportTemplateBriefOut
    items: list[QuestionItemOut]
    answers: list[QuestionAnswerOut]


class SelfReportAnswerPairIn(CamelModel):
    question_item_id: UUID
    value: AnswerValue


class SelfReportSubmitIn(CamelModel):
    answers: list[SelfReportAnswerPairIn]


class SelfReportSubmitResponseOut(CamelModel):
    status: str
    completed_at: str = Field(serialization_alias="completedAt")
