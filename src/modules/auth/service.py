"""Auth business logic and transactions."""

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Settings
from src.core.enums import UserRole
from src.core.exceptions import ConflictError, NotFoundError, UnauthorizedError
from src.models.user import AuthUser, RefreshToken, User
from src.modules.auth.jwt_access import create_access_token
from src.modules.auth.passwords import hash_password, verify_password
from src.modules.auth.refresh_material import (
    create_refresh_pair,
    parse_refresh_token,
    refresh_expires_at,
    verify_refresh_secret,
)
from src.modules.auth.repository import AuthRepository
from src.modules.auth.schemas import (
    ChangePasswordIn,
    LoginIn,
    LoginResponse,
    LogoutIn,
    RefreshIn,
    RefreshResponse,
    RegisterIn,
    RegisterResponse,
    UserPublic,
)

_INVALID_LOGIN = "Invalid email or password"
_INVALID_REFRESH = "Invalid or expired refresh token"
_INVALID_REFRESH_CODE = "INVALID_REFRESH_TOKEN"


class AuthService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self._session = session
        self._settings = settings
        self._repo = AuthRepository(session)

    def _to_user_public(self, user: User, auth: AuthUser) -> UserPublic:
        created = user.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=UTC)
        return UserPublic(
            id=str(user.id),
            email=user.email,
            name=user.name,
            role=UserRole(user.role),
            created_at=created.isoformat(),
            email_verified=auth.email_verified_at is not None,
            is_first_access=user.is_first_access,
            totp_enabled=False,
        )

    async def register(self, body: RegisterIn) -> RegisterResponse:
        email = body.email.strip().lower()
        if await self._repo.user_exists_by_email(email):
            raise ConflictError("Email already in use", code="EMAIL_IN_USE")

        now = datetime.now(UTC)
        # PK must be set before flush: SQLAlchemy does not apply `default=uuid.uuid4`
        # on the in-memory instance until flush, so FKs would see `user.id` as None.
        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            email=email,
            name=body.name.strip(),
            role=UserRole.PLAYER.value,
            is_first_access=True,
        )
        auth = AuthUser(
            user_id=user_id,
            password_hash=hash_password(body.password),
            email_verified_at=now,
        )
        rid = uuid.uuid4()
        expires = refresh_expires_at(self._settings)
        raw_refresh, sec_hash = create_refresh_pair(self._settings, rid)
        rt = RefreshToken(
            id=rid,
            user_id=user_id,
            secret_hash=sec_hash,
            expires_at=expires,
        )
        self._repo.add_user(user)
        self._repo.add_auth_user(auth)
        self._repo.add_refresh_token(rt)
        await self._session.flush()
        await self._session.commit()
        await self._session.refresh(user)
        await self._session.refresh(auth)

        access = create_access_token(user.id, self._settings)
        user_pub = self._to_user_public(user, auth)
        return RegisterResponse(
            user=user_pub,
            access_token=access,
            refresh_token=raw_refresh,
        )

    async def login(self, body: LoginIn) -> LoginResponse:
        email = body.email.strip().lower()
        user = await self._repo.get_active_user_by_email(email)
        if user is None or user.auth_user is None:
            raise UnauthorizedError(_INVALID_LOGIN, code="INVALID_CREDENTIALS")
        if not verify_password(body.password, user.auth_user.password_hash):
            raise UnauthorizedError(_INVALID_LOGIN, code="INVALID_CREDENTIALS")

        rid = uuid.uuid4()
        expires = refresh_expires_at(self._settings)
        raw_refresh, sec_hash = create_refresh_pair(self._settings, rid)
        rt = RefreshToken(
            id=rid,
            user_id=user.id,
            secret_hash=sec_hash,
            expires_at=expires,
        )
        self._repo.add_refresh_token(rt)
        await self._session.flush()
        await self._session.commit()
        await self._session.refresh(user)
        await self._session.refresh(user.auth_user)

        access = create_access_token(user.id, self._settings)
        user_pub = self._to_user_public(user, user.auth_user)
        return LoginResponse(
            user=user_pub,
            access_token=access,
            refresh_token=raw_refresh,
        )

    async def refresh(self, body: RefreshIn) -> RefreshResponse:
        try:
            material = parse_refresh_token(body.refresh_token)
        except ValueError as exc:
            raise UnauthorizedError(
                _INVALID_REFRESH,
                code=_INVALID_REFRESH_CODE,
            ) from exc

        row = await self._repo.get_refresh_token(material.row_id)
        now = datetime.now(UTC)
        if row is None or row.revoked_at is not None or row.expires_at <= now:
            raise UnauthorizedError(_INVALID_REFRESH, code=_INVALID_REFRESH_CODE)
        if not verify_refresh_secret(
            self._settings,
            material.secret,
            row.secret_hash,
        ):
            raise UnauthorizedError(_INVALID_REFRESH, code=_INVALID_REFRESH_CODE)

        self._repo.revoke_refresh_token(row, now)
        new_id = uuid.uuid4()
        expires = refresh_expires_at(self._settings)
        raw_new, sec_hash = create_refresh_pair(self._settings, new_id)
        new_row = RefreshToken(
            id=new_id,
            user_id=row.user_id,
            secret_hash=sec_hash,
            expires_at=expires,
        )
        self._repo.add_refresh_token(new_row)
        await self._session.flush()
        await self._session.commit()

        access = create_access_token(row.user_id, self._settings)
        return RefreshResponse(access_token=access, refresh_token=raw_new)

    async def logout(self, user_id: uuid.UUID, body: LogoutIn) -> None:
        now = datetime.now(UTC)
        if body.refresh_token:
            try:
                material = parse_refresh_token(body.refresh_token)
            except ValueError as exc:
                raise UnauthorizedError(
                    _INVALID_REFRESH,
                    code=_INVALID_REFRESH_CODE,
                ) from exc
            row = await self._repo.get_refresh_token(material.row_id)
            if row is None or row.user_id != user_id:
                raise UnauthorizedError(_INVALID_REFRESH, code=_INVALID_REFRESH_CODE)
            if row.revoked_at is not None:
                return
            if not verify_refresh_secret(
                self._settings,
                material.secret,
                row.secret_hash,
            ):
                raise UnauthorizedError(_INVALID_REFRESH, code=_INVALID_REFRESH_CODE)
            self._repo.revoke_refresh_token(row, now)
        else:
            await self._repo.revoke_all_refresh_tokens_for_user(user_id, now)
        await self._session.commit()

    async def me(self, user_id: uuid.UUID) -> UserPublic:
        user = await self._repo.get_active_user_by_id(user_id)
        if user is None or user.auth_user is None:
            raise NotFoundError("User not found", code="USER_NOT_FOUND")
        return self._to_user_public(user, user.auth_user)

    async def change_password(
        self, user_id: uuid.UUID, body: ChangePasswordIn
    ) -> UserPublic:
        user = await self._repo.get_active_user_by_id(user_id)
        if user is None or user.auth_user is None:
            raise NotFoundError("User not found", code="USER_NOT_FOUND")
        auth = user.auth_user
        auth.password_hash = hash_password(body.password)
        user.is_first_access = False
        await self._session.commit()
        await self._session.refresh(user)
        await self._session.refresh(auth)
        return self._to_user_public(user, auth)
