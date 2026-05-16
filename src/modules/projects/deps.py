"""Dependency providers for projects."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.modules.projects.service import ProjectsService


def get_projects_service(db: AsyncSession = Depends(get_db)) -> ProjectsService:
    return ProjectsService(db)
