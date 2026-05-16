"""Admin user management (transactions)."""

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.enums import UserRole
from src.core.exceptions import ConflictError, NotFoundError
from src.models.user import AuthUser, User
from src.modules.auth.passwords import hash_password
from src.modules.auth.repository import AuthRepository
from src.modules.users.repository import UsersRepository
from src.modules.users.schemas import (
    UserAdminOut,
    UserCreateIn,
    UserListItemOut,
    UserListResponse,
    UserUpdateIn,
    parse_order,
    parse_user_list_sort,
)


class UsersService:
    _SORT_COLUMNS = {
        "createdAt": User.created_at,
        "name": User.name,
        "email": User.email,
        "updatedAt": User.updated_at,
    }

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._users = UsersRepository(session)
        self._auth = AuthRepository(session)

    @staticmethod
    def _dt_iso(dt: datetime) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.isoformat()

    def _to_list_item(self, user: User, auth: AuthUser) -> UserListItemOut:
        return UserListItemOut(
            id=str(user.id),
            email=user.email,
            name=user.name,
            role=UserRole(user.role),
            created_at=self._dt_iso(user.created_at),
            email_verified=auth.email_verified_at is not None,
            is_first_access=user.is_first_access,
            totp_enabled=False,
            updated_at=self._dt_iso(user.updated_at),
        )

    def _to_admin_out(self, user: User, auth: AuthUser) -> UserAdminOut:
        deleted_raw = user.deleted_at
        deleted_out: str | None = None
        if deleted_raw is not None:
            deleted_out = self._dt_iso(deleted_raw)
        return UserAdminOut(
            id=str(user.id),
            email=user.email,
            name=user.name,
            role=UserRole(user.role),
            created_at=self._dt_iso(user.created_at),
            email_verified=auth.email_verified_at is not None,
            is_first_access=user.is_first_access,
            totp_enabled=False,
            updated_at=self._dt_iso(user.updated_at),
            deleted_at=deleted_out,
        )

    async def list_users(
        self,
        *,
        page: int,
        page_size: int,
        q: str | None,
        role: UserRole | None,
        sort: str,
        order: str,
    ) -> UserListResponse:
        sort_key = parse_user_list_sort(sort)
        sort_col = self._SORT_COLUMNS[sort_key]
        role_val = role.value if role is not None else None
        total = await self._users.count_list(q=q, role=role_val)
        rows = await self._users.list_page(
            page=page,
            page_size=page_size,
            q=q,
            role=role_val,
            sort_column=sort_col,
            order_desc=parse_order(order),
        )
        items: list[UserListItemOut] = []
        for u in rows:
            assert u.auth_user is not None  # inner join + joinedload
            items.append(self._to_list_item(u, u.auth_user))
        return UserListResponse(
            users=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_user(self, user_id: uuid.UUID) -> UserAdminOut:
        user = await self._users.get_by_id_with_auth(user_id)
        if user is None or user.auth_user is None:
            raise NotFoundError("User not found", code="USER_NOT_FOUND")
        return self._to_admin_out(user, user.auth_user)

    async def create_user(self, body: UserCreateIn) -> UserAdminOut:
        email = body.email.strip().lower()
        if await self._auth.user_exists_by_email(email):
            raise ConflictError("Email already in use", code="EMAIL_IN_USE")

        now = datetime.now(UTC)
        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            email=email,
            name=body.name.strip(),
            role=body.role.value,
            is_first_access=True,
        )
        auth = AuthUser(
            user_id=user_id,
            password_hash=hash_password(body.password),
            email_verified_at=now,
        )
        self._users.add_user(user)
        self._users.add_auth_user(auth)
        await self._session.flush()
        await self._session.commit()
        await self._session.refresh(user)
        await self._session.refresh(auth)
        return self._to_admin_out(user, auth)

    async def update_user(self, user_id: uuid.UUID, body: UserUpdateIn) -> UserAdminOut:
        user = await self._users.get_by_id_with_auth(user_id)
        if user is None or user.auth_user is None:
            raise NotFoundError("User not found", code="USER_NOT_FOUND")
        if user.deleted_at is not None:
            raise NotFoundError("User not found", code="USER_NOT_FOUND")

        auth = user.auth_user
        if body.email is not None:
            new_email = body.email.strip().lower()
            if new_email != user.email and await self._users.email_taken_by_other(
                new_email,
                user.id,
            ):
                raise ConflictError("Email already in use", code="EMAIL_IN_USE")
            user.email = new_email
        if body.name is not None:
            user.name = body.name.strip()
        if body.role is not None:
            user.role = body.role.value
        if body.is_first_access is not None:
            user.is_first_access = body.is_first_access
        if body.password is not None:
            auth.password_hash = hash_password(body.password)

        await self._session.commit()
        await self._session.refresh(user)
        await self._session.refresh(auth)
        return self._to_admin_out(user, auth)

    async def soft_delete(self, user_id: uuid.UUID) -> None:
        user = await self._users.get_by_id_with_auth(user_id)
        if user is None:
            raise NotFoundError("User not found", code="USER_NOT_FOUND")
        now = datetime.now(UTC)
        if user.deleted_at is None:
            user.deleted_at = now
            await self._auth.revoke_all_refresh_tokens_for_user(user.id, now)
        await self._session.commit()
