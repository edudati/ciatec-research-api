"""Dependency providers for the sessions module."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.modules.sessions.service import SessionsService


def get_sessions_service(db: AsyncSession = Depends(get_db)) -> SessionsService:
    return SessionsService(db)
