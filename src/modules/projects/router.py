"""Project HTTP routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from src.core.openapi_schemas import ApiErrorResponse
from src.models.user import User
from src.modules.auth.deps import (
    require_active_user,
    require_admin,
    require_admin_or_pi,
)
from src.modules.projects.deps import get_projects_service
from src.modules.projects.schemas import (
    ProjectCreateIn,
    ProjectListResponse,
    ProjectOut,
    ProjectPatchIn,
)
from src.modules.projects.service import ProjectsService

router = APIRouter(prefix="/api/v1/projects", tags=["Projects"])


@router.get(
    "",
    response_model=ProjectListResponse,
    response_model_by_alias=True,
    summary="List projects visible to the current user",
    responses={401: {"model": ApiErrorResponse}},
)
async def list_projects(
    viewer: User = Depends(require_active_user),
    service: ProjectsService = Depends(get_projects_service),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100, alias="pageSize"),
    q: str | None = Query(
        None,
        description="Filter by name or code (case-insensitive)",
    ),
) -> ProjectListResponse:
    return await service.list_projects(
        user=viewer,
        page=page,
        page_size=page_size,
        q=q,
    )


@router.post(
    "",
    response_model=ProjectOut,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=True,
    summary="Create project",
    responses={
        400: {"model": ApiErrorResponse},
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
        409: {"model": ApiErrorResponse},
    },
)
async def create_project(
    body: ProjectCreateIn,
    _: User = Depends(require_admin_or_pi),
    service: ProjectsService = Depends(get_projects_service),
) -> ProjectOut:
    return await service.create(body)


@router.get(
    "/{project_id}",
    response_model=ProjectOut,
    response_model_by_alias=True,
    summary="Get project by id",
    responses={
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
    },
)
async def get_project(
    project_id: UUID,
    viewer: User = Depends(require_active_user),
    service: ProjectsService = Depends(get_projects_service),
) -> ProjectOut:
    return await service.get(project_id, viewer)


@router.patch(
    "/{project_id}",
    response_model=ProjectOut,
    response_model_by_alias=True,
    summary="Update project",
    responses={
        400: {"model": ApiErrorResponse},
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
        422: {"model": ApiErrorResponse},
    },
)
async def patch_project(
    project_id: UUID,
    body: ProjectPatchIn,
    actor: User = Depends(require_active_user),
    service: ProjectsService = Depends(get_projects_service),
) -> ProjectOut:
    return await service.patch(project_id, body, actor)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete project (admin only)",
    responses={401: {"model": ApiErrorResponse}, 403: {"model": ApiErrorResponse}},
)
async def delete_project(
    project_id: UUID,
    _: User = Depends(require_admin),
    service: ProjectsService = Depends(get_projects_service),
) -> Response:
    await service.soft_delete(project_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
