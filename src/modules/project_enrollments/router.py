"""HTTP routes for participant enrollments (nested under /projects)."""

from uuid import UUID

from fastapi import APIRouter, Body, Depends, Response, status

from src.core.openapi_schemas import ApiErrorResponse
from src.models.user import User
from src.modules.auth.deps import require_active_user
from src.modules.project_enrollments.deps import get_project_enrollments_service
from src.modules.project_enrollments.schemas import (
    EnrollmentCreateIn,
    EnrollmentDeleteIn,
    EnrollmentListResponse,
    EnrollmentOut,
    EnrollmentPatchIn,
)
from src.modules.project_enrollments.service import ProjectEnrollmentsService

router = APIRouter(
    prefix="/api/v1/projects/{project_id}/enrollments",
    tags=["Project enrollments"],
)


@router.get(
    "",
    response_model=EnrollmentListResponse,
    response_model_by_alias=True,
    summary="List enrollments for a project",
    responses={
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
    },
)
async def list_enrollments(
    project_id: UUID,
    viewer: User = Depends(require_active_user),
    service: ProjectEnrollmentsService = Depends(get_project_enrollments_service),
) -> EnrollmentListResponse:
    return await service.list_for_project(project_id, viewer)


@router.post(
    "",
    response_model=EnrollmentOut,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=True,
    summary="Create participant enrollment",
    responses={
        400: {"model": ApiErrorResponse},
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
        409: {"model": ApiErrorResponse},
        422: {"model": ApiErrorResponse},
    },
)
async def create_enrollment(
    project_id: UUID,
    body: EnrollmentCreateIn,
    actor: User = Depends(require_active_user),
    service: ProjectEnrollmentsService = Depends(get_project_enrollments_service),
) -> EnrollmentOut:
    return await service.create(project_id, body, actor)


@router.get(
    "/{enrollment_id}",
    response_model=EnrollmentOut,
    response_model_by_alias=True,
    summary="Get enrollment by id",
    responses={
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
    },
)
async def get_enrollment(
    project_id: UUID,
    enrollment_id: UUID,
    viewer: User = Depends(require_active_user),
    service: ProjectEnrollmentsService = Depends(get_project_enrollments_service),
) -> EnrollmentOut:
    return await service.get_one(project_id, enrollment_id, viewer)


@router.patch(
    "/{enrollment_id}",
    response_model=EnrollmentOut,
    response_model_by_alias=True,
    summary="Update enrollment",
    responses={
        400: {"model": ApiErrorResponse},
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
    },
)
async def patch_enrollment(
    project_id: UUID,
    enrollment_id: UUID,
    body: EnrollmentPatchIn,
    actor: User = Depends(require_active_user),
    service: ProjectEnrollmentsService = Depends(get_project_enrollments_service),
) -> EnrollmentOut:
    return await service.patch(project_id, enrollment_id, body, actor)


@router.delete(
    "/{enrollment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Record enrollment exit (sets exited_at and exit reason)",
    responses={
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
        409: {"model": ApiErrorResponse},
    },
)
async def delete_enrollment(
    project_id: UUID,
    enrollment_id: UUID,
    body: EnrollmentDeleteIn = Body(...),
    actor: User = Depends(require_active_user),
    service: ProjectEnrollmentsService = Depends(get_project_enrollments_service),
) -> Response:
    await service.record_exit(project_id, enrollment_id, body, actor)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
