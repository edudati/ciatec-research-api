"""Dependency providers for project enrollments."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.modules.project_enrollments.service import ProjectEnrollmentsService


def get_project_enrollments_service(
    db: AsyncSession = Depends(get_db),
) -> ProjectEnrollmentsService:
    return ProjectEnrollmentsService(db)
