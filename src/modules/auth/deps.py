"""Bearer access token -> user id (`sub`)."""

from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.core.config import Settings, get_settings
from src.core.database import get_db
from src.core.enums import UserRole
from src.core.exceptions import ForbiddenError, UnauthorizedError
from src.models.user import User
from src.modules.auth.jwt_access import decode_access_token

_MISSING_ACCESS = "Missing or invalid access token"
_INACTIVE_USER = "User not found or inactive"

# scheme_name = OpenAPI key in main.py (Swagger Authorize must match the route).
bearer_scheme = HTTPBearer(auto_error=False, scheme_name="bearerAuth")


async def get_access_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> UUID:
    if credentials is None or not credentials.credentials:
        raise UnauthorizedError(_MISSING_ACCESS, code="UNAUTHORIZED")
    try:
        return decode_access_token(credentials.credentials.strip(), settings)
    except ValueError as exc:
        raise UnauthorizedError(_MISSING_ACCESS, code="UNAUTHORIZED") from exc


async def get_access_user_id_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> UUID | None:
    if credentials is None or not credentials.credentials:
        return None
    try:
        return decode_access_token(credentials.credentials.strip(), settings)
    except ValueError:
        return None


async def get_optional_active_user(
    user_id: UUID | None = Depends(get_access_user_id_optional),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    if user_id is None:
        return None
    stmt = (
        select(User)
        .where(User.id == user_id, User.deleted_at.is_(None))
        .options(joinedload(User.auth_user))
    )
    result = await db.execute(stmt)
    return result.unique().scalar_one_or_none()


async def require_admin(
    user_id: UUID = Depends(get_access_user_id),
    db: AsyncSession = Depends(get_db),
) -> User:
    stmt = (
        select(User)
        .where(User.id == user_id, User.deleted_at.is_(None))
        .options(joinedload(User.auth_user))
    )
    result = await db.execute(stmt)
    user = result.unique().scalar_one_or_none()
    if user is None:
        raise UnauthorizedError(_INACTIVE_USER, code="USER_INACTIVE")
    if user.role != UserRole.ADMIN.value:
        raise ForbiddenError("Admin access required", code="FORBIDDEN")
    return user


async def require_admin_or_pi(
    user_id: UUID = Depends(get_access_user_id),
    db: AsyncSession = Depends(get_db),
) -> User:
    stmt = (
        select(User)
        .where(User.id == user_id, User.deleted_at.is_(None))
        .options(joinedload(User.auth_user))
    )
    result = await db.execute(stmt)
    user = result.unique().scalar_one_or_none()
    if user is None:
        raise UnauthorizedError(_INACTIVE_USER, code="USER_INACTIVE")
    if user.role not in (UserRole.ADMIN.value, UserRole.PI.value):
        raise ForbiddenError("Admin or PI access required", code="FORBIDDEN")
    return user


async def require_active_user(
    user_id: UUID = Depends(get_access_user_id),
    db: AsyncSession = Depends(get_db),
) -> User:
    stmt = (
        select(User)
        .where(User.id == user_id, User.deleted_at.is_(None))
        .options(joinedload(User.auth_user))
    )
    result = await db.execute(stmt)
    user = result.unique().scalar_one_or_none()
    if user is None:
        raise UnauthorizedError(_INACTIVE_USER, code="USER_INACTIVE")
    return user
