"""HTTP routes for project members (nested under /projects)."""

from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from src.core.openapi_schemas import ApiErrorResponse
from src.models.user import User
from src.modules.auth.deps import require_active_user
from src.modules.project_members.deps import get_project_members_service
from src.modules.project_members.schemas import (
    ProjectMemberCreateIn,
    ProjectMemberListResponse,
    ProjectMemberOut,
    ProjectMemberPatchIn,
)
from src.modules.project_members.service import ProjectMembersService

router = APIRouter(
    prefix="/api/v1/projects/{project_id}/members",
    tags=["Project members"],
)


@router.get(
    "",
    response_model=ProjectMemberListResponse,
    response_model_by_alias=True,
    summary="List project members",
    responses={
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
    },
)
async def list_members(
    project_id: UUID,
    viewer: User = Depends(require_active_user),
    service: ProjectMembersService = Depends(get_project_members_service),
) -> ProjectMemberListResponse:
    return await service.list_for_project(project_id, viewer)


@router.post(
    "",
    response_model=ProjectMemberOut,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=True,
    summary="Add project member",
    responses={
        400: {"model": ApiErrorResponse},
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
        409: {"model": ApiErrorResponse},
    },
)
async def create_member(
    project_id: UUID,
    body: ProjectMemberCreateIn,
    actor: User = Depends(require_active_user),
    service: ProjectMembersService = Depends(get_project_members_service),
) -> ProjectMemberOut:
    return await service.create(project_id, body, actor)


@router.patch(
    "/{member_id}",
    response_model=ProjectMemberOut,
    response_model_by_alias=True,
    summary="Update project member",
    responses={
        400: {"model": ApiErrorResponse},
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
        422: {"model": ApiErrorResponse},
    },
)
async def patch_member(
    project_id: UUID,
    member_id: UUID,
    body: ProjectMemberPatchIn,
    actor: User = Depends(require_active_user),
    service: ProjectMembersService = Depends(get_project_members_service),
) -> ProjectMemberOut:
    return await service.patch(project_id, member_id, body, actor)


@router.delete(
    "/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove project member",
    responses={
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
        422: {"model": ApiErrorResponse},
    },
)
async def delete_member(
    project_id: UUID,
    member_id: UUID,
    actor: User = Depends(require_active_user),
    service: ProjectMembersService = Depends(get_project_members_service),
) -> Response:
    await service.delete(project_id, member_id, actor)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
