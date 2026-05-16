"""HTTP routes for assessment records (nested under /projects)."""

from uuid import UUID

from fastapi import APIRouter, Depends, status

from src.core.openapi_schemas import ApiErrorResponse
from src.models.user import User
from src.modules.auth.deps import require_active_user
from src.modules.project_assessments.deps import get_assessment_records_service
from src.modules.project_assessments.schemas import (
    AssessmentRecordCreateIn,
    AssessmentRecordOut,
    AssessmentRecordPatchIn,
    AssessmentRecordsListResponse,
)
from src.modules.project_assessments.service import AssessmentRecordsService

router = APIRouter(
    prefix="/api/v1/projects/{project_id}/assessments",
    tags=["Project assessments"],
)


@router.get(
    "",
    response_model=AssessmentRecordsListResponse,
    response_model_by_alias=True,
    summary="List assessment records for a project",
    responses={
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
    },
)
async def list_assessment_records(
    project_id: UUID,
    viewer: User = Depends(require_active_user),
    service: AssessmentRecordsService = Depends(get_assessment_records_service),
) -> AssessmentRecordsListResponse:
    return await service.list_for_project(project_id, viewer)


@router.post(
    "",
    response_model=AssessmentRecordOut,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=True,
    summary="Create assessment record",
    responses={
        400: {"model": ApiErrorResponse},
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
        422: {"model": ApiErrorResponse},
    },
)
async def create_assessment_record(
    project_id: UUID,
    body: AssessmentRecordCreateIn,
    actor: User = Depends(require_active_user),
    service: AssessmentRecordsService = Depends(get_assessment_records_service),
) -> AssessmentRecordOut:
    return await service.create(project_id, body, actor)


@router.get(
    "/{record_id}",
    response_model=AssessmentRecordOut,
    response_model_by_alias=True,
    summary="Get assessment record by id",
    responses={
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
    },
)
async def get_assessment_record(
    project_id: UUID,
    record_id: UUID,
    viewer: User = Depends(require_active_user),
    service: AssessmentRecordsService = Depends(get_assessment_records_service),
) -> AssessmentRecordOut:
    return await service.get_one(project_id, record_id, viewer)


@router.patch(
    "/{record_id}",
    response_model=AssessmentRecordOut,
    response_model_by_alias=True,
    summary="Update assessment record",
    responses={
        400: {"model": ApiErrorResponse},
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
        422: {"model": ApiErrorResponse},
    },
)
async def patch_assessment_record(
    project_id: UUID,
    record_id: UUID,
    body: AssessmentRecordPatchIn,
    actor: User = Depends(require_active_user),
    service: AssessmentRecordsService = Depends(get_assessment_records_service),
) -> AssessmentRecordOut:
    return await service.patch(project_id, record_id, body, actor)
