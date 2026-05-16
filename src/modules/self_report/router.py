"""Public HTTP routes for participant self-report (token, no JWT)."""

from uuid import UUID

from fastapi import APIRouter, Depends, status

from src.core.openapi_schemas import ApiErrorResponse
from src.modules.project_questionnaires.deps import get_questionnaire_responses_service
from src.modules.project_questionnaires.service import QuestionnaireResponsesService
from src.modules.self_report.schemas import (
    SelfReportSessionOut,
    SelfReportSubmitIn,
    SelfReportSubmitResponseOut,
)

router = APIRouter(prefix="/api/v1/self-report", tags=["Self-report"])


@router.get(
    "/{token}",
    response_model=SelfReportSessionOut,
    response_model_by_alias=True,
    summary="Load questionnaire session by self-report token",
    responses={
        404: {"model": ApiErrorResponse},
        409: {"model": ApiErrorResponse},
        410: {"model": ApiErrorResponse},
    },
)
async def get_self_report_session(
    token: UUID,
    service: QuestionnaireResponsesService = Depends(
        get_questionnaire_responses_service,
    ),
) -> SelfReportSessionOut:
    return await service.get_self_report_public(token)


@router.post(
    "/{token}/submit",
    response_model=SelfReportSubmitResponseOut,
    response_model_by_alias=True,
    status_code=status.HTTP_200_OK,
    summary="Submit all answers and complete self-report questionnaire",
    responses={
        404: {"model": ApiErrorResponse},
        409: {"model": ApiErrorResponse},
        410: {"model": ApiErrorResponse},
        422: {"model": ApiErrorResponse},
    },
)
async def submit_self_report(
    token: UUID,
    body: SelfReportSubmitIn,
    service: QuestionnaireResponsesService = Depends(
        get_questionnaire_responses_service,
    ),
) -> SelfReportSubmitResponseOut:
    return await service.submit_self_report_public(token, body)
