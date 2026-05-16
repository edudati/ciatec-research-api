"""Auth HTTP routes."""

from uuid import UUID

from fastapi import APIRouter, Body, Depends, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Settings, get_settings
from src.core.database import get_db
from src.core.openapi_schemas import ApiErrorResponse
from src.modules.auth.deps import get_access_user_id
from src.modules.auth.schemas import (
    ChangePasswordIn,
    ChangePasswordResponse,
    LoginIn,
    LoginResponse,
    LogoutIn,
    RefreshIn,
    RefreshResponse,
    RegisterIn,
    RegisterResponse,
    UserPublic,
)
from src.modules.auth.service import AuthService


def get_auth_service(
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AuthService:
    return AuthService(db, settings)


router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=True,
    responses={409: {"model": ApiErrorResponse}},
)
async def register(
    body: RegisterIn,
    service: AuthService = Depends(get_auth_service),
) -> RegisterResponse:
    return await service.register(body)


@router.post(
    "/login",
    response_model=LoginResponse,
    response_model_by_alias=True,
)
async def login(
    body: LoginIn,
    service: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    return await service.login(body)


@router.post(
    "/refresh",
    response_model=RefreshResponse,
    response_model_by_alias=True,
)
async def refresh_tokens(
    body: RefreshIn,
    service: AuthService = Depends(get_auth_service),
) -> RefreshResponse:
    return await service.refresh(body)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def logout(
    body: LogoutIn = Body(default_factory=LogoutIn),
    user_id: UUID = Depends(get_access_user_id),
    service: AuthService = Depends(get_auth_service),
) -> Response:
    await service.logout(user_id, body)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/me",
    response_model=UserPublic,
    response_model_by_alias=True,
)
async def me(
    user_id: UUID = Depends(get_access_user_id),
    service: AuthService = Depends(get_auth_service),
) -> UserPublic:
    return await service.me(user_id)


@router.post(
    "/change-password",
    response_model=ChangePasswordResponse,
    response_model_by_alias=True,
    summary="Change own password",
    description=(
        "Any authenticated user may set a new password for their account. "
        "Clears `isFirstAccess` after a successful update."
    ),
)
async def change_password(
    body: ChangePasswordIn,
    user_id: UUID = Depends(get_access_user_id),
    service: AuthService = Depends(get_auth_service),
) -> ChangePasswordResponse:
    user = await service.change_password(user_id, body)
    return ChangePasswordResponse(user=user)
