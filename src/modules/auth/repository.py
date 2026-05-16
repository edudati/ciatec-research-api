"""Auth persistence."""

import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.models.user import AuthUser, RefreshToken, User


class AuthRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def user_exists_by_email(self, email: str) -> bool:
        stmt = select(User.id).where(User.email == email).limit(1)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_active_user_by_email(self, email: str) -> User | None:
        stmt = (
            select(User)
            .where(User.email == email, User.deleted_at.is_(None))
            .options(joinedload(User.auth_user))
        )
        result = await self._session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_active_user_by_id(self, user_id: uuid.UUID) -> User | None:
        stmt = (
            select(User)
            .where(User.id == user_id, User.deleted_at.is_(None))
            .options(joinedload(User.auth_user))
        )
        result = await self._session.execute(stmt)
        return result.unique().scalar_one_or_none()

    def add_user(self, user: User) -> None:
        self._session.add(user)

    def add_auth_user(self, row: AuthUser) -> None:
        self._session.add(row)

    def add_refresh_token(self, row: RefreshToken) -> None:
        self._session.add(row)

    async def get_refresh_token(self, row_id: uuid.UUID) -> RefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.id == row_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    def revoke_refresh_token(self, row: RefreshToken, when: datetime) -> None:
        row.revoked_at = when

    async def revoke_all_refresh_tokens_for_user(
        self, user_id: uuid.UUID, when: datetime
    ) -> None:
        stmt = (
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=when)
        )
        await self._session.execute(stmt)
