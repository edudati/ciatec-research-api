"""Dependency providers for project exports."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Settings, get_settings
from src.core.database import get_db
from src.modules.project_exports.service import ProjectExportsService


def get_project_exports_service(
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ProjectExportsService:
    return ProjectExportsService(db, settings=settings)
