"""HTTP routes for questionnaire responses (nested under /projects)."""

from uuid import UUID

from fastapi import APIRouter, Depends, status

from src.core.config import Settings, get_settings
from src.core.openapi_schemas import ApiErrorResponse
from src.models.user import User
from src.modules.auth.deps import require_active_user
from src.modules.project_questionnaires.deps import get_questionnaire_responses_service
from src.modules.project_questionnaires.schemas import (
    QuestionnaireAnswerSubmitIn,
    QuestionnaireResponseCreateIn,
    QuestionnaireResponseDetailOut,
    QuestionnaireResponsesListResponse,
    QuestionnaireResponseSummaryOut,
    SelfReportSendLinkOut,
)
from src.modules.project_questionnaires.service import QuestionnaireResponsesService

router = APIRouter(
    prefix="/api/v1/projects/{project_id}/questionnaires",
    tags=["Project questionnaires"],
)


@router.get(
    "",
    response_model=QuestionnaireResponsesListResponse,
    response_model_by_alias=True,
    summary="List questionnaire responses for a project",
    responses={
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
    },
)
async def list_questionnaire_responses(
    project_id: UUID,
    viewer: User = Depends(require_active_user),
    service: QuestionnaireResponsesService = Depends(
        get_questionnaire_responses_service,
    ),
) -> QuestionnaireResponsesListResponse:
    return await service.list_for_project(project_id, viewer)


@router.post(
    "",
    response_model=QuestionnaireResponseSummaryOut,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=True,
    summary="Create questionnaire response",
    responses={
        400: {"model": ApiErrorResponse},
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
        422: {"model": ApiErrorResponse},
    },
)
async def create_questionnaire_response(
    project_id: UUID,
    body: QuestionnaireResponseCreateIn,
    actor: User = Depends(require_active_user),
    service: QuestionnaireResponsesService = Depends(
        get_questionnaire_responses_service,
    ),
) -> QuestionnaireResponseSummaryOut:
    return await service.create(project_id, body, actor)


@router.get(
    "/{response_id}",
    response_model=QuestionnaireResponseDetailOut,
    response_model_by_alias=True,
    summary="Get questionnaire response by id",
    responses={
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
    },
)
async def get_questionnaire_response(
    project_id: UUID,
    response_id: UUID,
    viewer: User = Depends(require_active_user),
    service: QuestionnaireResponsesService = Depends(
        get_questionnaire_responses_service,
    ),
) -> QuestionnaireResponseDetailOut:
    return await service.get_one(project_id, response_id, viewer)


@router.post(
    "/{response_id}/answers",
    response_model=QuestionnaireResponseDetailOut,
    response_model_by_alias=True,
    summary="Submit an answer for a questionnaire response",
    responses={
        400: {"model": ApiErrorResponse},
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
        409: {"model": ApiErrorResponse},
        422: {"model": ApiErrorResponse},
    },
)
async def submit_questionnaire_answer(
    project_id: UUID,
    response_id: UUID,
    body: QuestionnaireAnswerSubmitIn,
    actor: User = Depends(require_active_user),
    service: QuestionnaireResponsesService = Depends(
        get_questionnaire_responses_service,
    ),
) -> QuestionnaireResponseDetailOut:
    return await service.submit_answer(project_id, response_id, body, actor)


@router.post(
    "/{response_id}/send-link",
    response_model=SelfReportSendLinkOut,
    response_model_by_alias=True,
    summary="Issue or refresh self-report fill link for a questionnaire response",
    responses={
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
        409: {"model": ApiErrorResponse},
        422: {"model": ApiErrorResponse},
    },
)
async def send_self_report_link(
    project_id: UUID,
    response_id: UUID,
    actor: User = Depends(require_active_user),
    settings: Settings = Depends(get_settings),
    service: QuestionnaireResponsesService = Depends(
        get_questionnaire_responses_service,
    ),
) -> SelfReportSendLinkOut:
    return await service.send_self_report_link(
        project_id,
        response_id,
        actor,
        settings,
    )
