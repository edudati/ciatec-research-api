"""HTTP routes for intervention records (nested under /projects)."""

from uuid import UUID

from fastapi import APIRouter, Depends, status

from src.core.openapi_schemas import ApiErrorResponse
from src.models.user import User
from src.modules.auth.deps import require_active_user
from src.modules.project_interventions.deps import get_intervention_records_service
from src.modules.project_interventions.schemas import (
    InterventionRecordCreateIn,
    InterventionRecordOut,
    InterventionRecordPatchIn,
    InterventionRecordsListResponse,
)
from src.modules.project_interventions.service import InterventionRecordsService

router = APIRouter(
    prefix="/api/v1/projects/{project_id}/interventions",
    tags=["Project interventions"],
)


@router.get(
    "",
    response_model=InterventionRecordsListResponse,
    response_model_by_alias=True,
    summary="List intervention records for a project",
    responses={
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
    },
)
async def list_intervention_records(
    project_id: UUID,
    viewer: User = Depends(require_active_user),
    service: InterventionRecordsService = Depends(get_intervention_records_service),
) -> InterventionRecordsListResponse:
    return await service.list_for_project(project_id, viewer)


@router.post(
    "",
    response_model=InterventionRecordOut,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=True,
    summary="Create intervention record",
    responses={
        400: {"model": ApiErrorResponse},
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
        409: {"model": ApiErrorResponse},
        422: {"model": ApiErrorResponse},
    },
)
async def create_intervention_record(
    project_id: UUID,
    body: InterventionRecordCreateIn,
    actor: User = Depends(require_active_user),
    service: InterventionRecordsService = Depends(get_intervention_records_service),
) -> InterventionRecordOut:
    return await service.create(project_id, body, actor)


@router.get(
    "/{record_id}",
    response_model=InterventionRecordOut,
    response_model_by_alias=True,
    summary="Get intervention record by id",
    responses={
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
    },
)
async def get_intervention_record(
    project_id: UUID,
    record_id: UUID,
    viewer: User = Depends(require_active_user),
    service: InterventionRecordsService = Depends(get_intervention_records_service),
) -> InterventionRecordOut:
    return await service.get_one(project_id, record_id, viewer)


@router.patch(
    "/{record_id}",
    response_model=InterventionRecordOut,
    response_model_by_alias=True,
    summary="Update intervention record",
    responses={
        400: {"model": ApiErrorResponse},
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
        422: {"model": ApiErrorResponse},
    },
)
async def patch_intervention_record(
    project_id: UUID,
    record_id: UUID,
    body: InterventionRecordPatchIn,
    actor: User = Depends(require_active_user),
    service: InterventionRecordsService = Depends(get_intervention_records_service),
) -> InterventionRecordOut:
    return await service.patch(project_id, record_id, body, actor)
