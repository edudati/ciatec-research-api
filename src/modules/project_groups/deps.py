"""Dependency providers for project groups."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.modules.project_groups.service import ProjectGroupsService


def get_project_groups_service(
    db: AsyncSession = Depends(get_db),
) -> ProjectGroupsService:
    return ProjectGroupsService(db)
