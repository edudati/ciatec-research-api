"""Admin user HTTP routes."""

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.enums import UserRole
from src.core.openapi_schemas import ApiErrorResponse
from src.modules.auth.deps import require_admin
from src.modules.users.schemas import (
    UserAdminOut,
    UserCreateIn,
    UserListResponse,
    UserUpdateIn,
)
from src.modules.users.service import UsersService


def get_users_service(db: AsyncSession = Depends(get_db)) -> UsersService:
    return UsersService(db)


router = APIRouter(
    prefix="/api/v1/users",
    tags=["Users"],
    dependencies=[Depends(require_admin)],
)

SortField = Literal["createdAt", "name", "email", "updatedAt"]
OrderDir = Literal["asc", "desc"]


@router.get(
    "",
    response_model=UserListResponse,
    response_model_by_alias=True,
    summary="List users",
    description=(
        "Paginated list of users that are not soft-deleted and have credentials. "
        "`total` matches the same filters."
    ),
)
async def list_users(
    service: UsersService = Depends(get_users_service),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(10, ge=1, le=100, alias="pageSize"),
    q: str | None = Query(
        None,
        description="Case-insensitive match on name or email",
    ),
    role: UserRole | None = Query(None, description="Filter by system role"),
    sort: SortField = Query(
        "createdAt",
        description="Sort field: createdAt, name, email, updatedAt",
    ),
    order: OrderDir = Query("desc", description="Sort direction: asc or desc"),
) -> UserListResponse:
    return await service.list_users(
        page=page,
        page_size=page_size,
        q=q,
        role=role,
        sort=sort,
        order=order,
    )


@router.post(
    "",
    response_model=UserAdminOut,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=True,
    summary="Create user (admin)",
    description=(
        "Creates `User` + `AuthUser` with an explicit role. "
        "Password rules match public register."
    ),
    responses={409: {"model": ApiErrorResponse}},
)
async def create_user(
    body: UserCreateIn,
    service: UsersService = Depends(get_users_service),
) -> UserAdminOut:
    return await service.create_user(body)


@router.get(
    "/{user_id}",
    response_model=UserAdminOut,
    response_model_by_alias=True,
    summary="Get user by id",
    description="Same core fields as `GET /auth/me`, plus `updatedAt` and `deletedAt`.",
)
async def get_user(
    user_id: UUID,
    service: UsersService = Depends(get_users_service),
) -> UserAdminOut:
    return await service.get_user(user_id)


@router.patch(
    "/{user_id}",
    response_model=UserAdminOut,
    response_model_by_alias=True,
    summary="Update user",
    description="Partial update. Cannot update a soft-deleted user.",
    responses={409: {"model": ApiErrorResponse}},
)
async def update_user(
    user_id: UUID,
    body: UserUpdateIn,
    service: UsersService = Depends(get_users_service),
) -> UserAdminOut:
    return await service.update_user(user_id, body)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user",
    description="Sets `deletedAt`. Idempotent if the user is already deleted.",
)
async def delete_user(
    user_id: UUID,
    service: UsersService = Depends(get_users_service),
) -> Response:
    await service.soft_delete(user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
