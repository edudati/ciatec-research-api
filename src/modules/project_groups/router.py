"""HTTP routes for project groups (nested under /projects)."""

from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from src.core.openapi_schemas import ApiErrorResponse
from src.models.user import User
from src.modules.auth.deps import require_active_user
from src.modules.project_groups.deps import get_project_groups_service
from src.modules.project_groups.schemas import (
    GroupCreateIn,
    GroupListResponse,
    GroupOut,
    GroupPatchIn,
)
from src.modules.project_groups.service import ProjectGroupsService

router = APIRouter(
    prefix="/api/v1/projects/{project_id}/groups",
    tags=["Project groups"],
)


@router.get(
    "",
    response_model=GroupListResponse,
    response_model_by_alias=True,
    summary="List groups for a project",
    responses={
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
    },
)
async def list_groups(
    project_id: UUID,
    viewer: User = Depends(require_active_user),
    service: ProjectGroupsService = Depends(get_project_groups_service),
) -> GroupListResponse:
    return await service.list_for_project(project_id, viewer)


@router.post(
    "",
    response_model=GroupOut,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=True,
    summary="Create project group",
    responses={
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
        409: {"model": ApiErrorResponse},
    },
)
async def create_group(
    project_id: UUID,
    body: GroupCreateIn,
    actor: User = Depends(require_active_user),
    service: ProjectGroupsService = Depends(get_project_groups_service),
) -> GroupOut:
    return await service.create(project_id, body, actor)


@router.patch(
    "/{group_id}",
    response_model=GroupOut,
    response_model_by_alias=True,
    summary="Update project group",
    responses={
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
        409: {"model": ApiErrorResponse},
    },
)
async def patch_group(
    project_id: UUID,
    group_id: UUID,
    body: GroupPatchIn,
    actor: User = Depends(require_active_user),
    service: ProjectGroupsService = Depends(get_project_groups_service),
) -> GroupOut:
    return await service.patch(project_id, group_id, body, actor)


@router.delete(
    "/{group_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete project group",
    responses={
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
        409: {"model": ApiErrorResponse},
    },
)
async def delete_group(
    project_id: UUID,
    group_id: UUID,
    actor: User = Depends(require_active_user),
    service: ProjectGroupsService = Depends(get_project_groups_service),
) -> Response:
    await service.delete(project_id, group_id, actor)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
