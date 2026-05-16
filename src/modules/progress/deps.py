"""Dependency providers for the progress module."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.modules.progress.service import ProgressService


def get_progress_service(db: AsyncSession = Depends(get_db)) -> ProgressService:
    return ProgressService(db)
